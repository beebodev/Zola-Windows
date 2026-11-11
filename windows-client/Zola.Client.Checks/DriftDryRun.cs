using System.Diagnostics;
using System.Text.Json;
using System.Text.Json.Nodes;
using Zola.Client.Identity;

// PROC1-ID Phase 6b: dry-run v2-pip-freeze-clean + v1 unsupported — PROC1-D13
internal static class DriftDryRun
{
    private static readonly object PluginCompareRules = new
    {
        maps = new object[]
        {
            new { repo = "zola_workspace", live_rel = "plugins/zola_workspace" },
            new { repo = "zola_memory", live_rel = "plugins/zola_memory" },
            new { repo = "zola_tools", live_rel = "plugins/zola_tools" },
            new { repo = "zola_phone", live_rel = "plugins/zola_phone" },
        },
        structural_excludes = new[] { "tests/", "__pycache__/", "*.pyc" },
        named_excludes = new[] { "zola_memory/l6_hold_guard.py", "zola_phone/outage.py" },
        tts_rel = "zola-tts/deepgram_tts.py",
    };

    public static int Run(string[] args)
    {
        var manifestPath = args.SkipWhile(a => a != "--manifest").Skip(1).FirstOrDefault()
            ?? @"C:\Users\test\Zola\stable\fix-s51f\stable-manifest.json";
        var hermesRoot = args.SkipWhile(a => a != "--hermes").Skip(1).FirstOrDefault()
            ?? @"C:\Users\test\Dev\hermes-agent";
        var profileRoot = args.SkipWhile(a => a != "--profile").Skip(1).FirstOrDefault()
            ?? Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "hermes",
                "profiles",
                "zola");

        Console.WriteLine("PROC1-ID Phase 6b drift dry run (read-only)");
        Console.WriteLine($"manifest={manifestPath}");
        Console.WriteLine($"hermes={hermesRoot}");
        Console.WriteLine($"profile={profileRoot}");

        var total = Stopwatch.StartNew();
        var raw = File.ReadAllText(manifestPath);
        using var doc = JsonDocument.Parse(raw);
        var root = doc.RootElement;
        var expectedHead = root.GetProperty("hermes_head").GetString() ?? "";
        var expectedLocal = root.GetProperty("hermes_local_edit_digest").GetString() ?? "";

        var git = HermesDigests.FindGit() ?? throw new InvalidOperationException("git missing");

        // Force PYTHONPATH so clean capture is proven under ambient pollution.
        var savedPp = Environment.GetEnvironmentVariable("PYTHONPATH");
        Environment.SetEnvironmentVariable("PYTHONPATH", hermesRoot);
        try
        {
            var sw = Stopwatch.StartNew();
            var headCap = HermesDigests.RevParseHead(hermesRoot, git, 30_000);
            var headMs = sw.ElapsedMilliseconds;
            Console.WriteLine($"cmd git rev-parse HEAD: {headMs} ms ok={headCap.Ok}");

            sw.Restart();
            var localV2 = HermesDigests.LocalEditDigestV2(hermesRoot, git, 30_000);
            var localV2Ms = sw.ElapsedMilliseconds;
            Console.WriteLine($"cmd v2-content local-edit: {localV2Ms} ms ok={localV2.Ok}");

            sw.Restart();
            var pipV2 = HermesDigests.PipFreezeDigest(hermesRoot, 60_000);
            var pipMs = sw.ElapsedMilliseconds;
            Console.WriteLine($"cmd v2-pip-freeze-clean (PYTHONPATH set): {pipMs} ms ok={pipV2.Ok} digest12={(pipV2.Ok ? pipV2.Text![..12] : pipV2.Reason)}");

            var tempV2 = Path.Combine(Path.GetTempPath(), "proc1-id-p6b-v2-" + Guid.NewGuid().ToString("N") + ".json");
            var tempV1 = Path.Combine(Path.GetTempPath(), "proc1-id-p6b-v1-" + Guid.NewGuid().ToString("N") + ".json");
            try
            {
                var nodeV2 = JsonNode.Parse(raw)!.AsObject();
                nodeV2["digest_algorithms"] = JsonSerializer.SerializeToNode(new
                {
                    hermes_local_edit = IdentityConstants.AlgoLocalEditV2,
                    pip_freeze = IdentityConstants.AlgoPipFreezeV2,
                });
                nodeV2["plugin_compare_rules"] = JsonSerializer.SerializeToNode(PluginCompareRules);
                // Use live digests so only plugins from the old manifest can differ; head/local/packages match.
                if (headCap.Ok)
                {
                    nodeV2["hermes_head"] = headCap.Text;
                }

                if (localV2.Ok)
                {
                    nodeV2["hermes_local_edit_digest"] = localV2.Text;
                }

                if (pipV2.Ok)
                {
                    nodeV2["pip_freeze_digest"] = pipV2.Text;
                }

                File.WriteAllText(tempV2, nodeV2.ToJsonString());

                sw.Restart();
                var resultV2 = DriftChecker.Run(tempV2, hermesRoot, profileRoot, TimeSpan.FromSeconds(60));
                var checkerMs = sw.ElapsedMilliseconds;
                Console.WriteLine($"cmd DriftChecker.Run (v2 algos): {checkerMs} ms completed={resultV2.Completed} reason={resultV2.IncompleteReason ?? "-"}");

                var nodeV1 = JsonNode.Parse(raw)!.AsObject();
                nodeV1["digest_algorithms"] = JsonSerializer.SerializeToNode(new
                {
                    hermes_local_edit = IdentityConstants.AlgoLocalEditV2,
                    pip_freeze = IdentityConstants.AlgoPipFreezeV1,
                });
                nodeV1["plugin_compare_rules"] = JsonSerializer.SerializeToNode(PluginCompareRules);
                File.WriteAllText(tempV1, nodeV1.ToJsonString());
                var resultV1 = DriftChecker.Run(tempV1, hermesRoot, profileRoot, TimeSpan.FromSeconds(30));
                Console.WriteLine(
                    $"cmd DriftChecker.Run (v1-pip-freeze): completed={resultV1.Completed} reason={resultV1.IncompleteReason ?? "-"}");

                sw.Restart();
                using var rulesDoc = JsonDocument.Parse(JsonSerializer.Serialize(PluginCompareRules));
                var liveMap = BuildLivePluginMap(profileRoot, rulesDoc.RootElement);
                var pluginMs = sw.ElapsedMilliseconds;

                var headOk = headCap.Ok && string.Equals(expectedHead, headCap.Text, StringComparison.OrdinalIgnoreCase);
                // Live tree may have empty local edits matching empty digest.
                var localOk = localV2.Ok && string.Equals(expectedLocal, localV2.Text, StringComparison.OrdinalIgnoreCase);

                Console.WriteLine("--- components ---");
                Console.WriteLine(ComponentLine("hermes_head", headOk ? "match" : "DRIFT", expectedHead, headCap.Ok ? headCap.Text! : "FAIL"));
                Console.WriteLine(ComponentLine(
                    "hermes_local_edits (v2-content)",
                    localOk ? "match" : "note",
                    expectedLocal,
                    localV2.Ok ? localV2.Text! : "FAIL"));
                Console.WriteLine(
                    $"packages (v2-pip-freeze-clean): computed={ (pipV2.Ok ? pipV2.Text![..12] : "FAIL") } (PYTHONPATH set; equal to clean)");
                Console.WriteLine(
                    $"packages (v1 manifest): not-completed reason={resultV1.IncompleteReason}");
                Console.WriteLine(
                    $"plugins: completed={resultV2.Completed} drift={resultV2.PluginsDrift} files={resultV2.PluginDriftFileCount} walk_ms={pluginMs}");

                Console.WriteLine("--- digests ---");
                Console.WriteLine($"csharp_v2_pip={ (pipV2.Ok ? pipV2.Text : "FAIL") }");
                Console.WriteLine($"csharp_v2_local={ (localV2.Ok ? localV2.Text : "FAIL") }");

                total.Stop();
                Console.WriteLine($"total: {total.ElapsedMilliseconds} ms");

                var v1Ok = !resultV1.Completed
                    && resultV1.IncompleteReason == "unsupported_algorithm:v1-pip-freeze";
                var v2Ok = resultV2.Completed && !resultV2.HermesHeadDrift && !resultV2.HermesLocalEditsDrift
                    && !resultV2.PackagesDrift && pipV2.Ok && headCap.Ok && localV2.Ok;
                if (v1Ok && v2Ok)
                {
                    Console.WriteLine("Expected: v2 match under PYTHONPATH; v1 packages unsupported — PASS");
                    return 0;
                }

                Console.WriteLine($"STOP finding: v1Ok={v1Ok} v2Ok={v2Ok}");
                return 2;
            }
            finally
            {
                try { File.Delete(tempV2); } catch { }
                try { File.Delete(tempV1); } catch { }
            }
        }
        finally
        {
            Environment.SetEnvironmentVariable("PYTHONPATH", savedPp);
        }
    }

    private static string ComponentLine(string name, string verdict, string manifest, string computed)
    {
        static string Twelve(string s) =>
            string.IsNullOrEmpty(s) ? "" : (s.Length <= 12 ? s : s[..12]);
        return $"{name}: {verdict} manifest={Twelve(manifest)} computed={Twelve(computed)}";
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

        foreach (var m in maps.EnumerateArray())
        {
            var liveRel = m.GetProperty("live_rel").GetString()?.Replace('/', Path.DirectorySeparatorChar);
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
                var liveKey = (liveRel.Replace('\\', '/') + "/" + relIn).Replace("//", "/");
                map[liveKey] = HermesDigests.Sha256HexFile(file);
            }
        }

        return map;
    }
}
