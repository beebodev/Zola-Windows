using System.Diagnostics;
using System.Globalization;
using System.Text;
using HelixToolkit.SharpDX.Model.Scene;
using Microsoft.UI.Dispatching;
using Zola.Client.Presence.Controllers;

namespace Zola.Client.Presence;

// P3-LIFE: single writer of morph weights and the gain multiplier — P3-D22
internal sealed class PresenceAnimator
{
    private enum MouthSpeakPhase
    {
        Idle,
        Armed,
        Active,
        Releasing,
    }

    private const int ForcedOff = -1;

    private static readonly PresenceMode[] ForcedCycle =
    {
        PresenceMode.Idle,
        PresenceMode.Listening,
        PresenceMode.Thinking,
        PresenceMode.Speaking,
        PresenceMode.Alert,
        PresenceMode.Dormant,
    };

    private readonly PresenceView _view;
    private readonly DispatcherQueue _dispatcher;
    private readonly DispatcherQueueTimer _tick;
    private readonly BlinkController _blink = new();
    private readonly ExpressionController _expression = new();
    private readonly BrightnessController _brightness = new();
    private readonly MouthController _mouth = new();
    private readonly ModeTransitionCoordinator _coordinator = new();
    private readonly float[] _composed = new float[MorphTargets.MorphTargetCount];
    private PresenceLife _life = PresenceLife.CreateDefault();
    private Random _random = new();
    private BoneSkinMeshNode? _morph;
    private ZolaDisplayStateModel? _display;
    private TtsPlaybackMonitor? _playback;
    private PresenceMode _mode = PresenceMode.Idle;
    private PresenceMode _lookMode = PresenceMode.Idle;
    private MouthSpeakPhase _mouthPhase = MouthSpeakPhase.Idle;
    private int _forcedIndex = ForcedOff;
    private float _multiplier = PresenceLife.DefaultIdleMultiplier;
    private bool _paused;
    private bool _tickRunning;
    private bool _weightsDirty;
    private bool _reducedMotion;
    private bool _awaitingPresent;
    private bool _eyesArmed = true;
    private bool _brightnessArmed = true;
    private bool _expressionArmed = true;
    private bool _snapChannels = true;
    private bool _speakingPlaybackArmed;
    private bool _usingEstimateFallback;
    private bool _stopMonitorAfterRelease;
    private bool _mouthWasOwning;
    private long _onsetTicks;
#if DEBUG
    private int _debugMorphCursor = -1;
    private bool _debugMorphOverride;
    private DispatcherQueueTimer? _blinkTimer;
#endif

    internal PresenceAnimator(PresenceView view, DispatcherQueue dispatcher)
    {
        _view = view;
        _dispatcher = dispatcher;
        _tick = dispatcher.CreateTimer();
        _tick.IsRepeating = true;
        _tick.Tick += OnTick;
        RecreateRandom();
        ResetControllers(snap: true);
    }

    internal PresenceLife Life => _life;

    internal bool TickRunning => _tickRunning;

    internal float Multiplier => _multiplier;

    // P3-LIFE: Hermes serve PID for owned-ffplay matching — P3-D14 / S17
    internal void AttachPlaybackMonitor(Func<int?> serveProcessId)
    {
        _playback?.Dispose();
        _playback = new TtsPlaybackMonitor(_dispatcher, serveProcessId);
        _playback.ApplyLife(_life);
        _playback.BoutStarted += OnPlaybackBoutStarted;
        _playback.BoutStopped += OnPlaybackBoutStopped;
        _playback.SegmentStarted += OnPlaybackSegmentStarted;
        _playback.SegmentStopped += OnPlaybackSegmentStopped;
    }

    internal void AttachDisplay(ZolaDisplayStateModel model)
    {
        if (_display is not null)
        {
            _display.Changed -= OnDisplayChanged;
        }

        _display = model;
        _display.Changed += OnDisplayChanged;
        ApplyPresenceMode(EffectiveMode(), snap: true, force: true);
    }

    internal void SetReducedMotion(bool reduced)
    {
        if (_reducedMotion == reduced)
        {
            return;
        }

        _reducedMotion = reduced;
        PresenceView.WriteLog(
            reduced
                ? "P3-LIFE: reduced on blink=animated expression=snap brightness=snap pulse=off lids=snap stagger=bypass"
                : "P3-LIFE: reduced off blink=animated expression=ease brightness=ease pulse=on lids=ease stagger=on");
        var now = NowTicks();
        if (reduced)
        {
            if (!_eyesArmed)
            {
                ResetBlink(snap: true, now);
                _eyesArmed = true;
            }
            else
            {
                _blink.ApplyReducedMotion(now);
            }

            if (!_brightnessArmed)
            {
                _brightness.Reset(_life, _lookMode, snap: true, reduced: true, now);
                _brightnessArmed = true;
            }
            else
            {
                _brightness.ApplyReducedMotion(true, now);
            }

            if (!_expressionArmed)
            {
                _expression.Reset(_life, _lookMode, snap: true, now, _composed, _mouth.OwnsMouth);
                _expressionArmed = true;
            }
            else
            {
                _expression.ApplyReducedMotion();
            }

            _mouth.ApplyReducedMotion(true, now);
        }
        else
        {
            _brightness.ApplyReducedMotion(false, now);
            _mouth.ApplyReducedMotion(false, now);
        }

        Commit(force: true);
    }

    internal void Bind(BoneSkinMeshNode? morph)
    {
        if (_morph is not null && morph is null)
        {
            ForceMouthRelease("unbind");
        }

        _morph = morph;
        if (_morph is null)
        {
            StopTick();
            PresenceView.WriteLog("P3-LIFE: unbound");
            return;
        }

        PresenceView.WriteLog("P3-LIFE: rebound");
        ApplyPresenceMode(EffectiveMode(), snap: true, force: true);
        if (!_tickRunning)
        {
            PresenceView.WriteLog("P3-LIFE: tick stopped");
        }
    }

    internal void OnPaused()
    {
        _paused = true;
        ForceMouthRelease("pause");
        StopTick();
    }

    internal void OnResumed()
    {
        _paused = false;
        var now = NowTicks();
        var next = EffectiveMode();
        _mode = next;
        if (next == PresenceMode.Speaking)
        {
            BeginSpeakingPipeline(snap: true, previousLook: _lookMode);
        }
        else
        {
            ForceMouthRelease("resume");
            _lookMode = next;
            ResetVisuals(snap: true);
        }

        Commit(force: true);
    }

    internal void Dispose()
    {
        ForceMouthRelease("dispose");
        if (_playback is not null)
        {
            _playback.BoutStarted -= OnPlaybackBoutStarted;
            _playback.BoutStopped -= OnPlaybackBoutStopped;
            _playback.SegmentStarted -= OnPlaybackSegmentStarted;
            _playback.SegmentStopped -= OnPlaybackSegmentStopped;
            _playback.Dispose();
            _playback = null;
        }

        StopTick();
        _tick.Tick -= OnTick;
        if (_display is not null)
        {
            _display.Changed -= OnDisplayChanged;
        }
#if DEBUG
        _blinkTimer?.Stop();
#endif
    }

    internal void NotePresented()
    {
        if (!_awaitingPresent)
        {
            return;
        }

        _awaitingPresent = false;
        PresenceView.WriteLog("P3-LIFE: presented");
    }

#if DEBUG
    internal void DebugWriteDefaults()
    {
        var path = DebugPath(PresenceLife.DefaultsFileName);
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        File.WriteAllText(path, PresenceLife.CreateDefault().ToPrettyJson());
        PresenceView.WriteLog("P3-LIFE: wrote defaults keys=" + PresenceLife.RequiredKeys.Length);
    }

    internal void DebugReloadLife()
    {
        var path = DebugPath(PresenceLife.DebugFileName);
        if (!File.Exists(path))
        {
            PresenceView.WriteLog("P3-LIFE: life reload rejected — " + PresenceLife.DebugFileName + " is missing");
            return;
        }

        string json;
        try
        {
            json = File.ReadAllText(path);
        }
        catch (Exception ex)
        {
            PresenceView.WriteLog("P3-LIFE: life reload rejected — " + ex.Message);
            return;
        }

        if (!PresenceLife.TryReplaceJson(json, out var next, out var reason))
        {
            PresenceView.WriteLog("P3-LIFE: life reload rejected — " + reason);
            return;
        }

        _life = next;
        RecreateRandom();
        _playback?.ApplyLife(_life);
        PresenceView.WriteLog("P3-LIFE: life applied fingerprint=" + _life.Fingerprint());
        ApplyPresenceMode(EffectiveMode(), snap: true, force: true);
    }

    internal void DebugCycleForcedMode()
    {
        _forcedIndex++;
        if (_forcedIndex >= ForcedCycle.Length)
        {
            _forcedIndex = ForcedOff;
            PresenceView.WriteLog("P3-LIFE: forced mode off");
        }
        else
        {
            PresenceView.WriteLog("P3-LIFE: forced mode " + ForcedCycle[_forcedIndex]);
        }

        ApplyPresenceMode(EffectiveMode(), snap: false, force: true);
    }

    internal void DebugBlink()
    {
        if (_morph is null)
        {
            return;
        }

        SetWeight(MorphTarget.BlinkBoth, PresenceLife.WeightMax);
        FlushWeights();
        PresenceView.WriteLog("P3-RENDER: debug blink on");
        _blinkTimer ??= _dispatcher.CreateTimer();
        _blinkTimer.IsRepeating = false;
        _blinkTimer.Interval = TimeSpan.FromMilliseconds(PresenceView.DebugBlinkResetMilliseconds);
        _blinkTimer.Tick -= OnDebugBlinkReset;
        _blinkTimer.Tick += OnDebugBlinkReset;
        _blinkTimer.Start();
        RequestRender();
    }

    internal void DebugMorphStep()
    {
        if (_morph is null)
        {
            return;
        }

        _debugMorphCursor++;
        if (_debugMorphCursor >= MorphTargets.MorphTargetCount)
        {
            _debugMorphCursor = -1;
            _debugMorphOverride = false;
            ResetAllWeights();
            FlushWeights();
            PresenceView.WriteLog("P3-RENDER: debug morph " + MorphTargets.MorphTargetCount + " Neutral");
            RequestRender();
            return;
        }

        _debugMorphOverride = true;
        ResetAllWeights();
        var target = (MorphTarget)_debugMorphCursor;
        SetWeight(target, PresenceLife.WeightMax);
        FlushWeights();
        PresenceView.WriteLog("P3-RENDER: debug morph " + _debugMorphCursor + " " + target);
        RequestRender();
    }

    internal void DebugForceMonitorUnavailable(bool force)
    {
        _playback?.DebugForceUnavailable(force);
    }

    internal void DebugSetSegmentOverride(bool? active)
    {
        _playback?.DebugSetSegmentOverride(active);
    }

    private void OnDebugBlinkReset(DispatcherQueueTimer sender, object args)
    {
        sender.Stop();
        SetWeight(MorphTarget.BlinkBoth, PresenceLife.WeightMin);
        FlushWeights();
        PresenceView.WriteLog("P3-RENDER: debug blink off");
        RequestRender();
    }

    private static string DebugPath(string fileName)
    {
        return Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            VoiceController.TimelineClientFolder,
            PresenceLook.DebugSubfolder,
            fileName);
    }
#endif

    private void OnDisplayChanged()
    {
        if (_paused)
        {
            return;
        }

        ApplyPresenceMode(EffectiveMode(), snap: false, force: false);
    }

    private PresenceMode EffectiveMode()
    {
        if (_forcedIndex != ForcedOff)
        {
            return ForcedCycle[_forcedIndex];
        }

        return _display?.Current.PresenceMode ?? PresenceMode.Idle;
    }

    private void RecreateRandom()
    {
#if DEBUG
        _random = _life.RandomSeed == PresenceLife.DefaultRandomSeed
            ? new Random()
            : new Random(_life.RandomSeed);
#else
        _random = new Random();
#endif
    }

    private void ApplyPresenceMode(PresenceMode next, bool snap, bool force)
    {
        if (!force && next == _mode)
        {
            return;
        }

        var previousLook = _lookMode;
        _mode = next;
        if (next == PresenceMode.Speaking)
        {
            BeginSpeakingPipeline(snap, previousLook);
            return;
        }

        ForceMouthRelease("mode");
        _lookMode = next;
        ResetVisuals(snap);
        Commit(force: true);
    }

    // P3-LIFE: SpeakingPlaybackArmed holds THINKING until Hermes playback bout — P3-D14 / S17
    private void BeginSpeakingPipeline(bool snap, PresenceMode previousLook)
    {
        var now = NowTicks();
        _playback?.ApplyLife(_life);
        _usingEstimateFallback = _playback is null;
        if (_playback is not null)
        {
            // Probe availability by starting; StartMonitoring refreshes roots + COM.
            _playback.StartMonitoring();
            _usingEstimateFallback = !_playback.IsAvailable;
        }

        _mouthPhase = MouthSpeakPhase.Armed;
        _speakingPlaybackArmed = true;
        if (_usingEstimateFallback)
        {
            var onsetMs = EstimateOnsetDelayMs();
            if (!_life.SpeakingHoldsThinkingUntilOnset || onsetMs <= PresenceLife.MsMin)
            {
                _speakingPlaybackArmed = false;
                EnterSpeakingActive(snap, commit: true);
                return;
            }

            _onsetTicks = now + PresenceLife.TicksFromMilliseconds(onsetMs);
            PresenceView.WriteLog(
                "P3-LIFE: speakingPlaybackArmed estimate onsetMs="
                + onsetMs.ToString(CultureInfo.InvariantCulture));
        }
        else
        {
            _onsetTicks = long.MaxValue;
            PresenceView.WriteLog("P3-LIFE: speakingPlaybackArmed monitor");
        }

        if (previousLook == PresenceMode.Thinking)
        {
            _lookMode = PresenceMode.Thinking;
            Commit(force: true);
            return;
        }

        _lookMode = PresenceMode.Thinking;
        ResetVisuals(snap);
        Commit(force: true);
    }

    private void EnterSpeakingActive(bool snap, bool commit)
    {
        var now = NowTicks();
        PresenceView.WriteLog("P3-LIFE: speaking onset");
        _speakingPlaybackArmed = false;
        _mouthPhase = MouthSpeakPhase.Active;
        _lookMode = PresenceMode.Speaking;
        ResetVisuals(snap || _reducedMotion);
        _mouth.Begin(_life, _random, now, _composed, _reducedMotion);
        if (_playback is not null && !_playback.IsSegmentActive)
        {
            _mouth.SetGenerating(false, now);
        }

        if (commit)
        {
            Commit(force: true);
        }
    }

    private void TryEnterPlaybackActive(long nowTicks)
    {
        if (_mouthPhase != MouthSpeakPhase.Armed || nowTicks < _onsetTicks)
        {
            return;
        }

        EnterSpeakingActive(_snapChannels || _reducedMotion, commit: false);
    }

    private void OnPlaybackBoutStarted()
    {
        if (_mode != PresenceMode.Speaking || _usingEstimateFallback)
        {
            return;
        }

        if (_mouthPhase == MouthSpeakPhase.Active)
        {
            return;
        }

        var delay = Math.Max(PresenceLife.MsMin, _life.MouthOnsetOffsetMs);
        var now = NowTicks();
        _onsetTicks = now + PresenceLife.TicksFromMilliseconds(delay);
        PresenceView.WriteLog(
            "P3-LIFE: speakingPlaybackArmed bout onsetMs="
            + delay.ToString(CultureInfo.InvariantCulture));
        // Enter Active on this dispatcher turn when delay is 0; do not rely on a
        // settled EnsureTick (it would StopTick and leave Armed until an unrelated wake).
        TryEnterPlaybackActive(now);
        EnsureTick(NowTicks());
    }

    private void OnPlaybackBoutStopped()
    {
        if (_mode != PresenceMode.Speaking)
        {
            return;
        }

        var now = NowTicks();
        if (_mouth.OwnsMouth)
        {
            _mouth.Release(now);
            _mouthPhase = MouthSpeakPhase.Releasing;
        }

        _speakingPlaybackArmed = true;
        _onsetTicks = long.MaxValue;
        if (_life.SpeakingPauseShowsThinking)
        {
            _lookMode = PresenceMode.Thinking;
            ResetVisuals(_snapChannels || _reducedMotion);
            PresenceView.WriteLog("P3-LIFE: speaking pause shows thinking");
        }
        else
        {
            _lookMode = PresenceMode.Speaking;
            PresenceView.WriteLog("P3-LIFE: speaking pause keeps speaking look");
        }

        Commit(force: true);
    }

    private void OnPlaybackSegmentStarted()
    {
        if (_mouthPhase != MouthSpeakPhase.Active)
        {
            return;
        }

        _mouth.SetGenerating(true, NowTicks());
        PresenceView.WriteLog("P3-LIFE: mouth generate on");
        EnsureTick(NowTicks());
    }

    private void OnPlaybackSegmentStopped()
    {
        if (_mouthPhase != MouthSpeakPhase.Active)
        {
            return;
        }

        _mouth.SetGenerating(false, NowTicks());
        PresenceView.WriteLog("P3-LIFE: mouth generate off");
        EnsureTick(NowTicks());
    }

    private void ForceMouthRelease(string reason)
    {
        var wasArmed = _speakingPlaybackArmed || _mouthPhase != MouthSpeakPhase.Idle;
        _speakingPlaybackArmed = false;
        _usingEstimateFallback = false;
        _onsetTicks = 0;
        if (_mouth.OwnsMouth)
        {
            _mouth.Release(NowTicks());
            _mouthPhase = MouthSpeakPhase.Releasing;
        }
        else
        {
            _mouth.SnapToRest();
            _mouthPhase = MouthSpeakPhase.Idle;
        }

        var stopNow = reason is "pause" or "dispose" or "unbind" || !_mouth.OwnsMouth;
        if (stopNow)
        {
            _stopMonitorAfterRelease = false;
            if (_playback is not null)
            {
                _playback.StopMonitoring();
            }
        }
        else
        {
            _stopMonitorAfterRelease = true;
        }

        if (wasArmed)
        {
            PresenceView.WriteLog("P3-LIFE: speakingPlaybackArmed cancelled reason=" + reason);
        }
    }

    private int EstimateOnsetDelayMs()
    {
        var delay = (int)Math.Round(
            VoiceController.FirstSentenceLatencySeconds * PresenceLife.MsPerSecond)
            + _life.MouthOnsetOffsetMs;
        return delay < PresenceLife.MsMin ? PresenceLife.MsMin : delay;
    }

    private void ResetControllers(bool snap)
    {
        _speakingPlaybackArmed = false;
        _usingEstimateFallback = false;
        _mouthPhase = MouthSpeakPhase.Idle;
        _mouth.SnapToRest();
        _lookMode = _mode;
        ResetVisuals(snap);
    }

    private void ResetVisuals(bool snap)
    {
        var now = NowTicks();
        if (!snap && (!_eyesArmed || !_brightnessArmed || !_expressionArmed))
        {
            PresenceView.WriteLog("P3-LIFE: stagger restart");
            PresenceView.WriteLog("P3-LIFE: stagger values weights=" + FormatWeights() + " multiplier=" + FormatFloat(_multiplier));
        }

        _snapChannels = snap;
        _coordinator.Begin(_life, now, snap || _reducedMotion);
        _eyesArmed = false;
        _brightnessArmed = false;
        _expressionArmed = false;
        TryArmChannels(now);
    }

    private void TryArmChannels(long nowTicks)
    {
        if (!_eyesArmed && _coordinator.EyesDue(nowTicks))
        {
            ResetBlink(_snapChannels || _reducedMotion, nowTicks);
            _eyesArmed = true;
            LogStagger("eyes", nowTicks);
        }

        if (!_brightnessArmed && _coordinator.BrightnessDue(nowTicks))
        {
            _brightness.Reset(_life, _lookMode, _snapChannels || _reducedMotion, _reducedMotion, nowTicks);
            _brightnessArmed = true;
            LogStagger("brightness", nowTicks);
        }

        if (!_expressionArmed && _coordinator.ExpressionDue(nowTicks))
        {
            _expression.Reset(
                _life,
                _lookMode,
                _snapChannels || _reducedMotion,
                nowTicks,
                _composed,
                _mouth.OwnsMouth);
            _expressionArmed = true;
            LogStagger("expression", nowTicks);
        }
    }

    private void ResetBlink(bool snap, long nowTicks)
    {
        _blink.Reset(
            _life,
            _lookMode,
            _random,
            _composed[(int)MorphTarget.BlinkLeft],
            _composed[(int)MorphTarget.BlinkRight],
            _composed[(int)MorphTarget.BlinkBoth],
            snap,
            nowTicks);
    }

    private void OnTick(DispatcherQueueTimer sender, object args)
    {
        if (_paused || _morph is null)
        {
            StopTick();
            return;
        }

        Commit(force: false);
    }

    private void Commit(bool force)
    {
        if (_morph is null)
        {
            return;
        }

#if DEBUG
        if (_debugMorphOverride && !force)
        {
            return;
        }
#endif

        var now = NowTicks();
        TryEnterPlaybackActive(now);
        TryArmChannels(now);
        var previousPhase = _blink.Phase;
        _blink.Evaluate(now);
        LogBlinkTransition(previousPhase);
        _expression.Evaluate(now);
        _mouth.Evaluate(now);
        if (_mouthPhase == MouthSpeakPhase.Releasing && !_mouth.OwnsMouth)
        {
            _mouthPhase = _mode == PresenceMode.Speaking ? MouthSpeakPhase.Armed : MouthSpeakPhase.Idle;
            if (_mouthPhase == MouthSpeakPhase.Idle && _stopMonitorAfterRelease)
            {
                _stopMonitorAfterRelease = false;
                _playback?.StopMonitoring();
            }
        }
        if (_mouthWasOwning && !_mouth.OwnsMouth)
        {
            for (var i = (int)MorphTarget.JawOpen; i < MorphTargets.MorphTargetCount; i++)
            {
                _composed[i] = _mouth.Weight((MorphTarget)i);
            }

            _expression.TakeFromMouth(_lookMode, _snapChannels || _reducedMotion, now, _composed);
        }

        _mouthWasOwning = _mouth.OwnsMouth;
        if (_mouth.TryTakeStepLog())
        {
            LogMouthStep();
        }

        var mouthOwns = _mouth.OwnsMouth;
        var weightsChanged = false;
        for (var i = 0; i < MorphTargets.MorphTargetCount; i++)
        {
            var target = (MorphTarget)i;
            float value;
            if (PresenceLife.IsBlinkTarget(target))
            {
                value = _blink.Weight(target);
            }
            else if (mouthOwns && PresenceLife.IsMouthTarget(target))
            {
                value = _mouth.Weight(target);
            }
            else
            {
                value = _expression.Weight(target);
            }

            if (Math.Abs(value) <= _life.WeightEpsilon)
            {
                value = PresenceLife.WeightMin;
            }
            else if (Math.Abs(value - _composed[i]) <= _life.WeightEpsilon)
            {
                value = _composed[i];
            }

#if DEBUG
            if (_debugMorphOverride)
            {
                continue;
            }
#endif
            if (force || Math.Abs(value - _composed[i]) > _life.WeightEpsilon)
            {
                SetWeight(target, value);
                weightsChanged = true;
            }
        }

        // P3-LIFE: index 13 across Alert, speakingPlaybackArmed, and mouth ownership — P3-D14
        if (_lookMode == PresenceMode.Alert || mouthOwns || _mode == PresenceMode.Speaking)
        {
            PresenceView.WriteLog("P3-LIFE: wideEe=" + FormatFloat(_composed[(int)MorphTarget.WideEE]));
        }

        var multiplier = _brightness.Evaluate(now);
        var multiplierChanged = Math.Abs(multiplier - _multiplier) > _life.MultiplierEpsilon;
        if (multiplierChanged || force)
        {
            _multiplier = multiplier;
            _view.ApplyGainMultiplier(_multiplier);
        }

        FlushWeights();
        if (force || weightsChanged || multiplierChanged)
        {
            RequestRender();
        }

        EnsureTick(now);
    }

    private void EnsureTick(long nowTicks)
    {
        var changing = ChannelsChanging();
        var staggerPending = !_eyesArmed || !_brightnessArmed || !_expressionArmed;
        if (changing)
        {
            // P3-LIFE: speaking mouth/pulse may use a coarser tick than idle blinks — P3-D22
            var speakingMotion = _mouth.IsChanging
                || (_lookMode == PresenceMode.Speaking && _brightness.IsChanging);
            var interval = speakingMotion ? _life.SpeakingTickIntervalMs : _life.TickIntervalMs;
            ApplyTick(interval, repeating: true);
            return;
        }

        if (staggerPending)
        {
            ApplyTick(
                PresenceLife.DelayMilliseconds(
                    _coordinator.NextPendingMs(nowTicks, _eyesArmed, _brightnessArmed, _expressionArmed)),
                repeating: false);
            return;
        }

        LogSettled();
        if (_speakingPlaybackArmed && _onsetTicks != long.MaxValue)
        {
            if (_onsetTicks <= nowTicks)
            {
                ApplyTick(1, repeating: false);
                return;
            }

            ApplyTick(
                PresenceLife.DelayMilliseconds(PresenceLife.ElapsedMilliseconds(nowTicks, _onsetTicks)),
                repeating: false);
            return;
        }

        if (_blink.HasScheduledBlink)
        {
            ApplyTick(PresenceLife.DelayMilliseconds(_blink.RemainingMs(nowTicks)), repeating: false);
            return;
        }

        StopTick();
    }

    private bool ChannelsChanging()
    {
        return _blink.IsChanging || _expression.IsChanging || _brightness.IsChanging || _mouth.IsChanging;
    }

    private void ApplyTick(int milliseconds, bool repeating)
    {
        if (_paused)
        {
            StopTick();
            return;
        }

        var interval = TimeSpan.FromMilliseconds(milliseconds);
        if (_tickRunning && _tick.IsRepeating == repeating && _tick.Interval == interval)
        {
            return;
        }

        _tick.Stop();
        _tick.IsRepeating = repeating;
        _tick.Interval = interval;
        _tick.Start();
        if (!_tickRunning)
        {
            PresenceView.WriteLog("P3-LIFE: tick started");
        }

        _tickRunning = true;
    }

    private void LogBlinkTransition(BlinkPhase previous)
    {
        if (_blink.Phase == previous)
        {
            return;
        }

        if (_blink.Phase == BlinkPhase.Closing)
        {
            PresenceView.WriteLog(
                "P3-LIFE: blink start intervalMs=" + _blink.StartedIntervalMs.ToString(CultureInfo.InvariantCulture)
                + " depth=" + FormatFloat(_life.BlinkDepth(_lookMode))
                + " peak=" + FormatFloat(_blink.Peak));
        }
        else if (_blink.Phase == BlinkPhase.Opening)
        {
            PresenceView.WriteLog(
                "P3-LIFE: blink closed weight=" + FormatFloat(_blink.LidAmount)
                + " peak=" + FormatFloat(_blink.Peak)
                + " mix=" + FormatFloat(_blink.Weight(MorphTarget.BlinkLeft))
                + "," + FormatFloat(_blink.Weight(MorphTarget.BlinkRight))
                + "," + FormatFloat(_blink.Weight(MorphTarget.BlinkBoth)));
        }
        else if (_blink.Phase == BlinkPhase.Rest && previous == BlinkPhase.Opening)
        {
            PresenceView.WriteLog("P3-LIFE: blink open");
        }
    }

    private void LogMouthStep()
    {
        PresenceView.WriteLog(
            "P3-LIFE: mouth step L=" + FormatFloat(_mouth.Level)
            + " weights="
            + FormatFloat(_mouth.Weight(MorphTarget.JawOpen))
            + "," + FormatFloat(_mouth.Weight(MorphTarget.OpenAH))
            + "," + FormatFloat(_mouth.Weight(MorphTarget.MidOpenEhUh))
            + "," + FormatFloat(_mouth.Weight(MorphTarget.ClosedMBP))
            + "," + FormatFloat(_mouth.Weight(MorphTarget.RoundOOW))
            + "," + FormatFloat(_mouth.Weight(MorphTarget.WideEE))
            + "," + FormatFloat(_mouth.Weight(MorphTarget.TeethFV)));
    }

    private void LogSettled()
    {
        var line = "P3-LIFE: settled mode=" + _mode
            + " weights=" + FormatWeights()
            + " multiplier=" + FormatFloat(_multiplier);
        if (_lookMode != _mode)
        {
            line = "P3-LIFE: settled mode=" + _mode
                + " look=" + _lookMode
                + " weights=" + FormatWeights()
                + " multiplier=" + FormatFloat(_multiplier);
        }

        PresenceView.WriteLog(line);
    }

    private void LogStagger(string channel, long nowTicks)
    {
        PresenceView.WriteLog(
            "P3-LIFE: stagger " + channel + " t="
            + ((int)Math.Round(_coordinator.ElapsedMs(nowTicks))).ToString(CultureInfo.InvariantCulture));
    }

    private string FormatWeights()
    {
        var builder = new StringBuilder();
        for (var i = 0; i < MorphTargets.MorphTargetCount; i++)
        {
            if (i > (int)MorphTarget.BlinkLeft)
            {
                builder.Append(',');
            }

            builder.Append(FormatFloat(_composed[i]));
        }

        return builder.ToString();
    }

    private static string FormatFloat(float value)
    {
        return value.ToString("G9", CultureInfo.InvariantCulture);
    }

    private void SetWeight(MorphTarget target, float weight)
    {
        if (_morph is null)
        {
            return;
        }

        var clamped = Math.Clamp(weight, PresenceLife.WeightMin, PresenceLife.WeightMax);
        _morph.SetWeight((int)target, clamped);
        _composed[(int)target] = clamped;
        _weightsDirty = true;
    }

    private void ResetAllWeights()
    {
        foreach (MorphTarget target in Enum.GetValues<MorphTarget>())
        {
            SetWeight(target, PresenceLife.WeightMin);
        }
    }

    private void FlushWeights()
    {
        if (!_weightsDirty || _morph is null)
        {
            return;
        }

        _morph.WeightUpdated();
        _weightsDirty = false;
    }

    private void RequestRender()
    {
        _awaitingPresent = true;
        _view.RequestRender();
    }

    private void StopTick()
    {
        if (!_tickRunning)
        {
            return;
        }

        _tick.Stop();
        _tickRunning = false;
        PresenceView.WriteLog("P3-LIFE: tick stopped");
    }

    private static long NowTicks()
    {
        return Stopwatch.GetTimestamp();
    }
}
