using System.Diagnostics;
using System.Numerics;
using HelixToolkit.SharpDX;
using HelixToolkit.SharpDX.Assimp;
using HelixToolkit.SharpDX.Model;
using HelixToolkit.SharpDX.Model.Scene;
using HelixToolkit.SharpDX.Utilities;
using HelixToolkit.WinUI.SharpDX;
using Microsoft.UI.Dispatching;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;
using Windows.UI;
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
    private const float CameraX = 0f;
    private const float CameraY = 0.05f;
    private const float CameraZ = 3.15f;
    private const float LookX = 0f;
    private const float LookY = 0f;
    private const float LookZ = -3.372f;
    private const float CameraFovDegrees = 35f;
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
    private const byte AmbientRed = 90;
    private const byte AmbientGreen = 70;
    private const byte AmbientBlue = 40;
    private const byte KeyRed = 255;
    private const byte KeyGreen = 220;
    private const byte KeyBlue = 170;
    private const float KeyDirectionX = -0.3f;
    private const float KeyDirectionY = -0.8f;
    private const float KeyDirectionZ = -1f;
    private const byte FillRed = 180;
    private const byte FillGreen = 120;
    private const byte FillBlue = 60;
    private const float FillDirectionX = 0.6f;
    private const float FillDirectionY = -0.2f;
    private const float FillDirectionZ = -0.5f;
    private const float MaterialChannelMax = 1f;
    private const float WeightMin = 0f;
    private const float WeightMax = 1f;
    private const int EnvCubeFaceSize = 16;
    private const int EnvCubeFaceCount = 6;
    private const int EnvCubeBytesPerPixel = 4;
    private const int DdsHeaderBytes = 128;
    private const uint DdsMagic = 0x20534444;
    private const int DdsStructSize = 124;
    private const int DdsFlags = 0x1007;
    private const int DdsPixelFormatSize = 32;
    private const int DdsPixelFormatFlags = 0x41;
    private const int DdsRgbBitCount = 32;
    private const uint DdsRedMask = 0x00ff0000;
    private const uint DdsGreenMask = 0x0000ff00;
    private const uint DdsBlueMask = 0x000000ff;
    private const uint DdsAlphaMask = 0xff000000;
    private const int DdsCaps = 0x1008;
    private const int DdsCaps2 = 0xFE00;
    private const int DdsSizeOffset = 4;
    private const int DdsFlagsOffset = 8;
    private const int DdsHeightOffset = 12;
    private const int DdsWidthOffset = 16;
    private const int DdsPitchOffset = 20;
    private const int DdsPixelFormatSizeOffset = 76;
    private const int DdsPixelFormatFlagsOffset = 80;
    private const int DdsRgbBitCountOffset = 88;
    private const int DdsRedMaskOffset = 92;
    private const int DdsGreenMaskOffset = 96;
    private const int DdsBlueMaskOffset = 100;
    private const int DdsAlphaMaskOffset = 104;
    private const int DdsCapsOffset = 108;
    private const int DdsCaps2Offset = 112;
    private const byte EnvRedBase = 80;
    private const byte EnvRedSpan = 140;
    private const byte EnvGreenBase = 40;
    private const byte EnvGreenSpan = 70;
    private const byte EnvBlueBase = 10;
    private const byte EnvBlueFaceStep = 4;
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
    private const string PauseLocked = "locked";
    private const string PauseSuspended = "suspended";
    private const int RevalidateTimeoutMs = 5000;
    private const int RevalidatePollMs = 100;
    private const int DebugBlinkResetMs = 1000;
    private const int WorkingSetBytesPerMegabyte = 1_048_576;

    private readonly Viewport3DX _view;
    private readonly SceneNodeGroupModel3D _host;
    private readonly Grid _fallbackHost;
    private readonly SessionLockWatcher _lockWatcher;
    private readonly HashSet<string> _pauseReasons = new();
    private readonly DispatcherQueue _dispatcher;
    private PresenceLoadState _state = PresenceLoadState.NotLoaded;
    private Task? _loadTask;
    private int _generation;
    private bool _disposed;
    private bool _lightsAdded;
    private bool _firstFrameLogged;
    private bool _morphCountOk;
    private bool _morphApiWarned;
    private bool _unavailableLogged;
    private bool _weightsDirty;
    private bool _resumeFrameSeen;
    private bool _resumeException;
    private int _revalidateEpoch;
    private BoneSkinMeshNode? _morph;
    private TextureModel? _envTexture;
#if DEBUG
    private int _debugMorphCursor = -1;
    private DispatcherQueueTimer? _blinkTimer;
#endif

    internal PresenceView(IntPtr windowHandle)
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
                FieldOfView = CameraFovDegrees,
                Position = new Vector3(CameraX, CameraY, CameraZ),
                LookDirection = new Vector3(LookX, LookY, LookZ),
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

        _lockWatcher = new SessionLockWatcher(windowHandle);
        _lockWatcher.Locked += () => PauseRendering(PauseLocked);
        _lockWatcher.Unlocked += () => OnUnlockOrPowerResume(PauseLocked);
        _lockWatcher.Suspending += () => PauseRendering(PauseSuspended);
        _lockWatcher.Resumed += () => OnUnlockOrPowerResume(PauseSuspended);
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
        _generation++;
        _state = PresenceLoadState.NotLoaded;
        _loadTask = null;
        _morph = null;
        _morphCountOk = false;
        _firstFrameLogged = false;
        _host.Clear(true);
        ShowScene();
    }

    internal void PauseRendering(string reason)
    {
        if (_pauseReasons.Add(reason))
        {
            WriteLog("P3-RENDER: paused (" + reason + ")");
            ApplyRenderGate();
        }
    }

    internal void ResumeRendering(string reason)
    {
        if (_pauseReasons.Remove(reason))
        {
            WriteLog("P3-RENDER: resumed (" + reason + ")");
            ApplyRenderGate();
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
        _lockWatcher.Dispose();
        _view.OnRendered -= OnViewRendered;
        _view.RenderExceptionOccurred -= OnRenderException;
#if DEBUG
        _blinkTimer?.Stop();
#endif
        _host.Clear(true);
        (_view.EffectsManager as IDisposable)?.Dispose();
    }

    internal void SetWeight(MorphTarget target, float weight)
    {
        if (!CanUseMorphs())
        {
            return;
        }

        if (_morph is null)
        {
            return;
        }

        var clamped = Math.Clamp(weight, WeightMin, WeightMax);
        _morph.SetWeight((int)target, clamped);
        _weightsDirty = true;
    }

    internal void ApplyWeights()
    {
        if (!CanUseMorphs() || !_weightsDirty || _morph is null)
        {
            return;
        }

        _morph.WeightUpdated();
        _weightsDirty = false;
    }

#if DEBUG
    internal void DebugBlink()
    {
        SetWeight(MorphTarget.BlinkBoth, WeightMax);
        ApplyWeights();
        WriteLog("P3-RENDER: debug blink on");
        _blinkTimer ??= _dispatcher.CreateTimer();
        _blinkTimer.IsRepeating = false;
        _blinkTimer.Interval = TimeSpan.FromMilliseconds(DebugBlinkResetMs);
        _blinkTimer.Tick -= OnDebugBlinkReset;
        _blinkTimer.Tick += OnDebugBlinkReset;
        _blinkTimer.Start();
    }

    internal void DebugReload()
    {
        InvalidateScene();
        _ = LoadAsync();
        _ = LoadAsync();
    }

    internal void DebugMorphStep()
    {
        _debugMorphCursor++;
        if (_debugMorphCursor >= MorphTargets.MorphTargetCount)
        {
            _debugMorphCursor = -1;
            ResetAllWeights();
            ApplyWeights();
            WriteLog("P3-RENDER: debug morph " + MorphTargets.MorphTargetCount + " Neutral");
            return;
        }

        ResetAllWeights();
        var target = (MorphTarget)_debugMorphCursor;
        SetWeight(target, WeightMax);
        ApplyWeights();
        WriteLog("P3-RENDER: debug morph " + _debugMorphCursor + " " + target);
    }

    private void OnDebugBlinkReset(DispatcherQueueTimer sender, object args)
    {
        sender.Stop();
        SetWeight(MorphTarget.BlinkBoth, WeightMin);
        ApplyWeights();
        WriteLog("P3-RENDER: debug blink off");
    }

    private void ResetAllWeights()
    {
        foreach (MorphTarget target in Enum.GetValues<MorphTarget>())
        {
            SetWeight(target, WeightMin);
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

        var located = GlbTextureLocator.LocateMetallicRoughness(path);
        if (!located.Ok || located.Bytes is null)
        {
            throw new InvalidOperationException(located.FailureReason ?? "metallic-roughness lookup failed");
        }

        var roughness = new TextureModel(new MemoryStream(located.Bytes), false);
        return new ImportBundle(scene, roughness);
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

        morph.Material = new PBRMaterialCore
        {
            AlbedoMap = phong.DiffuseMap,
            NormalMap = phong.NormalMap,
            EmissiveMap = phong.EmissiveMap,
            RoughnessMetallicMap = bundle.RoughnessMetallic,
            AlbedoColor = new Color4(MaterialChannelMax, MaterialChannelMax, MaterialChannelMax, MaterialChannelMax),
            EmissiveColor = new Color4(MaterialChannelMax, MaterialChannelMax, MaterialChannelMax, MaterialChannelMax),
            MetallicFactor = MaterialChannelMax,
            RoughnessFactor = MaterialChannelMax,
            AmbientOcclusionFactor = MaterialChannelMax,
            RenderAlbedoMap = true,
            RenderNormalMap = phong.NormalMap is not null,
            RenderEmissiveMap = true,
            RenderRoughnessMetallicMap = true,
            RenderAmbientOcclusionMap = false,
            RenderEnvironmentMap = true,
        };

        EnsureLightsAndEnvironment();
        _host.Clear(true);
        var root = bundle.Scene.Root;
        // P3-RENDER: Grounding frames the bust at the origin, not the glTF translation — P3-D02
        root.ModelMatrix = Matrix4x4.Identity;
        _host.AddNode(root);
        _morph = morph;
        _morphCountOk = true;
        _state = PresenceLoadState.Ready;
        ShowScene();
        ApplyRenderGate();
        WriteLog("P3-RENDER: scene attached (UI thread)");
        WriteLog(
            "P3-RENDER: load duration=" + durationMs + "ms workingSetBefore=" + workingSetBefore
            + " workingSetAfter=" + ReadWorkingSet()
            + " workingSetBeforeMB=" + (workingSetBefore / WorkingSetBytesPerMegabyte)
            + " workingSetAfterMB=" + (ReadWorkingSet() / WorkingSetBytesPerMegabyte));
    }

    private void EnsureLightsAndEnvironment()
    {
        if (_lightsAdded)
        {
            return;
        }

        _envTexture = new TextureModel(new MemoryStream(CreateWarmCubeDds()), false);
        _view.Items.Add(new AmbientLight3D
        {
            Color = Windows.UI.Color.FromArgb(OpaqueAlpha, AmbientRed, AmbientGreen, AmbientBlue),
        });
        _view.Items.Add(new DirectionalLight3D
        {
            Color = Windows.UI.Color.FromArgb(OpaqueAlpha, KeyRed, KeyGreen, KeyBlue),
            Direction = new Vector3(KeyDirectionX, KeyDirectionY, KeyDirectionZ),
        });
        _view.Items.Add(new DirectionalLight3D
        {
            Color = Windows.UI.Color.FromArgb(OpaqueAlpha, FillRed, FillGreen, FillBlue),
            Direction = new Vector3(FillDirectionX, FillDirectionY, FillDirectionZ),
        });
        _view.Items.Add(new EnvironmentMap3D
        {
            Texture = _envTexture,
            SkipRendering = true,
        });
        _lightsAdded = true;
    }

    private void BecomeUnavailable(string reason)
    {
        _state = PresenceLoadState.Unavailable;
        _morph = null;
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

    private void OnUnlockOrPowerResume(string reason)
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
    }

    private void OnRenderException(object? sender, RelayExceptionEventArgs e)
    {
        _resumeException = true;
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

    private bool CanUseMorphs()
    {
        if (_state == PresenceLoadState.Ready && _morphCountOk && _morph is not null)
        {
            return true;
        }

        if (!_morphApiWarned)
        {
            _morphApiWarned = true;
            WriteLog("P3-RENDER: morph API ignored (not ready)");
        }

        return false;
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

    private static void DiscardBundle(ImportBundle? bundle)
    {
        if (bundle is null)
        {
            return;
        }

        _ = bundle.RoughnessMetallic;
    }

    private static long ReadWorkingSet()
    {
        using var process = Process.GetCurrentProcess();
        process.Refresh();
        return process.WorkingSet64;
    }

    private static byte[] CreateWarmCubeDds()
    {
        var faceBytes = EnvCubeFaceSize * EnvCubeFaceSize * EnvCubeBytesPerPixel;
        var data = new byte[DdsHeaderBytes + (faceBytes * EnvCubeFaceCount)];
        BitConverter.GetBytes(DdsMagic).CopyTo(data, 0);
        BitConverter.GetBytes(DdsStructSize).CopyTo(data, DdsSizeOffset);
        BitConverter.GetBytes(DdsFlags).CopyTo(data, DdsFlagsOffset);
        BitConverter.GetBytes(EnvCubeFaceSize).CopyTo(data, DdsHeightOffset);
        BitConverter.GetBytes(EnvCubeFaceSize).CopyTo(data, DdsWidthOffset);
        BitConverter.GetBytes(EnvCubeFaceSize * EnvCubeBytesPerPixel).CopyTo(data, DdsPitchOffset);
        BitConverter.GetBytes(DdsPixelFormatSize).CopyTo(data, DdsPixelFormatSizeOffset);
        BitConverter.GetBytes(DdsPixelFormatFlags).CopyTo(data, DdsPixelFormatFlagsOffset);
        BitConverter.GetBytes(DdsRgbBitCount).CopyTo(data, DdsRgbBitCountOffset);
        BitConverter.GetBytes(DdsRedMask).CopyTo(data, DdsRedMaskOffset);
        BitConverter.GetBytes(DdsGreenMask).CopyTo(data, DdsGreenMaskOffset);
        BitConverter.GetBytes(DdsBlueMask).CopyTo(data, DdsBlueMaskOffset);
        BitConverter.GetBytes(DdsAlphaMask).CopyTo(data, DdsAlphaMaskOffset);
        BitConverter.GetBytes(DdsCaps).CopyTo(data, DdsCapsOffset);
        BitConverter.GetBytes(DdsCaps2).CopyTo(data, DdsCaps2Offset);
        var last = EnvCubeFaceSize - 1;
        for (var face = 0; face < EnvCubeFaceCount; face++)
        {
            for (var y = 0; y < EnvCubeFaceSize; y++)
            {
                var t = last == 0 ? WeightMin : y / (float)last;
                var red = (byte)(EnvRedBase + (EnvRedSpan * t));
                var green = (byte)(EnvGreenBase + (EnvGreenSpan * t));
                var blue = (byte)(EnvBlueBase + (face * EnvBlueFaceStep));
                for (var x = 0; x < EnvCubeFaceSize; x++)
                {
                    var o = DdsHeaderBytes + (face * faceBytes) + (((y * EnvCubeFaceSize) + x) * EnvCubeBytesPerPixel);
                    data[o] = blue;
                    data[o + 1] = green;
                    data[o + 2] = red;
                    data[o + 3] = OpaqueAlpha;
                }
            }
        }

        return data;
    }

    private static void WriteLog(string line)
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

    private sealed record ImportBundle(HelixToolkitScene Scene, TextureModel RoughnessMetallic);
}
