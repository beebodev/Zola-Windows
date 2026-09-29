using System.Diagnostics;
using System.Globalization;
using System.Management;
using Microsoft.UI.Dispatching;

namespace Zola.Client.Presence;

// P3-LIFE: Hermes TTS playback presence only (owned ffplay sessions); no audio data — P3-D14 / S17
internal sealed class TtsPlaybackMonitor : IDisposable
{
    private readonly DispatcherQueue _dispatcher;
    private readonly Func<int?> _serveProcessId;
    private readonly object _gate = new();
    private Thread? _thread;
    private CancellationTokenSource? _cts;
    private IntPtr _enumerator;
    private IntPtr _device;
    private IntPtr _manager;
    private bool _comReady;
    private bool _monitoring;
    private bool _disposed;
    private bool _segmentActive;
    private bool _boutActive;
    private bool _fallbackLogged;
    private bool _foreignRejectLogged;
    private bool _useSessionInactiveStop = true;
    private readonly Dictionary<uint, int> _ownedSessionStates = new();
    private DateTimeOffset? _pendingInactiveUtc;
    private int _pollHz = PresenceLife.DefaultPlaybackPollHz;
    private int _releaseDebounceMs = PresenceLife.DefaultReleaseDebounceMs;
    private int? _rootPid;
    private DateTime _rootStartUtc = DateTime.MinValue;
    private string _rootSource = "none";
    private DateTime _segmentLostUtc = DateTime.MinValue;
    private DateTimeOffset? _lastSegmentStarted;
    private DateTimeOffset? _lastSegmentStopped;
    private DateTimeOffset? _lastBoutStarted;
    private DateTimeOffset? _lastBoutStopped;
#if DEBUG
    private bool _debugForceUnavailable;
    private bool? _debugSegmentOverride;
#endif

    internal TtsPlaybackMonitor(DispatcherQueue dispatcher, Func<int?> serveProcessId)
    {
        _dispatcher = dispatcher;
        _serveProcessId = serveProcessId;
    }

    internal bool IsAvailable { get; private set; }

    internal bool IsSegmentActive
    {
        get
        {
#if DEBUG
            if (_debugSegmentOverride.HasValue)
            {
                return _debugSegmentOverride.Value;
            }
#endif
            return _segmentActive;
        }
    }

    internal bool IsBoutActive => _boutActive;

    internal DateTimeOffset? LastSegmentStartedUtc => _lastSegmentStarted;
    internal DateTimeOffset? LastSegmentStoppedUtc => _lastSegmentStopped;
    internal DateTimeOffset? LastBoutStartedUtc => _lastBoutStarted;
    internal DateTimeOffset? LastBoutStoppedUtc => _lastBoutStopped;

    internal event Action? SegmentStarted;
    internal event Action? SegmentStopped;
    internal event Action? BoutStarted;
    internal event Action? BoutStopped;

    internal void ApplyLife(PresenceLife life)
    {
        _pollHz = Math.Clamp(life.PlaybackPollHz, PresenceLife.PlaybackPollHzMin, PresenceLife.PlaybackPollHzMax);
        _releaseDebounceMs = Math.Clamp(
            life.ReleaseDebounceMs,
            PresenceLife.MsMin,
            PresenceLife.MsMax);
    }

    internal void StartMonitoring()
    {
        lock (_gate)
        {
            if (_disposed)
            {
                return;
            }

            if (_monitoring)
            {
                return;
            }

            RefreshOwnershipRoots(log: true);
            EnsureCom();
            UpdateAvailability();
            _monitoring = true;
            _segmentLostUtc = DateTime.MinValue;
            _cts = new CancellationTokenSource();
            var token = _cts.Token;
            _thread = new Thread(() => PollLoop(token))
            {
                IsBackground = true,
                Name = "Zola.TtsPlaybackMonitor",
            };
            _thread.Start();
            PresenceView.WriteLog(
                "P3-LIFE: playback monitor start available="
                + IsAvailable.ToString(CultureInfo.InvariantCulture)
                + " root="
                + (_rootPid?.ToString(CultureInfo.InvariantCulture) ?? "none")
                + " source="
                + _rootSource
                + " hz="
                + _pollHz.ToString(CultureInfo.InvariantCulture));
        }
    }

    internal void StopMonitoring()
    {
        Thread? thread;
        CancellationTokenSource? cts;
        lock (_gate)
        {
            if (!_monitoring)
            {
                ForceInactiveLocked("stop");
                return;
            }

            _monitoring = false;
            cts = _cts;
            _cts = null;
            thread = _thread;
            _thread = null;
        }

        try
        {
            cts?.Cancel();
        }
        catch
        {
        }

        if (thread is not null && thread.IsAlive)
        {
            thread.Join(500);
        }

        cts?.Dispose();
        lock (_gate)
        {
            ForceInactiveLocked("stop");
        }

        PresenceView.WriteLog("P3-LIFE: playback monitor stop");
    }

    public void Dispose()
    {
        lock (_gate)
        {
            if (_disposed)
            {
                return;
            }

            _disposed = true;
        }

        StopMonitoring();
        ReleaseCom();
    }

#if DEBUG
    internal void DebugForceUnavailable(bool force)
    {
        _debugForceUnavailable = force;
        UpdateAvailability();
        PresenceView.WriteLog(
            "P3-LIFE: playback monitor debug forceUnavailable="
            + force.ToString(CultureInfo.InvariantCulture)
            + " available="
            + IsAvailable.ToString(CultureInfo.InvariantCulture));
    }

    internal void DebugSetSegmentOverride(bool? active)
    {
        _debugSegmentOverride = active;
        PresenceView.WriteLog(
            "P3-LIFE: playback monitor debug segmentOverride="
            + (active.HasValue ? active.Value.ToString(CultureInfo.InvariantCulture) : "live"));
    }
#endif

    private void PollLoop(CancellationToken token)
    {
        try
        {
            AudioSessionInterop.CoInitializeEx(IntPtr.Zero, 0x0);
        }
        catch
        {
        }

        while (!token.IsCancellationRequested)
        {
            var hz = Math.Max(1, _pollHz);
            var interval = TimeSpan.FromMilliseconds(1000.0 / hz);
            try
            {
                RefreshOwnershipRoots(log: false);
                UpdateAvailability();
                var owned = false;
#if DEBUG
                if (_debugSegmentOverride.HasValue)
                {
                    owned = _debugSegmentOverride.Value;
                }
                else
#endif
                if (IsAvailable && _comReady && _manager != IntPtr.Zero)
                {
                    owned = HasOwnedFfplaySegment();
                }

                ApplySegmentSample(owned);
            }
            catch (Exception ex)
            {
                PresenceView.WriteLog("P3-LIFE: playback monitor poll error=" + ex.GetType().Name);
            }

            try
            {
                Task.Delay(interval, token).GetAwaiter().GetResult();
            }
            catch (OperationCanceledException)
            {
                break;
            }
        }
    }

    private bool HasOwnedFfplaySegment()
    {
        var sessions = AudioSessionInterop.EnumerateSessionProcesses(_manager);
        var rejectedForeign = false;
        var ownedPresent = false;
        var ownedActive = false;
        var seenOwned = new HashSet<uint>();
        foreach (var (pid, name, state) in sessions)
        {
            if (!string.Equals(name, "ffplay", StringComparison.OrdinalIgnoreCase))
            {
                continue;
            }

            if (!IsHermesOwned((int)pid))
            {
                rejectedForeign = true;
                continue;
            }

            ownedPresent = true;
            seenOwned.Add(pid);
            if (state == AudioSessionInterop.SessionStateActive)
            {
                ownedActive = true;
            }

            TrackOwnedSessionState(pid, state);
        }

        foreach (var pid in _ownedSessionStates.Keys.ToArray())
        {
            if (!seenOwned.Contains(pid))
            {
                LogOwnedSessionGone(pid);
                _ownedSessionStates.Remove(pid);
            }
        }

        if (!ownedPresent)
        {
            _pendingInactiveUtc = null;
        }

        if (rejectedForeign)
        {
            if (!_foreignRejectLogged)
            {
                _foreignRejectLogged = true;
                PresenceView.WriteLog("P3-LIFE: playback ownership reject foreign ffplay");
            }
        }
        else
        {
            _foreignRejectLogged = false;
        }

        // P3-LIFE: SegmentStopped prefers GetState Inactive when it leads session removal — P3-D14 / S17
        return _useSessionInactiveStop ? ownedActive : ownedPresent;
    }

    private void TrackOwnedSessionState(uint pid, int state)
    {
        if (_ownedSessionStates.TryGetValue(pid, out var previous))
        {
            if (previous == AudioSessionInterop.SessionStateActive
                && state == AudioSessionInterop.SessionStateInactive)
            {
                _pendingInactiveUtc = DateTimeOffset.Now;
                PresenceView.WriteLog(
                    "P3-LIFE: playback segment state Inactive pid="
                    + pid.ToString(CultureInfo.InvariantCulture));
            }
        }
        else if (state == AudioSessionInterop.SessionStateInactive && _segmentActive)
        {
            _pendingInactiveUtc ??= DateTimeOffset.Now;
            PresenceView.WriteLog(
                "P3-LIFE: playback segment state Inactive pid="
                + pid.ToString(CultureInfo.InvariantCulture));
        }

        _ownedSessionStates[pid] = state;
    }

    private void LogOwnedSessionGone(uint pid)
    {
        var now = DateTimeOffset.Now;
        var savingMs = _pendingInactiveUtc is { } inactive
            ? (now - inactive).TotalMilliseconds
            : double.NaN;
        PresenceView.WriteLog(
            "P3-LIFE: playback segment session gone pid="
            + pid.ToString(CultureInfo.InvariantCulture)
            + " inactiveLeadMs="
            + (double.IsNaN(savingMs)
                ? "none"
                : Math.Round(savingMs).ToString(CultureInfo.InvariantCulture)));
        _pendingInactiveUtc = null;
    }

    private bool IsHermesOwned(int ffplayPid)
    {
        var root = _rootPid;
        if (root is null or <= 0)
        {
            return false;
        }

        DateTime start;
        try
        {
            start = Process.GetProcessById(ffplayPid).StartTime.ToUniversalTime();
        }
        catch
        {
            return false;
        }

        if (_rootStartUtc != DateTime.MinValue && start < _rootStartUtc)
        {
            return false;
        }

        var walk = ffplayPid;
        for (var hop = 0; hop <= 2; hop++)
        {
            if (walk == root.Value)
            {
                return true;
            }

            var parent = AudioSessionInterop.GetParentProcessId(walk);
            if (parent <= 0)
            {
                break;
            }

            walk = parent;
        }

        return false;
    }

    private void ApplySegmentSample(bool owned)
    {
        var now = DateTime.UtcNow;
        bool raiseSegmentStarted = false;
        bool raiseSegmentStopped = false;
        bool raiseBoutStarted = false;
        bool raiseBoutStopped = false;
        double bridgedGapMs = 0;

        lock (_gate)
        {
            if (!_monitoring || _disposed)
            {
                return;
            }

            if (owned)
            {
                if (!_segmentActive)
                {
                    _segmentActive = true;
                    _lastSegmentStarted = DateTimeOffset.Now;
                    raiseSegmentStarted = true;
                    if (_boutActive && _segmentLostUtc != DateTime.MinValue)
                    {
                        bridgedGapMs = (now - _segmentLostUtc).TotalMilliseconds;
                    }
                }

                _segmentLostUtc = DateTime.MinValue;
                if (!_boutActive)
                {
                    _boutActive = true;
                    _lastBoutStarted = DateTimeOffset.Now;
                    raiseBoutStarted = true;
                }
            }
            else
            {
                if (_segmentActive)
                {
                    _segmentActive = false;
                    _lastSegmentStopped = DateTimeOffset.Now;
                    _segmentLostUtc = now;
                    raiseSegmentStopped = true;
                }

                if (_boutActive && _segmentLostUtc != DateTime.MinValue)
                {
                    var lostMs = (now - _segmentLostUtc).TotalMilliseconds;
                    if (lostMs >= _releaseDebounceMs)
                    {
                        _boutActive = false;
                        _lastBoutStopped = DateTimeOffset.Now;
                        _segmentLostUtc = DateTime.MinValue;
                        raiseBoutStopped = true;
                    }
                }
            }
        }

        if (raiseSegmentStarted)
        {
            if (bridgedGapMs > 0)
            {
                PresenceView.WriteLog(
                    "P3-LIFE: playback bridged gapMs="
                    + bridgedGapMs.ToString("0", CultureInfo.InvariantCulture));
            }

            PresenceView.WriteLog("P3-LIFE: playback segment start");
            Raise(SegmentStarted);
        }

        if (raiseSegmentStopped)
        {
            PresenceView.WriteLog("P3-LIFE: playback segment stop");
            Raise(SegmentStopped);
        }

        if (raiseBoutStarted)
        {
            PresenceView.WriteLog("P3-LIFE: playback bout start");
            Raise(BoutStarted);
        }

        if (raiseBoutStopped)
        {
            PresenceView.WriteLog("P3-LIFE: playback bout stop");
            Raise(BoutStopped);
        }
    }

    private void ForceInactiveLocked(string reason)
    {
        var hadSegment = _segmentActive;
        var hadBout = _boutActive;
        _segmentActive = false;
        _boutActive = false;
        _segmentLostUtc = DateTime.MinValue;
        _ownedSessionStates.Clear();
        _pendingInactiveUtc = null;
        if (hadSegment)
        {
            _lastSegmentStopped = DateTimeOffset.Now;
        }

        if (hadBout)
        {
            _lastBoutStopped = DateTimeOffset.Now;
        }

        if (hadSegment || hadBout)
        {
            PresenceView.WriteLog("P3-LIFE: playback forced release reason=" + reason);
        }

        // Events after unlock via Raise from StopMonitoring caller path — fire here marshalled
        if (hadSegment)
        {
            Raise(SegmentStopped);
        }

        if (hadBout)
        {
            Raise(BoutStopped);
        }
    }

    private void RefreshOwnershipRoots(bool log)
    {
        var previous = _rootPid;
        var launched = _serveProcessId();
        if (launched is int pid and > 0 && ProcessAlive(pid))
        {
            _rootPid = pid;
            _rootSource = "HermesProcessManager";
            try
            {
                _rootStartUtc = Process.GetProcessById(pid).StartTime.ToUniversalTime();
            }
            catch
            {
                _rootStartUtc = DateTime.MinValue;
            }
        }
        else
        {
            // Command-line discovery only when the client did not hand us a live serve identity.
            var discovered = DiscoverServePidByCommandLine();
            if (discovered is int found)
            {
                _rootPid = found;
                _rootSource = "command-line";
                try
                {
                    _rootStartUtc = Process.GetProcessById(found).StartTime.ToUniversalTime();
                }
                catch
                {
                    _rootStartUtc = DateTime.MinValue;
                }
            }
            else
            {
                _rootPid = null;
                _rootSource = "none";
                _rootStartUtc = DateTime.MinValue;
            }
        }

        if (log || previous != _rootPid)
        {
            PresenceView.WriteLog(
                "P3-LIFE: playback ownership root="
                + (_rootPid?.ToString(CultureInfo.InvariantCulture) ?? "none")
                + " source="
                + _rootSource);
        }
    }

    private static int? DiscoverServePidByCommandLine()
    {
        try
        {
            using var searcher = new ManagementObjectSearcher(
                "SELECT ProcessId, CommandLine FROM Win32_Process WHERE Name='python.exe'");
            foreach (ManagementObject row in searcher.Get())
            {
                var cmd = row["CommandLine"] as string ?? "";
                if (cmd.IndexOf("hermes_cli.main", StringComparison.OrdinalIgnoreCase) < 0)
                {
                    continue;
                }

                if (cmd.IndexOf("serve", StringComparison.OrdinalIgnoreCase) < 0)
                {
                    continue;
                }

                if (cmd.IndexOf("--isolated", StringComparison.OrdinalIgnoreCase) < 0)
                {
                    continue;
                }

                return Convert.ToInt32(row["ProcessId"]);
            }
        }
        catch
        {
        }

        return null;
    }

    private static bool ProcessAlive(int pid)
    {
        try
        {
            using var p = Process.GetProcessById(pid);
            return !p.HasExited;
        }
        catch
        {
            return false;
        }
    }

    private void EnsureCom()
    {
        if (_comReady)
        {
            return;
        }

        if (!AudioSessionInterop.TryOpenSessionManager(out _enumerator, out _device, out _manager))
        {
            _comReady = false;
            PresenceView.WriteLog("P3-LIFE: playback monitor com init failed");
            return;
        }

        _comReady = true;
    }

    private void ReleaseCom()
    {
        AudioSessionInterop.Release(_manager);
        AudioSessionInterop.Release(_device);
        AudioSessionInterop.Release(_enumerator);
        _manager = IntPtr.Zero;
        _device = IntPtr.Zero;
        _enumerator = IntPtr.Zero;
        _comReady = false;
    }

    private void UpdateAvailability()
    {
        var available = _comReady && _rootPid is > 0;
#if DEBUG
        if (_debugForceUnavailable)
        {
            available = false;
        }
#endif
        if (IsAvailable == available)
        {
            return;
        }

        IsAvailable = available;
        if (!available && !_fallbackLogged)
        {
            _fallbackLogged = true;
            PresenceView.WriteLog("P3-LIFE: playback monitor fallback estimate (unavailable)");
        }
    }

    private void Raise(Action? handler)
    {
        if (handler is null)
        {
            return;
        }

        if (_dispatcher.HasThreadAccess)
        {
            handler.Invoke();
            return;
        }

        _ = _dispatcher.TryEnqueue(() => handler.Invoke());
    }
}
