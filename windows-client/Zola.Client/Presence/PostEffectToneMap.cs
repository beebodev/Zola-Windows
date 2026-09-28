using System.Numerics;
using System.Reflection;
using HelixToolkit.SharpDX;
using HelixToolkit.SharpDX.Core;
using HelixToolkit.SharpDX.Core.Components;
using HelixToolkit.SharpDX.Model.Scene;
using HelixToolkit.SharpDX.Render;
using HelixToolkit.SharpDX.Shaders;
using HelixToolkit.SharpDX.Utilities;
using HelixToolkit.WinUI.SharpDX;
using SharpDX.Direct3D;
using Color4 = HelixToolkit.Maths.Color4;

namespace Zola.Client.Presence;

// P3-LOOK: ACES Filmic post-effect, approved pipeline only — P3-D20
internal sealed class PostEffectToneMap : Element3D
{
    internal const string TechniqueName = "PostEffectToneMap";
    internal const string EmbeddedResourceName = "Zola.Client.Presence.Shaders.AcesTonemap.cso";
    internal const string PixelShaderName = "psAcesTonemap";
    internal const string MissingResourceName = "Zola.Client.Presence.Shaders.MissingTonemap.cso";

    private bool _effectEnabled;
    private float _gain = PresenceLook.DefaultToneMapGain;

    internal bool EffectEnabled
    {
        get => _effectEnabled;
        set
        {
            _effectEnabled = value;
            if (SceneNode is NodePostEffectToneMap node)
            {
                node.EffectEnabled = value;
            }
        }
    }

    internal float Gain
    {
        get => _gain;
        set
        {
            _gain = value;
            if (SceneNode is NodePostEffectToneMap node)
            {
                node.Gain = value;
            }
        }
    }

    internal static bool TryRegister(IEffectsManager manager, string resourceName, out string reason)
    {
        reason = "";
        if (manager.HasTechnique(TechniqueName))
        {
            return true;
        }

        byte[]? bytecode;
        try
        {
            bytecode = LoadBytecode(resourceName);
        }
        catch (Exception ex)
        {
            reason = "shader load failed: " + ex.Message;
            return false;
        }

        if (bytecode is null || bytecode.Length == 0)
        {
            reason = "shader bytecode missing";
            return false;
        }

        try
        {
            var pixel = new ShaderDescription(PixelShaderName, ShaderStage.Pixel, bytecode);
            var technique = new TechniqueDescription(TechniqueName)
            {
                InputLayoutDescription = InputLayoutDescription.EmptyInputLayout,
                PassDescriptions =
                [
                    new ShaderPassDescription(DefaultPassNames.ScreenQuad)
                    {
                        ShaderList =
                        [
                            DefaultVSShaderDescriptions.VSMeshOutlineScreenQuad,
                            pixel,
                        ],
                        BlendStateDescription = DefaultBlendStateDescriptions.BSSourceAlways,
                        DepthStencilStateDescription = DefaultDepthStencilDescriptions.DSSNoDepthNoStencil,
                        RasterStateDescription = DefaultRasterDescriptions.RSOutline,
                        Topology = PrimitiveTopology.TriangleStrip,
                    },
                ],
            };
            manager.AddTechnique(technique);
            return true;
        }
        catch (Exception ex)
        {
            reason = "technique creation failed: " + ex.Message;
            return false;
        }
    }

    internal static byte[]? LoadBytecode(string resourceName)
    {
        var assembly = typeof(PostEffectToneMap).GetTypeInfo().Assembly;
        using var stream = assembly.GetManifestResourceStream(resourceName);
        if (stream is null)
        {
            return null;
        }

        using var memory = new MemoryStream();
        stream.CopyTo(memory);
        return memory.ToArray();
    }

    protected override SceneNode OnCreateSceneNode()
    {
        return new NodePostEffectToneMap();
    }

    protected override void AssignDefaultValuesToSceneNode(SceneNode node)
    {
        base.AssignDefaultValuesToSceneNode(node);
        if (node is NodePostEffectToneMap tone)
        {
            tone.EffectEnabled = _effectEnabled;
            tone.Gain = _gain;
        }
    }
}

internal sealed class NodePostEffectToneMap : SceneNode
{
    internal bool EffectEnabled
    {
        get => RenderCore is PostEffectToneMapCore core && core.EffectEnabled;
        set
        {
            if (RenderCore is PostEffectToneMapCore core)
            {
                core.EffectEnabled = value;
            }
        }
    }

    internal float Gain
    {
        get => RenderCore is PostEffectToneMapCore core ? core.Gain : PresenceLook.DefaultToneMapGain;
        set
        {
            if (RenderCore is PostEffectToneMapCore core)
            {
                core.Gain = value;
            }
        }
    }

    protected override RenderCore OnCreateRenderCore()
    {
        return new PostEffectToneMapCore();
    }

    protected override IRenderTechnique? OnCreateRenderTechnique(IEffectsManager effectsManager)
    {
        return effectsManager[PostEffectToneMap.TechniqueName];
    }

    public sealed override bool HitTest(HitTestContext? context, ref List<HitTestResult> hits)
    {
        return false;
    }

    protected sealed override bool OnHitTest(HitTestContext? context, Matrix4x4 totalModelMatrix, ref List<HitTestResult> hits)
    {
        return false;
    }
}

internal sealed class PostEffectToneMapCore : RenderCore
{
    private readonly ConstantBufferComponent _modelCb;
    private BorderEffectStruct _model;
    private ShaderPass? _pass;
    private SamplerStateProxy? _sampler;
    private int _textureSlot;
    private int _samplerSlot;
    private bool _effectEnabled;
    private float _gain = PresenceLook.DefaultToneMapGain;

    internal PostEffectToneMapCore()
        : base(RenderType.GlobalEffect)
    {
        _modelCb = AddComponent(new ConstantBufferComponent(
            new ConstantBufferDescription(DefaultBufferNames.BorderEffectCB, BorderEffectStruct.SizeInBytes)));
    }

    internal bool EffectEnabled
    {
        get => _effectEnabled;
        set => SetAffectsCanRenderFlag(ref _effectEnabled, value);
    }

    internal float Gain
    {
        get => _gain;
        set => _gain = value;
    }

    protected override bool OnAttach(IRenderTechnique? technique)
    {
        if (technique is null || technique.IsNull)
        {
            return false;
        }

        _pass = technique.GetPass(DefaultPassNames.ScreenQuad);
        if (_pass is null || _pass.IsNULL)
        {
            return false;
        }

        _textureSlot = _pass.PixelShader.ShaderResourceViewMapping.TryGetBindSlot(DefaultBufferNames.DiffuseMapTB);
        _samplerSlot = _pass.PixelShader.SamplerMapping.TryGetBindSlot(DefaultSamplerStateNames.SurfaceSampler);
        _sampler = technique.EffectsManager?.StateManager?.Register(DefaultSamplers.LinearSamplerClampAni1);
        return _sampler is not null;
    }

    protected override void OnDetach()
    {
        RemoveAndDispose(ref _sampler);
        _pass = null;
    }

    protected override bool OnUpdateCanRenderFlag()
    {
        return IsAttached && _effectEnabled && _pass is not null && !_pass.IsNULL;
    }

    public override void Render(RenderContext context, DeviceContextProxy deviceContext)
    {
        var buffer = context.RenderHost.RenderBuffer?.FullResPPBuffer;
        if (buffer?.CurrentSRV is null || buffer.NextRTV is null)
        {
            return;
        }

        // P3-LOOK: Color.a is gain; sRGB decode/encode are baked into the shader — P3-D20
        _model.Color = new Color4(0f, 0f, 0f, _gain);
        _modelCb.Upload(deviceContext, ref _model);
        deviceContext.SetRenderTarget(buffer.NextRTV);
        var viewport = context.Viewport;
        deviceContext.SetViewport(ref viewport);
        deviceContext.SetScissorRectangle(ref viewport);
        _pass!.BindShader(deviceContext);
        _pass.BindStates(deviceContext, StateType.All);
        _pass.PixelShader.BindTexture(deviceContext, _textureSlot, buffer.CurrentSRV);
        _pass.PixelShader.BindSampler(deviceContext, _samplerSlot, _sampler);
        deviceContext.Draw(4, 0);
        _pass.PixelShader.BindTexture(deviceContext, _textureSlot, null);
        buffer.SwapTargets();
    }
}
