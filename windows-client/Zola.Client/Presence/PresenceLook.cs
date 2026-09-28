using System.Collections.Generic;
using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace Zola.Client.Presence;

// P3-LOOK: approved pipeline — unlit albedo, gain, mip bias, camera — P3-D20
internal sealed class PresenceLook
{
    internal const string DebugSubfolder = "debug";
    internal const string DebugFileName = "presence-look.json";
    internal const string EffectiveFileName = "presence-look.effective.json";

    internal const float DefaultCameraX = 0f;
    internal const float DefaultCameraY = 0.05f;
    internal const float DefaultCameraZ = 3.15f;
    internal const float DefaultLookX = 0f;
    internal const float DefaultLookY = 0f;
    internal const float DefaultLookZ = -3.372f;
    internal const float DefaultCameraFovDegrees = 35f;
    internal const float DefaultToneMapGain = 4.4f;
    internal const float DefaultMipLodBias = 0.75f;

    internal const byte ByteMin = 0;
    internal const byte ByteMax = 255;
    internal const float CameraXMin = -1.5f;
    internal const float CameraXMax = 1.5f;
    internal const float CameraYMin = -1.5f;
    internal const float CameraYMax = 1.5f;
    internal const float CameraZMin = 1.5f;
    internal const float CameraZMax = 6f;
    internal const float LookXMin = -1.5f;
    internal const float LookXMax = 1.5f;
    internal const float LookYMin = -2f;
    internal const float LookYMax = 2f;
    internal const float LookZMin = -8f;
    internal const float LookZMax = -1f;
    internal const float FovMin = 22f;
    internal const float FovMax = 50f;
    internal const float ToneMapGainMin = 0f;
    internal const float ToneMapGainMax = 16f;
    internal const float MipLodBiasMin = 0f;
    internal const float MipLodBiasMax = 2f;
    internal const byte DisplayBlackByte = 8;
    internal const float AcesA = 2.51f;
    internal const float AcesB = 0.03f;
    internal const float AcesC = 2.43f;
    internal const float AcesD = 0.59f;
    internal const float AcesE = 0.14f;

    internal float CameraX { get; private set; } = DefaultCameraX;
    internal float CameraY { get; private set; } = DefaultCameraY;
    internal float CameraZ { get; private set; } = DefaultCameraZ;
    internal float LookX { get; private set; } = DefaultLookX;
    internal float LookY { get; private set; } = DefaultLookY;
    internal float LookZ { get; private set; } = DefaultLookZ;
    internal float CameraFovDegrees { get; private set; } = DefaultCameraFovDegrees;
    internal float ToneMapGain { get; private set; } = DefaultToneMapGain;
    internal float MipLodBias { get; private set; } = DefaultMipLodBias;
#if DEBUG
    internal bool ToneMapForceFail { get; private set; }
#endif

    internal static PresenceLook CreateDefault()
    {
        return new PresenceLook();
    }

    internal PresenceLook Clone()
    {
        return (PresenceLook)MemberwiseClone();
    }

    // P3-LOOK: F12 replace starts from defaults; every key is required — P3-D19
    internal static readonly string[] RequiredKeys =
    {
        "cameraX", "cameraY", "cameraZ", "lookX", "lookY", "lookZ", "fov",
        "toneMapGain", "mipLodBias",
#if DEBUG
        "toneMapForceFail",
#endif
    };

    internal static bool TryMergeJson(string json, PresenceLook inherit, out PresenceLook next, out string reason)
    {
        return TryAssignObject(json, inherit.Clone(), requireAllKeys: false, out next, out reason);
    }

    internal static bool TryReplaceJson(string json, out PresenceLook next, out string reason)
    {
        return TryAssignObject(json, CreateDefault(), requireAllKeys: true, out next, out reason);
    }

    private static bool TryAssignObject(
        string json,
        PresenceLook seed,
        bool requireAllKeys,
        out PresenceLook next,
        out string reason)
    {
        next = seed;
        reason = "";
        JsonDocument document;
        try
        {
            document = JsonDocument.Parse(json);
        }
        catch (JsonException ex)
        {
            reason = "invalid JSON: " + ex.Message;
            return false;
        }

        var seen = new HashSet<string>(StringComparer.Ordinal);
        using (document)
        {
            if (document.RootElement.ValueKind != JsonValueKind.Object)
            {
                reason = "root is not an object";
                return false;
            }

            foreach (var property in document.RootElement.EnumerateObject())
            {
                if (!TryAssign(next, property, out reason))
                {
                    return false;
                }

                seen.Add(property.Name);
            }
        }

        if (requireAllKeys)
        {
            foreach (var key in RequiredKeys)
            {
                if (!seen.Contains(key))
                {
                    reason = key + " is missing";
                    return false;
                }
            }
        }

        return true;
    }

    internal string ToCanonicalJson()
    {
        var builder = new StringBuilder();
        builder.Append('{');
        for (var i = 0; i < RequiredKeys.Length; i++)
        {
            if (i > 0)
            {
                builder.Append(',');
            }

            var key = RequiredKeys[i];
            builder.Append('"').Append(key).Append("\":");
            AppendCanonicalValue(builder, key);
        }

        builder.Append('}');
        return builder.ToString();
    }

    internal string Fingerprint()
    {
        var bytes = SHA256.HashData(Encoding.UTF8.GetBytes(ToCanonicalJson()));
        return Convert.ToHexString(bytes).ToLowerInvariant();
    }

    private static bool TryAssign(PresenceLook look, JsonProperty property, out string reason)
    {
        reason = "";
        var key = property.Name;
        var value = property.Value;
        switch (key)
        {
            case "cameraX": return AssignFloat(key, value, CameraXMin, CameraXMax, v => look.CameraX = v, out reason);
            case "cameraY": return AssignFloat(key, value, CameraYMin, CameraYMax, v => look.CameraY = v, out reason);
            case "cameraZ": return AssignFloat(key, value, CameraZMin, CameraZMax, v => look.CameraZ = v, out reason);
            case "lookX": return AssignFloat(key, value, LookXMin, LookXMax, v => look.LookX = v, out reason);
            case "lookY": return AssignFloat(key, value, LookYMin, LookYMax, v => look.LookY = v, out reason);
            case "lookZ": return AssignFloat(key, value, LookZMin, LookZMax, v => look.LookZ = v, out reason);
            case "fov": return AssignFloat(key, value, FovMin, FovMax, v => look.CameraFovDegrees = v, out reason);
            case "toneMapGain": return AssignFloat(key, value, ToneMapGainMin, ToneMapGainMax, v => look.ToneMapGain = v, out reason);
            case "mipLodBias": return AssignFloat(key, value, MipLodBiasMin, MipLodBiasMax, v => look.MipLodBias = v, out reason);
#if DEBUG
            case "toneMapForceFail": return AssignBool(key, value, v => look.ToneMapForceFail = v, out reason);
#endif
            default:
                reason = key + " is not a look value";
                return false;
        }
    }

    private static bool AssignFloat(string key, JsonElement value, float min, float max, Action<float> assign, out string reason)
    {
        if (value.ValueKind != JsonValueKind.Number || !value.TryGetDouble(out var parsed))
        {
            reason = key + " is not a number";
            return false;
        }

        if (parsed < min || parsed > max)
        {
            reason = key + " out of range";
            return false;
        }

        assign((float)parsed);
        reason = "";
        return true;
    }

#if DEBUG
    private static bool AssignBool(string key, JsonElement value, Action<bool> assign, out string reason)
    {
        if (value.ValueKind == JsonValueKind.True)
        {
            assign(true);
            reason = "";
            return true;
        }

        if (value.ValueKind == JsonValueKind.False)
        {
            assign(false);
            reason = "";
            return true;
        }

        reason = key + " is not a boolean";
        return false;
    }
#endif

    private void AppendCanonicalValue(StringBuilder builder, string key)
    {
        switch (key)
        {
            case "cameraX": AppendFloat(builder, CameraX); return;
            case "cameraY": AppendFloat(builder, CameraY); return;
            case "cameraZ": AppendFloat(builder, CameraZ); return;
            case "lookX": AppendFloat(builder, LookX); return;
            case "lookY": AppendFloat(builder, LookY); return;
            case "lookZ": AppendFloat(builder, LookZ); return;
            case "fov": AppendFloat(builder, CameraFovDegrees); return;
            case "toneMapGain": AppendFloat(builder, ToneMapGain); return;
            case "mipLodBias": AppendFloat(builder, MipLodBias); return;
#if DEBUG
            case "toneMapForceFail": AppendBool(builder, ToneMapForceFail); return;
#endif
            default: builder.Append("null"); return;
        }
    }

    private static void AppendFloat(StringBuilder builder, float value)
    {
        builder.Append(value.ToString("G9", CultureInfo.InvariantCulture));
    }

#if DEBUG
    private static void AppendBool(StringBuilder builder, bool value)
    {
        builder.Append(value ? "true" : "false");
    }
#endif
}
