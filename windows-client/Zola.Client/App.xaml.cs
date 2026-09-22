using Microsoft.UI.Xaml;

namespace Zola.Client;

// P1-CLIENT: app entry starts the dedicated hermes serve lifecycle and tears it down on close — P1-D01
public partial class App : Application
{
    private Window? _window;
    private HermesProcessManager? _backend;

    public App()
    {
        // P1-CLIENT: WinUI bootstrap before any backend process is spawned — P1-D01
        InitializeComponent();
    }

    protected override void OnLaunched(LaunchActivatedEventArgs args)
    {
        // P1-CLIENT: own the backend for this window; chat socket stays closed until health passes — P1-D01
        _backend = new HermesProcessManager();
        _window = new MainWindow(_backend);
        _window.Closed += (_, _) => _backend.Shutdown();
        _window.Activate();
        _ = _backend.StartAsync();
    }
}
