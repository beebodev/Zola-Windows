using Microsoft.UI.Xaml;

namespace Zola.Client;

// P1-CLIENT: app entry starts the dedicated hermes serve lifecycle and tears it down on close — P1-D01
public partial class App : Application
{
    private Window? _window;
    private HermesProcessManager? _backend;
    private WatcherProcess? _watcher;

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
        // P9-WATCH: polling continues while serve is down, so the watcher is not serve's child — P9-D02
        _watcher = new WatcherProcess(_backend.ProfileDirectory);
        _window = new MainWindow(_backend);
        _window.Closed += (_, _) =>
        {
            _watcher.StopDeliberate();
            _backend.Shutdown();
        };
        _window.Activate();
        _watcher.Start();
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
