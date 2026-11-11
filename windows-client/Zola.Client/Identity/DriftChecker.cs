using System.Text.Json;

namespace Zola.Client.Identity;

// PROC1-ID: stable-only drift check; rules come only from the manifest — PROC1-D13
public static class DriftChecker
{
    // PROC1-ID Phase 6b: at most one packages_capture file per process — PROC1-D13
    private static int _packagesCaptureWritten;

    public static DriftCheckResult Run(
        string manifestPath,
        string hermesRoot,
        string profileRoot,
        TimeSpan timeout,
        string? pipFreezePath = null,
        Func<string, IEnumerable<string>, int, HermesDigests.CaptureResult>? capture = null)
    {
        var sw = System.Diagnostics.Stopwatch.StartNew();
        try
        {
            if (!File.Exists(manifestPath))
            {
                return DriftCheckResult.Incomplete("missing_manifest");
            }

            using var doc = JsonDocument.Parse(File.ReadAllText(manifestPath));
            var root = doc.RootElement;
            if (!root.TryGetProperty("digest_algorithms", out var algos)
                || !root.TryGetProperty("plugin_compare_rules", out var rules))
            {
                return DriftCheckResult.Incomplete("missing_rules");
            }

            var localAlgo = algos.TryGetProperty("hermes_local_edit", out var la) ? la.GetString() : null;
            var pipAlgo = algos.TryGetProperty("pip_freeze", out var pa) ? pa.GetString() : null;
            // PROC1-ID Phase 6b: client knows only v2 names; v1 never drifts — PROC1-D13
            if (localAlgo == IdentityConstants.AlgoLocalEditV1)
            {
                return DriftCheckResult.Incomplete("unsupported_algorithm:" + IdentityConstants.AlgoLocalEditV1);
            }

            if (pipAlgo == IdentityConstants.AlgoPipFreezeV1)
            {
                return DriftCheckResult.Incomplete("unsupported_algorithm:" + IdentityConstants.AlgoPipFreezeV1);
            }

            if (localAlgo != IdentityConstants.AlgoLocalEditV2)
            {
                return DriftCheckResult.Incomplete("unsupported_algorithm:" + (localAlgo ?? "missing"));
            }

            if (pipAlgo != IdentityConstants.AlgoPipFreezeV2)
            {
                return DriftCheckResult.Incomplete("unsupported_algorithm:" + (pipAlgo ?? "missing"));
            }

            var git = HermesDigests.FindGit();
            if (git is null)
            {
                return DriftCheckResult.Incomplete("missing:git");
            }

            var remain = (int)Math.Max(1, timeout.TotalMilliseconds - sw.ElapsedMilliseconds);
            var headCap = HermesDigests.RevParseHead(hermesRoot, git, remain);
            if (!headCap.Ok)
            {
                return DriftCheckResult.Incomplete(headCap.Reason ?? "head");
            }

            remain = (int)Math.Max(1, timeout.TotalMilliseconds - sw.ElapsedMilliseconds);
            var localCap = HermesDigests.LocalEditDigestV2(hermesRoot, git, remain);
            if (!localCap.Ok)
            {
                return DriftCheckResult.Incomplete(localCap.Reason ?? "local_edit");
            }

            remain = (int)Math.Max(1, timeout.TotalMilliseconds - sw.ElapsedMilliseconds);
            var pipFreeze = HermesDigests.PipFreeze(hermesRoot, remain);
            if (!pipFreeze.Ok)
            {
                return DriftCheckResult.Incomplete(pipFreeze.Reason ?? "pip_freeze");
            }

            if (sw.Elapsed >= timeout)
            {
                return DriftCheckResult.Incomplete("timeout");
            }

            var expectedHead = root.GetProperty("hermes_head").GetString();
            var expectedLocal = root.GetProperty("hermes_local_edit_digest").GetString();
            var expectedPip = root.GetProperty("pip_freeze_digest").GetString();

            var livePlugins = BuildLivePluginMap(profileRoot, rules);
            var tagPlugins = ReadHashMap(root.GetProperty("plugins_tag"));
            var pluginDrift = CompareMaps(tagPlugins, livePlugins, out var driftCount);

            var packagesDrift = !string.Equals(expectedPip, pipFreeze.Digest, StringComparison.OrdinalIgnoreCase);
            IReadOnlyList<string> added = Array.Empty<string>();
            IReadOnlyList<string> removed = Array.Empty<string>();
            IReadOnlyList<string> changed = Array.Empty<string>();
            // PROC1-ID Phase 4c: when Switch saved pip-freeze.txt, name add/remove/change — PROC1-D13
            var fromFreeze = false;
            if (packagesDrift
                && !string.IsNullOrWhiteSpace(pipFreezePath)
                && File.Exists(pipFreezePath)
                && !string.IsNullOrEmpty(pipFreeze.Text))
            {
                var promoted = ParseFreezeMap(File.ReadAllText(pipFreezePath));
                var live = ParseFreezeMap(pipFreeze.Text);
                DiffFreezeMaps(promoted, live, out added, out removed, out changed);
                fromFreeze = true;
            }

            // PROC1-ID Phase 6b: persist captured freeze text when packages differ (once per launch) — PROC1-D13
            string? captureName = null;
            if (packagesDrift)
            {
                captureName = TryWritePackagesCapture(pipFreeze.RawText ?? pipFreeze.Text ?? "");
            }

            return new DriftCheckResult
            {
                Completed = true,
                HermesHeadDrift = !string.Equals(expectedHead, headCap.Text, StringComparison.OrdinalIgnoreCase),
                HermesLocalEditsDrift = !string.Equals(expectedLocal, localCap.Text, StringComparison.OrdinalIgnoreCase),
                PackagesDrift = packagesDrift,
                PluginsDrift = pluginDrift,
                PluginDriftFileCount = pluginDrift ? driftCount : null,
                PackagesAdded = added,
                PackagesRemoved = removed,
                PackagesChanged = changed,
                PackagesDiffFromFreezeFile = fromFreeze,
                PackagesCaptureFileName = captureName,
            };
        }
        catch (Exception ex)
        {
            return DriftCheckResult.Incomplete("error:" + ex.GetType().Name);
        }
    }

    public static Dictionary<string, string> ParseFreezeMap(string text)
    {
        var map = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        foreach (var raw in HermesDigests.JoinAsV1CommandOutput(text).Split('\n'))
        {
            var line = raw.Trim();
            if (line.Length == 0 || line.StartsWith('#'))
            {
                continue;
            }

            var name = PackageNameFromFreezeLine(line);
            if (name.Length == 0)
            {
                continue;
            }

            map[name] = line;
        }

        return map;
    }

    public static string PackageNameFromFreezeLine(string line)
    {
        var at = line.IndexOf(" @ ", StringComparison.Ordinal);
        if (at > 0)
        {
            return line[..at].Trim();
        }

        var eq = line.IndexOf("==", StringComparison.Ordinal);
        if (eq > 0)
        {
            return line[..eq].Trim();
        }

        return line.Trim();
    }

    public static void DiffFreezeMaps(
        Dictionary<string, string> promoted,
        Dictionary<string, string> live,
        out IReadOnlyList<string> added,
        out IReadOnlyList<string> removed,
        out IReadOnlyList<string> changed)
    {
        var add = new List<string>();
        var rem = new List<string>();
        var chg = new List<string>();
        foreach (var kv in live)
        {
            if (!promoted.TryGetValue(kv.Key, out var before))
            {
                add.Add(kv.Value);
            }
            else if (!string.Equals(before, kv.Value, StringComparison.Ordinal))
            {
                chg.Add($"{before}->{kv.Value}");
            }
        }

        foreach (var kv in promoted)
        {
            if (!live.ContainsKey(kv.Key))
            {
                rem.Add(kv.Value);
            }
        }

        add.Sort(StringComparer.OrdinalIgnoreCase);
        rem.Sort(StringComparer.OrdinalIgnoreCase);
        chg.Sort(StringComparer.OrdinalIgnoreCase);
        added = add;
        removed = rem;
        changed = chg;
    }

    // PROC1-ID Phase 6b: package lines only as captured; no env values; ≤1 file per process — PROC1-D13
    public static string? TryWritePackagesCapture(string rawFreezeText)
    {
        if (Interlocked.Exchange(ref _packagesCaptureWritten, 1) != 0)
        {
            return null;
        }

        try
        {
            var root = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "ZolaClient",
                "logs");
            Directory.CreateDirectory(root);
            var name = "drift-pip-freeze-" + DateTime.Now.ToString("yyyyMMdd-HHmmss") + ".txt";
            var path = Path.Combine(root, name);
            // PROC1-ID Phase 6b: capture without BOM — PROC1-D13
            File.WriteAllText(path, rawFreezeText ?? "", new System.Text.UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
            return name;
        }
        catch
        {
            return null;
        }
    }

    private static Dictionary<string, string> ReadHashMap(JsonElement el)
    {
        var map = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        if (el.ValueKind != JsonValueKind.Object)
        {
            return map;
        }

        foreach (var p in el.EnumerateObject())
        {
            map[p.Name.Replace('\\', '/')] = p.Value.GetString() ?? "";
        }

        return map;
    }

    private static Dictionary<string, string> BuildLivePluginMap(string profileRoot, JsonElement rules)
    {
        var map = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        if (!rules.TryGetProperty("maps", out var maps))
        {
            return map;
        }

        var named = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        if (rules.TryGetProperty("named_excludes", out var ne))
        {
            foreach (var x in ne.EnumerateArray())
            {
                var s = x.GetString();
                if (!string.IsNullOrEmpty(s))
                {
                    named.Add(s.Replace('\\', '/'));
                }
            }
        }

        foreach (var m in maps.EnumerateArray())
        {
            var liveRel = m.GetProperty("live_rel").GetString()?.Replace('/', Path.DirectorySeparatorChar);
            var repo = m.GetProperty("repo").GetString() ?? "";
            if (string.IsNullOrEmpty(liveRel))
            {
                continue;
            }

            var dir = Path.Combine(profileRoot, liveRel);
            if (!Directory.Exists(dir))
            {
                continue;
            }

            foreach (var file in Directory.EnumerateFiles(dir, "*", SearchOption.AllDirectories))
            {
                var relIn = Path.GetRelativePath(dir, file).Replace('\\', '/');
                var repoKey = $"{repo}/{relIn}";
                if (IsExcluded(repoKey, named))
                {
                    continue;
                }

                var liveKey = (liveRel.Replace('\\', '/') + "/" + relIn).Replace("//", "/");
                map[liveKey] = HermesDigests.Sha256HexFile(file);
            }
        }

        var ttsRel = rules.TryGetProperty("tts_rel", out var tr) ? tr.GetString() : "zola-tts/deepgram_tts.py";
        if (!string.IsNullOrEmpty(ttsRel))
        {
            var tts = Path.Combine(profileRoot, ttsRel.Replace('/', Path.DirectorySeparatorChar));
            if (File.Exists(tts))
            {
                map[ttsRel.Replace('\\', '/')] = HermesDigests.Sha256HexFile(tts);
            }
        }

        return map;
    }

    private static bool IsExcluded(string repoKey, HashSet<string> named)
    {
        var n = repoKey.Replace('\\', '/');
        if (n.Contains("/tests/", StringComparison.OrdinalIgnoreCase)
            || n.StartsWith("tests/", StringComparison.OrdinalIgnoreCase)
            || n.Contains("/__pycache__/", StringComparison.OrdinalIgnoreCase)
            || n.EndsWith(".pyc", StringComparison.OrdinalIgnoreCase))
        {
            return true;
        }

        return named.Contains(n);
    }

    private static bool CompareMaps(
        Dictionary<string, string> tag,
        Dictionary<string, string> live,
        out int driftCount)
    {
        driftCount = 0;
        var keys = new HashSet<string>(tag.Keys, StringComparer.OrdinalIgnoreCase);
        foreach (var k in live.Keys)
        {
            keys.Add(k);
        }

        foreach (var k in keys)
        {
            var hasTag = tag.TryGetValue(k, out var tv);
            var hasLive = live.TryGetValue(k, out var lv);
            if (!hasTag || !hasLive || !string.Equals(tv, lv, StringComparison.OrdinalIgnoreCase))
            {
                driftCount++;
            }
        }

        return driftCount > 0;
    }
}
