using System.Runtime.InteropServices;

namespace Zola.Client.Identity;

// PROC1-ID: modal before any WinUI window exists — PROC1-D7
public static class NativeMessageBox
{
    private const uint MbOk = 0x00000000;
    private const uint MbIconWarning = 0x00000030;

    [DllImport("user32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern int MessageBoxW(IntPtr hWnd, string text, string caption, uint type);

    public static void Show(string title, string text) =>
        MessageBoxW(IntPtr.Zero, text, title, MbOk | MbIconWarning);
}
