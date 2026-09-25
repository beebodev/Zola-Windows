using System.Runtime.InteropServices;

namespace Zola.Client.Presence;

// P3-RENDER: lock and power come from a window subclass, not a new package — P3-D02
internal sealed class SessionLockWatcher : IDisposable
{
    public event Action? Locked;
    public event Action? Unlocked;
    public event Action? Suspending;
    public event Action? Resumed;

    private const int NotifyForThisSession = 0;
    private const uint WmWtsSessionChange = 0x02B1;
    private const uint WmPowerBroadcast = 0x0218;
    private const uint WmNcDestroy = 0x0082;
    private const int WtsSessionLock = 0x7;
    private const int WtsSessionUnlock = 0x8;
    private const int PbtApmSuspend = 0x4;
    private const int PbtApmResumeAutomatic = 0x12;
    private static readonly UIntPtr SubclassId = new(0x50335244);

    private readonly IntPtr _hwnd;
    private readonly SubclassProc _subclassProc;
    private bool _registeredSession;
    private bool _subclassed;
    private bool _disposed;

    internal SessionLockWatcher(IntPtr hwnd)
    {
        _hwnd = hwnd;
        _subclassProc = OnSubclass;
        if (_hwnd == IntPtr.Zero)
        {
            return;
        }

        _registeredSession = WTSRegisterSessionNotification(_hwnd, NotifyForThisSession);
        _subclassed = SetWindowSubclass(_hwnd, _subclassProc, SubclassId, UIntPtr.Zero);
    }

    public void Dispose()
    {
        if (_disposed)
        {
            return;
        }

        _disposed = true;
        Unhook();
    }

    private void Unhook()
    {
        if (_hwnd == IntPtr.Zero)
        {
            return;
        }

        if (_subclassed)
        {
            RemoveWindowSubclass(_hwnd, _subclassProc, SubclassId);
            _subclassed = false;
        }

        if (_registeredSession)
        {
            WTSUnRegisterSessionNotification(_hwnd);
            _registeredSession = false;
        }
    }

    private IntPtr OnSubclass(IntPtr hWnd, uint msg, UIntPtr wParam, IntPtr lParam, UIntPtr uIdSubclass, UIntPtr dwRefData)
    {
        if (msg == WmNcDestroy)
        {
            Dispose();
            return DefSubclassProc(hWnd, msg, wParam, lParam);
        }

        if (msg == WmWtsSessionChange)
        {
            var code = unchecked((int)wParam.ToUInt32());
            if (code == WtsSessionLock)
            {
                Locked?.Invoke();
            }
            else if (code == WtsSessionUnlock)
            {
                Unlocked?.Invoke();
            }
        }
        else if (msg == WmPowerBroadcast)
        {
            var code = unchecked((int)wParam.ToUInt32());
            if (code == PbtApmSuspend)
            {
                Suspending?.Invoke();
            }
            else if (code == PbtApmResumeAutomatic)
            {
                Resumed?.Invoke();
            }
        }

        return DefSubclassProc(hWnd, msg, wParam, lParam);
    }

    private delegate IntPtr SubclassProc(IntPtr hWnd, uint uMsg, UIntPtr wParam, IntPtr lParam, UIntPtr uIdSubclass, UIntPtr dwRefData);

    [DllImport("wtsapi32.dll", SetLastError = true)]
    private static extern bool WTSRegisterSessionNotification(IntPtr hWnd, int dwFlags);

    [DllImport("wtsapi32.dll", SetLastError = true)]
    private static extern bool WTSUnRegisterSessionNotification(IntPtr hWnd);

    [DllImport("comctl32.dll", SetLastError = true)]
    private static extern bool SetWindowSubclass(IntPtr hWnd, SubclassProc pfnSubclass, UIntPtr uIdSubclass, UIntPtr dwRefData);

    [DllImport("comctl32.dll", SetLastError = true)]
    private static extern bool RemoveWindowSubclass(IntPtr hWnd, SubclassProc pfnSubclass, UIntPtr uIdSubclass);

    [DllImport("comctl32.dll")]
    private static extern IntPtr DefSubclassProc(IntPtr hWnd, uint uMsg, UIntPtr wParam, IntPtr lParam);
}
