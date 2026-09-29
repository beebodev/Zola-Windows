// P3-LOOK: approved pipeline — sRGB decode × gain → ACES → sRGB encode — P3-D20
#pragma pack_matrix(row_major)

cbuffer cbBorderEffect : register(b6)
{
    float4 Color;
    float4x4 Param;
    float viewportScale;
    float3 padding9;
};

Texture2D texDiffuseMap : register(t0);
SamplerState samplerSurface : register(s0);

struct MeshOutlinePS_INPUT
{
    float4 Pos : SV_POSITION;
    noperspective float2 Tex : TEXCOORD0;
};

static const float AcesA = 2.51f;
static const float AcesB = 0.03f;
static const float AcesC = 2.43f;
static const float AcesD = 0.59f;
static const float AcesE = 0.14f;

float3 AcesFilmic(float3 x)
{
    return saturate((x * (AcesA * x + AcesB)) / (x * (AcesC * x + AcesD) + AcesE));
}

float SrgbToLinear1(float c)
{
    return c <= 0.04045f ? c / 12.92f : pow(abs((c + 0.055f) / 1.055f), 2.4f);
}

float LinearToSrgb1(float c)
{
    return c <= 0.0031308f ? 12.92f * c : 1.055f * pow(saturate(c), 1.0f / 2.4f) - 0.055f;
}

float3 SrgbToLinear(float3 c)
{
    return float3(SrgbToLinear1(c.r), SrgbToLinear1(c.g), SrgbToLinear1(c.b));
}

float3 LinearToSrgb(float3 c)
{
    return float3(LinearToSrgb1(c.r), LinearToSrgb1(c.g), LinearToSrgb1(c.b));
}

// P3-LIFE: lerp token RGB over the field (source.a) so the background is never tone-mapped — P3-D22
float4 main(MeshOutlinePS_INPUT pin) : SV_Target
{
    float4 source = texDiffuseMap.Sample(samplerSurface, pin.Tex);
    float3 mapped = LinearToSrgb(AcesFilmic(SrgbToLinear(source.rgb) * Color.a));
    float3 outRgb = lerp(Color.rgb, saturate(mapped), source.a);
    return float4(outRgb, 1.0f);
}
