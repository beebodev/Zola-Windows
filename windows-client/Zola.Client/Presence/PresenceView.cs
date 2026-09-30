using System.Diagnostics;
using System.Numerics;
using System.Runtime;
using HelixToolkit.SharpDX;
using HelixToolkit.SharpDX.Assimp;
using HelixToolkit.SharpDX.Model;
using HelixToolkit.SharpDX.Model.Scene;
using HelixToolkit.SharpDX.Utilities;
using HelixToolkit.WinUI.SharpDX;
using SharpDX.Direct3D11;
using Microsoft.UI.Dispatching;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;
using Color4 = HelixToolkit.Maths.Color4;

namespace Zola.Client.Presence;

internal enum PresenceLoadState
{
    NotLoaded,
    Loading,
    Ready,
    Unavailable,
}

internal sealed class PresenceView : UserControl, IDisposable
{
    private const float CameraUpX = 0f;
    private const float CameraUpY = 1f;
    private const float CameraUpZ = 0f;
    // P3-RENDER: fixed presence, no editor chrome or camera control — P3-D11
    private const bool ViewportShowViewCube = false;
    private const bool ViewportShowCoordinateSystem = false;
    private const bool ViewportShowFrameRate = false;
    private const bool ViewportShowFrameDetails = false;
    private const bool ViewportShowCameraInfo = false;
    private const bool ViewportShowCameraTarget = false;
    private const bool ViewportShowTriangleCountInfo = false;
    private const bool ViewportEnableCursorPosition = false;
    private const bool ViewportIsViewCubeEdgeClicksEnabled = false;
    private const bool ViewportIsViewCubeMoverEnabled = false;
    private const bool ViewportIsCoordinateSystemMoverEnabled = false;
    private const string ViewportTitle = "";
    private const string ViewportSubTitle = "";
    private const bool ViewportIsRotationEnabled = false;
    private const bool ViewportIsZoomEnabled = false;
    private const bool ViewportIsPanEnabled = false;
    private const bool ViewportIsInertiaEnabled = false;
    private const bool ViewportIsChangeFieldOfViewEnabled = false;
    private const bool ViewportIsMoveEnabled = false;
    private const bool ViewportZoomExtentsWhenLoaded = false;
    private const bool ViewportUseDefaultGestures = false;
    private const bool ViewportIsPinchZoomEnabled = false;
    private const bool ViewportIsThreeFingerPanningEnabled = false;
    private const bool ViewportIsTouchRotateEnabled = false;
    private const bool ViewportAllowLeftRightRotation = false;
    private const bool ViewportAllowUpDownRotation = false;
    private const bool ViewportRotateAroundMouseDownPoint = false;
    private const bool ViewportZoomAroundMouseDownPoint = false;
    private const bool ViewportFixedRotationPointEnabled = false;
    private const byte OpaqueAlpha = 255;
    private const byte ClearAlpha = 0;
    private const byte TokenChannelMax = 255;
    // P3-LIFE: last-resort fallback mirrors the ZolaBackground token #080808 — P3-D22
    private const byte TokenBackgroundFallbackChannel = 8;
    private const float MaterialChannelMax = 1f;
    private const string PresenceLogFile = "presence.log";
    private const string AssetsFolder = "Assets";
    private const string PresenceFolder = "Presence";
    private const string GlbFileName = "zola.glb";
    private const string TokenBackgroundColor = "ZolaBackground";
    private const string TokenBackgroundBrush = "ZolaBackgroundBrush";
    private const string TokenFallbackStyle = "ZolaSectionHeaderStyle";
    private const string FallbackText = "PRESENCE UNAVAILABLE";
    private const string PauseMinimized = "minimized";
    private const string PauseHidden = "hidden";
    // P4-LOCK: MainWindow passes these pause reasons; presence no longer owns the watcher — P4-D01
    internal const string PauseLocked = "locked";
    internal const string PauseSuspended = "suspended";
    private const int RevalidateTimeoutMs = 5000;
    private const int RevalidatePollMs = 100;
    internal const int DebugBlinkResetMilliseconds = 1000;
#if DEBUG
    private const int LookWatchDebounceMs = 250;
#endif
    private const int WorkingSetBytesPerMegabyte = 1_048_576;

    private readonly Viewport3DX _view;
    private readonly SceneNodeGroupModel3D _host;
    private readonly Grid _fallbackHost;
    private readonly HashSet<string> _pauseReasons = new();
    private readonly DispatcherQueue _dispatcher;
    private readonly PresenceAnimator _animator;
    private PresenceLook _look = PresenceLook.CreateDefault();
    private PostEffectToneMap? _toneMap;
    private bool _toneMapAvailable;
    private bool _toneMapUnavailableLogged;
    private Windows.UI.Color _tokenBackground = Windows.UI.Color.FromArgb(
        OpaqueAlpha,
        TokenBackgroundFallbackChannel,
        TokenBackgroundFallbackChannel,
        TokenBackgroundFallbackChannel);
    private PresenceLoadState _state = PresenceLoadState.NotLoaded;
    private Task? _loadTask;
    private int _generation;
    private bool _disposed;
    private bool _toneMapAdded;
    private bool _firstFrameLogged;
    private bool _morphCountOk;
    private bool _unavailableLogged;
    private bool _resumeFrameSeen;
    private bool _resumeException;
    private int _revalidateEpoch;
    private BoneSkinMeshNode? _morph;
    private SceneNode? _modelRoot;
    private DiffuseMaterialCore? _unlitMaterial;
#if DEBUG
    private FileSystemWatcher? _lookWatcher;
    private DispatcherQueueTimer? _lookWatchDebounce;
    private readonly List<WeakReference> _retiredTextureRefs = new();
    private readonly List<WeakReference> _retiredRootRefs = new();
    private int _reloadGcGeneration;
#endif

    // P4-LOCK: MainWindow owns SessionLockWatcher; presence only pauses/resumes — P4-D01
    internal PresenceView()
    {
        _dispatcher = DispatcherQueue.GetForCurrentThread();
        HorizontalAlignment = HorizontalAlignment.Stretch;
        VerticalAlignment = VerticalAlignment.Stretch;

        // P3-RENDER: Viewport3DX is built in code; XAML construction crashes WinUI — P3-D02
        _view = new Viewport3DX
        {
            HorizontalAlignment = HorizontalAlignment.Stretch,
            VerticalAlignment = VerticalAlignment.Stretch,
            EffectsManager = new DefaultEffectsManager(),
            Camera = new PerspectiveCamera
            {
                FieldOfView = _look.CameraFovDegrees,
                Position = new Vector3(_look.CameraX, _look.CameraY, _look.CameraZ),
                LookDirection = new Vector3(_look.LookX, _look.LookY, _look.LookZ),
                UpDirection = new Vector3(CameraUpX, CameraUpY, CameraUpZ),
            },
            ShowViewCube = ViewportShowViewCube,
            ShowCoordinateSystem = ViewportShowCoordinateSystem,
            ShowFrameRate = ViewportShowFrameRate,
            ShowFrameDetails = ViewportShowFrameDetails,
            ShowCameraInfo = ViewportShowCameraInfo,
            ShowCameraTarget = ViewportShowCameraTarget,
            ShowTriangleCountInfo = ViewportShowTriangleCountInfo,
            EnableCursorPosition = ViewportEnableCursorPosition,
            IsViewCubeEdgeClicksEnabled = ViewportIsViewCubeEdgeClicksEnabled,
            IsViewCubeMoverEnabled = ViewportIsViewCubeMoverEnabled,
            IsCoordinateSystemMoverEnabled = ViewportIsCoordinateSystemMoverEnabled,
            Title = ViewportTitle,
            SubTitle = ViewportSubTitle,
            IsRotationEnabled = ViewportIsRotationEnabled,
            IsZoomEnabled = ViewportIsZoomEnabled,
            IsPanEnabled = ViewportIsPanEnabled,
            IsInertiaEnabled = ViewportIsInertiaEnabled,
            IsChangeFieldOfViewEnabled = ViewportIsChangeFieldOfViewEnabled,
            IsMoveEnabled = ViewportIsMoveEnabled,
            ZoomExtentsWhenLoaded = ViewportZoomExtentsWhenLoaded,
            UseDefaultGestures = ViewportUseDefaultGestures,
            IsPinchZoomEnabled = ViewportIsPinchZoomEnabled,
            IsThreeFingerPanningEnabled = ViewportIsThreeFingerPanningEnabled,
            IsTouchRotateEnabled = ViewportIsTouchRotateEnabled,
            AllowLeftRightRotation = ViewportAllowLeftRightRotation,
            AllowUpDownRotation = ViewportAllowUpDownRotation,
            RotateAroundMouseDownPoint = ViewportRotateAroundMouseDownPoint,
            ZoomAroundMouseDownPoint = ViewportZoomAroundMouseDownPoint,
            FixedRotationPointEnabled = ViewportFixedRotationPointEnabled,
        };
        _view.InputBindings.Clear();
        if (Application.Current.Resources.TryGetValue(TokenBackgroundColor, out var background) && background is Windows.UI.Color color)
        {
            _tokenBackground = color;
            _view.BackgroundColor = color;
        }

        _host = new SceneNodeGroupModel3D();
        _view.Items.Add(_host);
        _view.OnRendered += OnViewRendered;
        _view.RenderExceptionOccurred += OnRenderException;

        _fallbackHost = new Grid { Visibility = Visibility.Collapsed };
        if (Application.Current.Resources.TryGetValue(TokenBackgroundBrush, out var brush) && brush is Brush fill)
        {
            _fallbackHost.Background = fill;
        }

        var fallbackLine = new TextBlock
        {
            Text = FallbackText,
            HorizontalAlignment = HorizontalAlignment.Center,
            VerticalAlignment = VerticalAlignment.Center,
            TextAlignment = TextAlignment.Center,
        };
        if (Application.Current.Resources.TryGetValue(TokenFallbackStyle, out var style) && style is Style header)
        {
            fallbackLine.Style = header;
        }

        _fallbackHost.Children.Add(fallbackLine);
        var root = new Grid();
        root.Children.Add(_view);
        root.Children.Add(_fallbackHost);
        Content = root;

        // P3-LIFE: animator is the only morph-weight and gain-multiplier writer — P3-D22
        _animator = new PresenceAnimator(this, _dispatcher);
#if DEBUG
        StartLookFileWatcher();
#endif
    }

    internal void AttachDisplay(ZolaDisplayStateModel model)
    {
        _animator.AttachDisplay(model);
    }

    // P3-LIFE: Hermes serve identity for TTS playback ownership — P3-D14 / S17
    internal void AttachPlaybackMonitor(Func<int?> serveProcessId)
    {
        _animator.AttachPlaybackMonitor(serveProcessId);
    }

    // P4-ASK: forward monitor bout signals and availability for question speech release — P4-D13
    internal bool PlaybackMonitorAvailable => _animator.PlaybackMonitorAvailable;

    internal event Action? PlaybackBoutStarted
    {
        add => _animator.PlaybackBoutStarted += value;
        remove => _animator.PlaybackBoutStarted -= value;
    }

    internal event Action<bool>? PlaybackBoutStopped
    {
        add => _animator.PlaybackBoutStopped += value;
        remove => _animator.PlaybackBoutStopped -= value;
    }

    internal void SetReducedMotion(bool reduced)
    {
        _animator.SetReducedMotion(reduced);
    }

    internal void RequestRender()
    {
        if (_view.RenderHost is not null)
        {
            _view.RenderHost.InvalidateRender();
        }
    }

    // P3-LIFE: animator writes the multiplier; the shader composites the token field — P3-D22
    internal void ApplyGainMultiplier(float multiplier)
    {
        if (_toneMap is null || !_toneMapAvailable)
        {
            return;
        }

        _toneMap.Multiplier = multiplier;
    }

    internal Task LoadAsync()
    {
        if (_disposed || _state == PresenceLoadState.Ready || _state == PresenceLoadState.Unavailable)
        {
            return Task.CompletedTask;
        }

        if (_state == PresenceLoadState.Loading && _loadTask is not null)
        {
            WriteLog("P3-RENDER: load coalesced");
            return _loadTask;
        }

        _state = PresenceLoadState.Loading;
        _loadTask = RunLoadAsync();
        return _loadTask;
    }

    internal void InvalidateScene()
    {
#if DEBUG
        TrackRetiringScene();
#endif
        var oldRoot = _modelRoot;
        _generation++;
        _state = PresenceLoadState.NotLoaded;
        _loadTask = null;
        _animator.Bind(null);
        _morph = null;
        _modelRoot = null;
        _unlitMaterial = null;
        _morphCountOk = false;
        _firstFrameLogged = false;
        _host.Clear(true);
        // P3-LOOK: KC11 — dispose the detached scene root on reload — P3-D13
        if (oldRoot is IDisposable disposable)
        {
            disposable.Dispose();
        }

        ShowScene();
    }

    internal void PauseRendering(string reason)
    {
        if (_pauseReasons.Add(reason))
        {
            WriteLog("P3-RENDER: paused (" + reason + ")");
            ApplyRenderGate();
            if (_pauseReasons.Count == 1)
            {
                _animator.OnPaused();
            }
        }
    }

    internal void ResumeRendering(string reason)
    {
        if (_pauseReasons.Remove(reason))
        {
            WriteLog("P3-RENDER: resumed (" + reason + ")");
            ApplyRenderGate();
            if (_pauseReasons.Count == 0)
            {
                _animator.OnResumed();
            }
        }
    }

    internal void NoteRootLoaded()
    {
        WriteLog("P3-RENDER: root loaded");
    }

    internal void NoteRenderOpportunity()
    {
        WriteLog("P3-RENDER: render opportunity");
    }

    public void Dispose()
    {
        if (_disposed)
        {
            return;
        }

        _disposed = true;
        _generation++;
        _animator.Dispose();
        _view.OnRendered -= OnViewRendered;
        _view.RenderExceptionOccurred -= OnRenderException;
#if DEBUG
        _lookWatchDebounce?.Stop();
        _lookWatcher?.Dispose();
#endif
        _host.Clear(true);
        (_view.EffectsManager as IDisposable)?.Dispose();
    }

#if DEBUG
    internal void DebugBlink()
    {
        _animator.DebugBlink();
    }

    internal void DebugWriteLifeDefaults()
    {
        _animator.DebugWriteDefaults();
    }

    internal void DebugReloadLife()
    {
        _animator.DebugReloadLife();
    }

    internal void DebugCycleForcedMode()
    {
        _animator.DebugCycleForcedMode();
    }

    internal void DebugForceMonitorUnavailable(bool force)
    {
        _animator.DebugForceMonitorUnavailable(force);
    }

    internal void DebugSetSegmentOverride(bool? active)
    {
        _animator.DebugSetSegmentOverride(active);
    }

    internal void DebugReload()
    {
        InvalidateScene();
        _ = LoadAsync();
        _ = LoadAsync();
    }

    // P3-LOOK: DEBUG file watch applies the same F12 JSON without needing window focus — P3-D13
    private void StartLookFileWatcher()
    {
        var dir = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            VoiceController.TimelineClientFolder,
            PresenceLook.DebugSubfolder);
        Directory.CreateDirectory(dir);
        _lookWatchDebounce = _dispatcher.CreateTimer();
        _lookWatchDebounce.IsRepeating = false;
        _lookWatchDebounce.Interval = TimeSpan.FromMilliseconds(LookWatchDebounceMs);
        _lookWatchDebounce.Tick += OnLookWatchDebounce;
        _lookWatcher = new FileSystemWatcher(dir, PresenceLook.DebugFileName)
        {
            NotifyFilter = NotifyFilters.LastWrite | NotifyFilters.Size | NotifyFilters.FileName,
        };
        _lookWatcher.Changed += OnLookFileChanged;
        _lookWatcher.Created += OnLookFileChanged;
        _lookWatcher.EnableRaisingEvents = true;
    }

    private void OnLookFileChanged(object sender, FileSystemEventArgs e)
    {
        if (_disposed)
        {
            return;
        }

        _ = _dispatcher.TryEnqueue(() =>
        {
            if (_lookWatchDebounce is null)
            {
                return;
            }

            _lookWatchDebounce.Stop();
            _lookWatchDebounce.Start();
        });
    }

    private void OnLookWatchDebounce(DispatcherQueueTimer sender, object args)
    {
        DebugReloadLook();
    }

    // P3-LOOK: F12 replaces from defaults; the JSON must list every look value — P3-D19
    internal void DebugReloadLook()
    {
        var path = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            VoiceController.TimelineClientFolder,
            PresenceLook.DebugSubfolder,
            PresenceLook.DebugFileName);
        if (!File.Exists(path))
        {
            WriteLog("P3-LOOK: look reload rejected — " + PresenceLook.DebugFileName + " is missing");
            return;
        }

        string json;
        try
        {
            json = File.ReadAllText(path);
        }
        catch (Exception ex)
        {
            WriteLog("P3-LOOK: look reload rejected — " + ex.Message);
            return;
        }

        if (!PresenceLook.TryReplaceJson(json, out var next, out var reason))
        {
            WriteLog("P3-LOOK: look reload rejected — " + reason);
            return;
        }

        _look = next;
        ApplyLook();
        WriteEffectiveLook();
        WriteLog("P3-LOOK: look applied fingerprint=" + _look.Fingerprint());
    }

    internal void DebugMorphStep()
    {
        _animator.DebugMorphStep();
    }

    // P3-LOOK: dump the full applied look after a complete replace — P3-D19
    private void WriteEffectiveLook()
    {
        var path = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            VoiceController.TimelineClientFolder,
            PresenceLook.DebugSubfolder,
            PresenceLook.EffectiveFileName);
        try
        {
            Directory.CreateDirectory(Path.GetDirectoryName(path)!);
            File.WriteAllText(path, _look.ToCanonicalJson());
        }
        catch (Exception ex)
        {
            WriteLog("P3-LOOK: effective dump failed — " + ex.Message);
        }
    }
#endif

    private async Task RunLoadAsync()
    {
        var generation = _generation;
        var path = Path.Combine(AppContext.BaseDirectory, AssetsFolder, PresenceFolder, GlbFileName);
        WriteLog("P3-RENDER: import started");
        var workingSetBefore = ReadWorkingSet();
        var clock = Stopwatch.StartNew();
        ImportBundle? bundle = null;
        string? failure = null;
        try
        {
            bundle = await Task.Run(() => ImportOnWorker(path)).ConfigureAwait(false);
        }
        catch (Exception ex)
        {
            failure = ex.Message;
        }

        clock.Stop();
        if (!IsCurrent(generation))
        {
            DiscardBundle(bundle);
            WriteLog("P3-RENDER: stale load discarded (gen " + generation + ")");
            return;
        }

        await EnqueueAsync(() =>
        {
            if (!IsCurrent(generation))
            {
                DiscardBundle(bundle);
                WriteLog("P3-RENDER: stale load discarded (gen " + generation + ")");
                return;
            }

            if (failure is not null || bundle is null)
            {
                BecomeUnavailable(failure ?? "import returned nothing");
                return;
            }

            AttachOnUi(bundle, clock.ElapsedMilliseconds, workingSetBefore);
        }).ConfigureAwait(false);
    }

    private ImportBundle ImportOnWorker(string path)
    {
        if (!File.Exists(path))
        {
            throw new FileNotFoundException("GLB missing", path);
        }

        using var importer = new Importer();
        var scene = importer.Load(path);
        if (scene?.Root is null)
        {
            throw new InvalidOperationException("GLB import produced no root");
        }

        return new ImportBundle(scene);
    }

    private void AttachOnUi(ImportBundle bundle, long durationMs, long workingSetBefore)
    {
        var morph = FindMorph(bundle.Scene.Root);
        if (morph?.MorphTargetWeights is null || morph.MorphTargetWeights.Length != MorphTargets.MorphTargetCount)
        {
            DiscardBundle(bundle);
            BecomeUnavailable("morph weight count is not " + MorphTargets.MorphTargetCount);
            return;
        }

        if (morph.Material is not PhongMaterialCore phong)
        {
            DiscardBundle(bundle);
            BecomeUnavailable("imported material is not PhongMaterialCore");
            return;
        }

        // P3-LOOK: one path — DiffuseMaterial EnableUnLit is albedo × white — P3-D20
        _unlitMaterial = new DiffuseMaterialCore
        {
            DiffuseMap = phong.DiffuseMap,
            DiffuseColor = new Color4(MaterialChannelMax, MaterialChannelMax, MaterialChannelMax, MaterialChannelMax),
            RenderDiffuseMap = true,
            EnableUnLit = true,
        };
        morph.Material = _unlitMaterial;

        EnsureToneMap();
        _host.Clear(true);
        var root = bundle.Scene.Root;
        // P3-RENDER: Grounding frames the bust at the origin, not the glTF translation — P3-D02
        root.ModelMatrix = Matrix4x4.Identity;
        _host.AddNode(root);
        _modelRoot = root;
        _morph = morph;
        _morphCountOk = true;
        _state = PresenceLoadState.Ready;
        ApplyLook();
        ShowScene();
        ApplyRenderGate();
        _animator.Bind(_morphCountOk ? _morph : null);
        LogTextureSampling();
        WriteLog("P3-RENDER: scene attached (UI thread)");
        WriteLog(
            "P3-RENDER: load duration=" + durationMs + "ms workingSetBefore=" + workingSetBefore
            + " workingSetAfter=" + ReadWorkingSet()
            + " workingSetBeforeMB=" + (workingSetBefore / WorkingSetBytesPerMegabyte)
            + " workingSetAfterMB=" + (ReadWorkingSet() / WorkingSetBytesPerMegabyte));
#if DEBUG
        LogReloadGc();
#endif
    }

    private void EnsureToneMap()
    {
        if (_toneMapAdded)
        {
            return;
        }

        // P3-LOOK: ACES pass; fail closed if the technique cannot load — P3-D19
        TryAddToneMap(PostEffectToneMap.EmbeddedResourceName);
        ApplyLook();
        _toneMapAdded = true;
    }

    private void BecomeUnavailable(string reason)
    {
        _state = PresenceLoadState.Unavailable;
        _animator.Bind(null);
        _morph = null;
        _modelRoot = null;
        _unlitMaterial = null;
        _morphCountOk = false;
        _host.Clear(true);
        _view.Visibility = Visibility.Collapsed;
        _fallbackHost.Visibility = Visibility.Visible;
        if (!_unavailableLogged)
        {
            _unavailableLogged = true;
            WriteLog("P3-RENDER: presence unavailable — " + reason);
        }
    }

    private void ShowScene()
    {
        _fallbackHost.Visibility = Visibility.Collapsed;
        _view.Visibility = Visibility.Visible;
    }

    // P4-LOCK: MainWindow drives unlock/resume with the same pause reasons as before — P4-D01
    internal void OnUnlockOrPowerResume(string reason)
    {
        ResumeRendering(reason);
        _ = RevalidateAfterResumeAsync();
    }

    private async Task RevalidateAfterResumeAsync()
    {
        var epoch = ++_revalidateEpoch;
        var generation = _generation;
        _resumeFrameSeen = false;
        _resumeException = false;
        ApplyRenderGate();
        var elapsed = 0;
        while (elapsed < RevalidateTimeoutMs)
        {
            if (_disposed || _generation != generation || epoch != _revalidateEpoch)
            {
                return;
            }

            if (_resumeFrameSeen)
            {
                WriteLog("P3-RENDER: scene reused");
                return;
            }

            if (_resumeException)
            {
                WriteLog("P3-RENDER: device recovered");
                InvalidateScene();
                await LoadAsync().ConfigureAwait(false);
                return;
            }

            if (IsWindowPresentable())
            {
                elapsed += RevalidatePollMs;
            }

            await Task.Delay(RevalidatePollMs).ConfigureAwait(false);
        }

        if (_disposed || _generation != generation || epoch != _revalidateEpoch)
        {
            return;
        }

        if (_resumeFrameSeen)
        {
            WriteLog("P3-RENDER: scene reused");
            return;
        }

        if (_resumeException)
        {
            WriteLog("P3-RENDER: device recovered");
        }
        else
        {
            WriteLog("P3-RENDER: reload (no frame after resume)");
        }

        InvalidateScene();
        await LoadAsync().ConfigureAwait(false);
    }

    private void OnViewRendered(object? sender, EventArgs e)
    {
        if (!_firstFrameLogged && _state == PresenceLoadState.Ready)
        {
            _firstFrameLogged = true;
            WriteLog("P3-RENDER: first 3D frame (Helix OnRendered)");
        }

        _resumeFrameSeen = true;
        _animator.NotePresented();
    }

    private void OnRenderException(object? sender, RelayExceptionEventArgs e)
    {
        _resumeException = true;
    }

    private void ApplyLook()
    {
        if (_view.Camera is PerspectiveCamera camera)
        {
            camera.FieldOfView = _look.CameraFovDegrees;
            camera.Position = new Vector3(_look.CameraX, _look.CameraY, _look.CameraZ);
            camera.LookDirection = new Vector3(_look.LookX, _look.LookY, _look.LookZ);
        }

        ApplyAlbedoSampler();
        ApplyToneMapLook();

        if (_view.RenderHost is not null)
        {
            _view.RenderHost.InvalidateRender();
        }
    }

    // P3-LOOK: albedo sampler uses linear mips and a look LOD bias — P3-D13
    private void ApplyAlbedoSampler()
    {
        if (_unlitMaterial is not null && _unlitMaterial.DiffuseMapSampler is { } unlitSampler)
        {
            unlitSampler.Filter = Filter.MinMagMipLinear;
            unlitSampler.MipLodBias = _look.MipLodBias;
            _unlitMaterial.DiffuseMapSampler = unlitSampler;
        }
    }

    private void TryAddToneMap(string resourceName)
    {
        if (_view.EffectsManager is null)
        {
            NoteToneMapUnavailable("effects manager missing");
            return;
        }

        if (!PostEffectToneMap.TryRegister(_view.EffectsManager, resourceName, out var reason))
        {
            NoteToneMapUnavailable(reason);
            RemoveToneMapElement();
            return;
        }

        try
        {
            if (_toneMap is null)
            {
                _toneMap = new PostEffectToneMap();
                _view.Items.Add(_toneMap);
            }

            _toneMapAvailable = true;
            _toneMapUnavailableLogged = false;
        }
        catch (Exception ex)
        {
            NoteToneMapUnavailable("render-target creation failed: " + ex.Message);
            RemoveToneMapElement();
        }
    }

    private void ApplyToneMapLook()
    {
#if DEBUG
        if (_look.ToneMapForceFail)
        {
            _ = PostEffectToneMap.LoadBytecode(PostEffectToneMap.MissingResourceName);
            NoteToneMapUnavailable("shader bytecode missing");
            if (_toneMap is not null)
            {
                _toneMap.EffectEnabled = false;
            }

            _view.BackgroundColor = _tokenBackground;
            return;
        }

        if (_toneMap is null)
        {
            TryAddToneMap(PostEffectToneMap.EmbeddedResourceName);
        }
#endif
        if (_toneMap is null)
        {
            _view.BackgroundColor = _tokenBackground;
            return;
        }

        _toneMapAvailable = true;
        _toneMapUnavailableLogged = false;
        _toneMap.Gain = _look.ToneMapGain;
        _toneMap.Multiplier = _animator.Multiplier;
        _toneMap.EffectEnabled = ShouldRunToneMapPass();
        ApplySceneClear();
    }

    // P3-LIFE: pass on clears A=0; fail-closed keeps opaque token #080808 — P3-D22
    private void ApplySceneClear()
    {
        if (!ShouldRunToneMapPass())
        {
            _view.BackgroundColor = _tokenBackground;
            return;
        }

        _view.BackgroundColor = Windows.UI.Color.FromArgb(
            ClearAlpha,
            _tokenBackground.R,
            _tokenBackground.G,
            _tokenBackground.B);
        PushTokenBackgroundToToneMap();
    }

    private void PushTokenBackgroundToToneMap()
    {
        if (_toneMap is null)
        {
            return;
        }

        var scale = 1f / TokenChannelMax;
        _toneMap.TokenBackground = new Color4(
            _tokenBackground.R * scale,
            _tokenBackground.G * scale,
            _tokenBackground.B * scale,
            1f);
    }

    private void RemoveToneMapElement()
    {
        if (_toneMap is not null)
        {
            _view.Items.Remove(_toneMap);
            _toneMap = null;
        }

        _toneMapAvailable = false;
    }

    private void NoteToneMapUnavailable(string reason)
    {
        _toneMapAvailable = false;
        if (_toneMapUnavailableLogged)
        {
            return;
        }

        _toneMapUnavailableLogged = true;
        WriteLog("P3-LOOK: tone map unavailable — " + reason);
    }

    private bool ShouldRunToneMapPass()
    {
        if (!_toneMapAvailable)
        {
            return false;
        }

#if DEBUG
        if (_look.ToneMapForceFail)
        {
            return false;
        }
#endif
        return true;
    }

    private void ApplyRenderGate()
    {
        if (_view.RenderHost is null)
        {
            return;
        }

        var run = _pauseReasons.Count == 0 && _state == PresenceLoadState.Ready;
        _view.RenderHost.IsRendering = run;
        if (run)
        {
            _view.RenderHost.InvalidateRender();
        }
    }

    private bool IsWindowPresentable()
    {
        return !_pauseReasons.Contains(PauseMinimized) && !_pauseReasons.Contains(PauseHidden);
    }

    private bool IsCurrent(int generation)
    {
        return !_disposed && _generation == generation;
    }

    private Task EnqueueAsync(Action action)
    {
        var done = new TaskCompletionSource();
        if (!_dispatcher.TryEnqueue(() =>
            {
                try
                {
                    action();
                    done.SetResult();
                }
                catch (Exception ex)
                {
                    done.SetException(ex);
                }
            }))
        {
            done.SetException(new InvalidOperationException("dispatcher rejected enqueue"));
        }

        return done.Task;
    }

    private static BoneSkinMeshNode? FindMorph(SceneNode node)
    {
        if (node is BoneSkinMeshNode bone)
        {
            return bone;
        }

        foreach (var child in node.Items)
        {
            var found = FindMorph(child);
            if (found is not null)
            {
                return found;
            }
        }

        return null;
    }

    private void LogTextureSampling()
    {
        var sampler = _unlitMaterial?.DiffuseMapSampler;
        if (sampler.HasValue)
        {
            var s = sampler.Value;
            WriteLog(
                "P3-LOOK: sampler Filter=" + s.Filter
                + " mipLodBias=" + s.MipLodBias.ToString("0.###")
                + " anisotropy=" + s.MaximumAnisotropy
                + " minLOD=" + s.MinimumLod
                + " maxLOD=" + s.MaximumLod
                + " (GLB sampler minFilter=9987 LINEAR_MIPMAP_LINEAR magFilter=9729 LINEAR)");
        }

        LogOneTexture("albedo", _unlitMaterial?.DiffuseMap);
    }

    private void LogOneTexture(string name, TextureModel? texture)
    {
        if (texture is null || _view.EffectsManager?.MaterialTextureManager is null)
        {
            WriteLog("P3-LOOK: texture " + name + " missing");
            return;
        }

        var srv = _view.EffectsManager.MaterialTextureManager.Register(texture);
        if (srv?.Resource is Texture2D gpu)
        {
            var d = gpu.Description;
            WriteLog(
                "P3-LOOK: texture " + name
                + " " + d.Width + "x" + d.Height
                + " mips=" + d.MipLevels
                + " format=" + d.Format
                + " option=" + d.OptionFlags);
            return;
        }

        WriteLog("P3-LOOK: texture " + name + " GPU resource not Texture2D");
    }

    private static void DiscardBundle(ImportBundle? bundle)
    {
        _ = bundle;
    }

    private static long ReadWorkingSet()
    {
        using var process = Process.GetCurrentProcess();
        process.Refresh();
        return process.WorkingSet64;
    }

#if DEBUG
    // P3-LOOK: debug-only reload GC / WeakRef diagnostic — P3-D13
    private void TrackRetiringScene()
    {
        if (_modelRoot is not null)
        {
            _retiredRootRefs.Add(new WeakReference(_modelRoot));
        }

        TrackRetiredTexture(_unlitMaterial?.DiffuseMap);
    }

    private void TrackRetiredTexture(TextureModel? texture)
    {
        if (texture is not null)
        {
            _retiredTextureRefs.Add(new WeakReference(texture));
        }
    }

    private void LogReloadGc()
    {
        _reloadGcGeneration++;
        GCSettings.LargeObjectHeapCompactionMode = GCLargeObjectHeapCompactionMode.CompactOnce;
        GC.Collect(GC.MaxGeneration, GCCollectionMode.Forced, blocking: true, compacting: true);
        GC.WaitForPendingFinalizers();
        GCSettings.LargeObjectHeapCompactionMode = GCLargeObjectHeapCompactionMode.CompactOnce;
        GC.Collect(GC.MaxGeneration, GCCollectionMode.Forced, blocking: true, compacting: true);
        var managed = GC.GetTotalMemory(true);
        using var process = Process.GetCurrentProcess();
        process.Refresh();
        var aliveTextures = 0;
        foreach (var reference in _retiredTextureRefs)
        {
            if (reference.IsAlive)
            {
                aliveTextures++;
            }
        }

        var aliveRoots = 0;
        foreach (var reference in _retiredRootRefs)
        {
            if (reference.IsAlive)
            {
                aliveRoots++;
            }
        }

        WriteLog(
            "P3-LOOK: reload-gc n=" + _reloadGcGeneration
            + " retiredTextures=" + _retiredTextureRefs.Count
            + " aliveTextures=" + aliveTextures
            + " retiredRoots=" + _retiredRootRefs.Count
            + " aliveRoots=" + aliveRoots
            + " workingSet=" + process.WorkingSet64
            + " privateBytes=" + process.PrivateMemorySize64
            + " gcTotal=" + managed);
    }
#endif

    internal static void WriteLog(string line)
    {
        try
        {
            var root = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                VoiceController.TimelineClientFolder,
                VoiceController.TimelineLogFolder);
            Directory.CreateDirectory(root);
            File.AppendAllText(
                Path.Combine(root, PresenceLogFile),
                DateTimeOffset.Now.ToString("o") + " " + line + Environment.NewLine);
        }
        catch
        {
        }
    }

    private sealed record ImportBundle(HelixToolkitScene Scene);
}
