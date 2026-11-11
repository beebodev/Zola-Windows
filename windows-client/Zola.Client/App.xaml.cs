using System.Diagnostics;
using System.Security.Cryptography;
using Microsoft.UI.Xaml;
using Zola.Client.Identity;

namespace Zola.Client;

// P1-CLIENT: app entry starts the dedicated hermes serve lifecycle and tears it down on close — P1-D01
public partial class App : Application
{
    private Window? _window;
    private HermesProcessManager? _backend;
    private WatcherProcess? _watcher;
    private PhoneProcess? _phone;
    private string _phoneSecret = "";
    private SingleInstanceLock? _instanceLock;
    private BuildRoleInfo? _buildRole;
    private CancellationTokenSource? _driftCts;

    public App()
    {
        // P1-CLIENT: WinUI bootstrap before any backend process is spawned — P1-D01
        InitializeComponent();
    }

    protected override void OnLaunched(LaunchActivatedEventArgs args)
    {
        // PROC1-ID: mutex acquire is the first statement; role only after lock owned — PROC1-D7
        _instanceLock = SingleInstanceLock.TryAcquire(
            IdentityConstants.MutexName,
            InstanceStatusFile.DefaultPath);
        if (!_instanceLock.Owned)
        {
            var holder = _instanceLock.ReadHolderStatus();
            var text = holder is null
                ? RefuseMessages.Unknown
                : RefuseMessages.ForHolder(holder.Role, holder.Tag);
            // PROC1-ID: refusing instance is debug-output only; writes nothing persistent — PROC1-D7
            Debug.WriteLine($"proc1-id refuse: {text}");
            NativeMessageBox.Show(IdentityConstants.RefuseTitle, text);
            _instanceLock.Dispose();
            _instanceLock = null;
            Environment.Exit(0);
            return;
        }

        var baseDir = AppContext.BaseDirectory;
        _buildRole = BuildRole.Resolve(baseDir);
        IdentityLog.Write(IdentityLog.RoleLine(_buildRole.Role, _buildRole.Why, _buildRole.Tag));
        var exePath = Environment.ProcessPath ?? Path.Combine(baseDir, "Zola.Client.exe");
        if (_instanceLock.TryWriteStatus(_buildRole, exePath, out var statusFail))
        {
            IdentityLog.Write(IdentityLog.StatusWriteOk());
        }
        else
        {
            IdentityLog.Write(IdentityLog.StatusWriteFailed(statusFail ?? "unknown"));
        }

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
            _driftCts?.Cancel();
            // PROC1-ID: phone/watcher KillChild now WaitForExit(5000); serve already waited 5000 — PROC1-D7
            if (_phone.StopDeliberate())
            {
                IdentityLog.Write(IdentityLog.ReleaseAfterWait("phone"));
            }

            if (_watcher.StopDeliberate())
            {
                IdentityLog.Write(IdentityLog.ReleaseAfterWait("watcher"));
            }

            _backend.Shutdown();
            if (_backend.LastShutdownChildAlive)
            {
                IdentityLog.Write(IdentityLog.ReleaseAfterWait("serve"));
            }

            _instanceLock?.Dispose();
            _instanceLock = null;
        };
        _window.Activate();
        _watcher.Start();
        _phone.Start();
        _ = StartBackendAsync();
        if (_buildRole.Role == IdentityConstants.RoleStable)
        {
            StartDriftCheck();
        }
    }

    private void StartDriftCheck()
    {
        // PROC1-ID: off UI thread after Activate; fail-open — PROC1-D13
        var window = _window as MainWindow;
        if (window is null || _backend is null || _buildRole is null)
        {
            return;
        }

        var manifestName = _buildRole.Manifest ?? IdentityConstants.ManifestFileName;
        var manifestPath = Path.Combine(AppContext.BaseDirectory, manifestName);
        // PROC1-ID: same Hermes root HermesLaunchResolver uses for this launch; no hard-coded fallback — PROC1-D13
        if (!HermesLaunchResolver.TryResolve(out _, out var hermesRoot, out _))
        {
            IdentityLog.Write(IdentityLog.DriftIncomplete("hermes_root"));
            return;
        }

        // PROC1-ID Phase 4c: StableRoot\_promotions\<tag>\pip-freeze.txt when Switch wrote it — PROC1-D13
        string? pipFreezePath = null;
        if (!string.IsNullOrWhiteSpace(_buildRole.Tag))
        {
            var tagDir = AppContext.BaseDirectory.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
            var stableRoot = Directory.GetParent(tagDir)?.FullName;
            if (!string.IsNullOrEmpty(stableRoot))
            {
                pipFreezePath = Path.Combine(stableRoot, "_promotions", _buildRole.Tag, "pip-freeze.txt");
            }
        }

        var profile = _backend.ProfileDirectory;
        _driftCts = new CancellationTokenSource();
        var token = _driftCts.Token;
        _ = Task.Run(() =>
        {
            try
            {
                var result = DriftChecker.Run(
                    manifestPath,
                    hermesRoot,
                    profile,
                    IdentityConstants.DriftTimeout,
                    pipFreezePath);
                if (token.IsCancellationRequested)
                {
                    return;
                }

                if (!result.Completed)
                {
                    IdentityLog.Write(IdentityLog.DriftIncomplete(result.IncompleteReason ?? "unknown"));
                    return;
                }

                var decision = DriftNotice.FromResult(result);
                if (!decision.PostNotice)
                {
                    IdentityLog.Write(IdentityLog.DriftCompletedNone());
                    return;
                }

                IdentityLog.Write(IdentityLog.DriftCompleted(decision.LogComponents, decision.PluginFileCount));
                if (!string.IsNullOrEmpty(result.PackagesCaptureFileName))
                {
                    IdentityLog.Write(IdentityLog.DriftPackagesCapture(result.PackagesCaptureFileName));
                }

                if (result.PackagesDiffFromFreezeFile)
                {
                    IdentityLog.Write(IdentityLog.DriftPackagesDiff(
                        result.PackagesAdded,
                        result.PackagesRemoved,
                        result.PackagesChanged));
                }

                if (token.IsCancellationRequested)
                {
                    return;
                }

                window.DispatcherQueue.TryEnqueue(() =>
                {
                    if (token.IsCancellationRequested)
                    {
                        return;
                    }

                    window.PostSystemNotice(decision.NoticeText);
                });
            }
            catch (Exception ex)
            {
                IdentityLog.Write(IdentityLog.DriftIncomplete($"error:{ex.GetType().Name}"));
            }
        }, token);
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
