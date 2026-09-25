using System.Text.Json;

namespace Zola.Client.Presence;

internal readonly record struct GlbTextureLocateResult(byte[]? Bytes, string? FailureReason)
{
    internal bool Ok => Bytes is not null;
}

// P3-RENDER: metallic-roughness bytes come from the GLB JSON walk, never a byte offset — P3-D02
internal static class GlbTextureLocator
{
    private const uint GlbMagic = 0x46546C67;
    private const uint GlbVersion = 2;
    private const int HeaderByteCount = 12;
    private const int ChunkHeaderByteCount = 8;
    private const uint JsonChunkType = 0x4E4F534A;
    private const uint BinChunkType = 0x004E4942;
    private const int ChunkAlignment = 4;
    private const string MissingMaterials = "GLB has no materials[0]";
    private const string MissingMetallicRoughness = "GLB materials[0] has no pbrMetallicRoughness.metallicRoughnessTexture.index";
    private const string MissingTextures = "GLB has no textures array";
    private const string TextureIndexOutOfRange = "GLB metallicRoughnessTexture.index is out of range";
    private const string MissingTextureSource = "GLB textures[i] has no source";
    private const string ImageIndexOutOfRange = "GLB textures[i].source is out of range";
    private const string MissingImages = "GLB has no images array";
    private const string MissingBufferView = "GLB images[j] has no bufferView";
    private const string MissingBufferViews = "GLB has no bufferViews array";
    private const string BufferViewIndexOutOfRange = "GLB images[j].bufferView is out of range";
    private const string MissingByteLength = "GLB bufferView has no byteLength";
    private const string BufferViewOutsideBin = "GLB bufferView lies outside the BIN chunk";
    private const string BadMagic = "GLB magic is not glTF";
    private const string BadVersion = "GLB version is not 2";
    private const string LengthMismatch = "GLB declared length does not equal the file length";
    private const string TruncatedHeader = "GLB header is truncated";
    private const string TruncatedChunk = "GLB chunk header or payload lies outside the file";
    private const string MissingJsonChunk = "GLB has no JSON chunk";
    private const string MissingBinChunk = "GLB has no BIN chunk";
    private const string BadJson = "GLB JSON chunk is not valid JSON";

    internal static GlbTextureLocateResult LocateMetallicRoughness(string path)
    {
        byte[] file;
        try
        {
            file = File.ReadAllBytes(path);
        }
        catch (Exception ex)
        {
            return new GlbTextureLocateResult(null, ex.Message);
        }

        return LocateMetallicRoughness(file);
    }

    internal static GlbTextureLocateResult LocateMetallicRoughness(ReadOnlySpan<byte> file)
    {
        if (file.Length < HeaderByteCount)
        {
            return Fail(TruncatedHeader);
        }

        var magic = ReadUInt32(file, 0);
        if (magic != GlbMagic)
        {
            return Fail(BadMagic);
        }

        var version = ReadUInt32(file, 4);
        if (version != GlbVersion)
        {
            return Fail(BadVersion);
        }

        var declaredLength = ReadUInt32(file, 8);
        if (declaredLength != (uint)file.Length)
        {
            return Fail(LengthMismatch);
        }

        ReadOnlySpan<byte> jsonBytes = default;
        ReadOnlySpan<byte> binBytes = default;
        var offset = HeaderByteCount;
        var sawJson = false;
        var sawBin = false;
        while (offset < file.Length)
        {
            if (offset + ChunkHeaderByteCount > file.Length)
            {
                return Fail(TruncatedChunk);
            }

            var chunkLength = ReadUInt32(file, offset);
            var chunkType = ReadUInt32(file, offset + 4);
            var dataStart = offset + ChunkHeaderByteCount;
            if (chunkLength > (uint)(file.Length - dataStart))
            {
                return Fail(TruncatedChunk);
            }

            var data = file.Slice(dataStart, (int)chunkLength);
            if (chunkType == JsonChunkType)
            {
                jsonBytes = data;
                sawJson = true;
            }
            else if (chunkType == BinChunkType)
            {
                binBytes = data;
                sawBin = true;
            }

            var padded = Align((uint)dataStart + chunkLength, ChunkAlignment);
            if (padded > (uint)file.Length)
            {
                return Fail(TruncatedChunk);
            }

            offset = (int)padded;
        }

        if (!sawJson)
        {
            return Fail(MissingJsonChunk);
        }

        if (!sawBin)
        {
            return Fail(MissingBinChunk);
        }

        JsonDocument document;
        try
        {
            document = JsonDocument.Parse(jsonBytes.ToArray());
        }
        catch (JsonException)
        {
            return Fail(BadJson);
        }

        using (document)
        {
            var root = document.RootElement;
            if (!TryGetArray(root, "materials", out var materials) || materials.GetArrayLength() < 1)
            {
                return Fail(MissingMaterials);
            }

            var material = materials[0];
            if (!material.TryGetProperty("pbrMetallicRoughness", out var pbr)
                || !pbr.TryGetProperty("metallicRoughnessTexture", out var textureInfo)
                || !textureInfo.TryGetProperty("index", out var textureIndexElement)
                || !TryGetIndex(textureIndexElement, out var textureIndex))
            {
                return Fail(MissingMetallicRoughness);
            }

            if (!TryGetArray(root, "textures", out var textures))
            {
                return Fail(MissingTextures);
            }

            if (textureIndex >= textures.GetArrayLength())
            {
                return Fail(TextureIndexOutOfRange);
            }

            var texture = textures[textureIndex];
            if (!texture.TryGetProperty("source", out var sourceElement)
                || !TryGetIndex(sourceElement, out var imageIndex))
            {
                return Fail(MissingTextureSource);
            }

            if (!TryGetArray(root, "images", out var images))
            {
                return Fail(MissingImages);
            }

            if (imageIndex >= images.GetArrayLength())
            {
                return Fail(ImageIndexOutOfRange);
            }

            var image = images[imageIndex];
            if (!image.TryGetProperty("bufferView", out var viewIndexElement)
                || !TryGetIndex(viewIndexElement, out var viewIndex))
            {
                return Fail(MissingBufferView);
            }

            if (!TryGetArray(root, "bufferViews", out var bufferViews))
            {
                return Fail(MissingBufferViews);
            }

            if (viewIndex >= bufferViews.GetArrayLength())
            {
                return Fail(BufferViewIndexOutOfRange);
            }

            var view = bufferViews[viewIndex];
            if (!view.TryGetProperty("byteLength", out var lengthElement)
                || !TryGetIndex(lengthElement, out var byteLength))
            {
                return Fail(MissingByteLength);
            }

            var byteOffset = 0;
            if (view.TryGetProperty("byteOffset", out var offsetElement)
                && !TryGetIndex(offsetElement, out byteOffset))
            {
                return Fail(MissingByteLength);
            }

            if ((ulong)byteOffset + (ulong)byteLength > (ulong)binBytes.Length)
            {
                return Fail(BufferViewOutsideBin);
            }

            var slice = binBytes.Slice(byteOffset, byteLength);
            return new GlbTextureLocateResult(slice.ToArray(), null);
        }
    }

    private static GlbTextureLocateResult Fail(string reason) => new(null, reason);

    private static bool TryGetArray(JsonElement parent, string name, out JsonElement array)
    {
        if (parent.TryGetProperty(name, out array) && array.ValueKind == JsonValueKind.Array)
        {
            return true;
        }

        array = default;
        return false;
    }

    private static bool TryGetIndex(JsonElement element, out int value)
    {
        if (element.ValueKind == JsonValueKind.Number && element.TryGetInt32(out value) && value >= 0)
        {
            return true;
        }

        value = 0;
        return false;
    }

    private static uint ReadUInt32(ReadOnlySpan<byte> data, int start)
    {
        return BitConverter.ToUInt32(data.Slice(start, 4));
    }

    private static uint Align(uint value, int alignment)
    {
        var mask = (uint)(alignment - 1);
        return (value + mask) & ~mask;
    }
}
