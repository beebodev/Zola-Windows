using System.Security.Cryptography;
using Microsoft.UI.Xaml;

namespace Zola.Client;

// P1-CLIENT: app entry starts the dedicated hermes serve lifecycle and tears it down on close — P1-D01
public partial class App : Application
{
    private Window? _window;
    private HermesProcessManager? _backend;
    private WatcherProcess? _watcher;
    private PhoneProcess? _phone;
    private string _phoneSecret = "";

    public App()
    {
        // P1-CLIENT: WinUI bootstrap before any backend process is spawned — P1-D01
        InitializeComponent();
    }

    protected override void OnLaunched(LaunchActivatedEventArgs args)
    {
        // P9-SUPERVISE: prune old local dumps on startup; the folder may be absent — P9-D02
        DumpPruner.PruneOnStartup();
        // P1-CLIENT: own the backend for this window; chat socket stays closed until health passes — P1-D01
        _backend = new HermesProcessManager();
        // P10-INTAKE: one secret for this launch, passed only to serve and zola-phone — P10-D12
        _phoneSecret = Convert.ToHexString(RandomNumberGenerator.GetBytes(32));
        _backend.PhoneLaunchSecret = _phoneSecret;
        // P9-WATCH: polling continues while serve is down, so the watcher is not serve's child — P9-D02
        _watcher = new WatcherProcess(_backend.ProfileDirectory);
        _phone = new PhoneProcess(_backend.ProfileDirectory, () => _phoneSecret);
        _window = new MainWindow(_backend, _watcher, _phone);
        _window.Closed += (_, _) =>
        {
            _phone.StopDeliberate();
            _watcher.StopDeliberate();
            _backend.Shutdown();
        };
        _window.Activate();
        _watcher.Start();
        _phone.Start();
        _ = StartBackendAsync();
    }

    private async Task StartBackendAsync()
    {
        var backend = _backend;
        var window = _window;
        if (backend is null)
        {
            return;
        }

        var ok = await backend.StartAsync().ConfigureAwait(false);
        if (!ok && window is MainWindow main && !backend.IsShutdown)
        {
            main.BeginBackendRecovery();
        }
    }
}
