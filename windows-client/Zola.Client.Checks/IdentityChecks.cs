using Zola.Client.Identity;

internal sealed partial class CheckRunner
{
    private void Identity(string name, Func<bool> body)
    {
        _identityTotal++;
        Run(name, body, pass =>
        {
            if (pass)
            {
                _identityPassed++;
            }
        });
    }

    private void RunIdentityRows()
    {
        Identity("source: mutex acquire is the first OnLaunched statement; before BuildRole and DumpPruner", () =>
        {
            var app = File.ReadAllText(Path.Combine(ClientRoot(), "Zola.Client", "App.xaml.cs"));
            var launched = app.IndexOf("OnLaunched", StringComparison.Ordinal);
            var body = app.IndexOf('{', launched);
            var i = body + 1;
            while (i < app.Length)
            {
                while (i < app.Length && char.IsWhiteSpace(app[i]))
                {
                    i++;
                }

                if (i + 1 < app.Length && app[i] == '/' && app[i + 1] == '/')
                {
                    while (i < app.Length && app[i] != '\n')
                    {
                        i++;
                    }

                    continue;
                }

                break;
            }

            var first = app[i..];
            var lockIdx = app.IndexOf("SingleInstanceLock.TryAcquire", StringComparison.Ordinal);
            var role = app.IndexOf("BuildRole.Resolve", StringComparison.Ordinal);
            var dump = app.IndexOf("DumpPruner.PruneOnStartup", StringComparison.Ordinal);
            var hermes = app.IndexOf("new HermesProcessManager", StringComparison.Ordinal);
            return launched >= 0 && first.StartsWith("_instanceLock = SingleInstanceLock.TryAcquire", StringComparison.Ordinal)
                && lockIdx > launched && role > lockIdx && dump > role && hermes > dump;
        });

        Identity("source: Closed releases lock after serve, watcher, and phone stops", () =>
        {
            var app = File.ReadAllText(Path.Combine(ClientRoot(), "Zola.Client", "App.xaml.cs"));
            var closed = app.IndexOf("_window.Closed", StringComparison.Ordinal);
            var phone = app.IndexOf("_phone.StopDeliberate", closed, StringComparison.Ordinal);
            var watcher = app.IndexOf("_watcher.StopDeliberate", closed, StringComparison.Ordinal);
            var serve = app.IndexOf("_backend.Shutdown", closed, StringComparison.Ordinal);
            var release = app.IndexOf("_instanceLock?.Dispose", closed, StringComparison.Ordinal);
            return closed >= 0 && phone > closed && watcher > phone && serve > watcher && release > serve;
        });

        Identity("identity log lines cover role, status_write, drift outcomes; refuse writes none", () =>
        {
            var app = File.ReadAllText(Path.Combine(ClientRoot(), "Zola.Client", "App.xaml.cs"));
            var refuseBlockStart = app.IndexOf("if (!_instanceLock.Owned)", StringComparison.Ordinal);
            var refuseBlockEnd = app.IndexOf("Environment.Exit(0)", StringComparison.Ordinal);
            var refuse = app[refuseBlockStart..refuseBlockEnd];
            var owned = app[refuseBlockEnd..];
            return refuse.Contains("Debug.WriteLine", StringComparison.Ordinal)
                && !refuse.Contains("IdentityLog.Write", StringComparison.Ordinal)
                && !refuse.Contains("SupervisionLog", StringComparison.Ordinal)
                && owned.Contains("IdentityLog.RoleLine", StringComparison.Ordinal)
                && owned.Contains("IdentityLog.StatusWriteOk", StringComparison.Ordinal)
                && owned.Contains("IdentityLog.StatusWriteFailed", StringComparison.Ordinal)
                && owned.Contains("IdentityLog.DriftCompletedNone", StringComparison.Ordinal)
                && owned.Contains("IdentityLog.DriftCompleted(", StringComparison.Ordinal)
                && owned.Contains("IdentityLog.DriftIncomplete", StringComparison.Ordinal)
                && owned.Contains("IdentityLog.DriftPackagesCapture", StringComparison.Ordinal)
                && IdentityLog.RoleLine("stable", "ok", "t").StartsWith("identity role=", StringComparison.Ordinal)
                && IdentityLog.StatusWriteOk() == "identity status_write ok"
                && IdentityLog.DriftCompletedNone() == "drift completed=true components=none"
                && IdentityLog.DriftIncomplete("hermes_root") == "drift completed=false reason=hermes_root"
                && IdentityLog.DriftPackagesCapture("drift-pip-freeze-20261110-150908.txt")
                    == "drift packages_capture=drift-pip-freeze-20261110-150908.txt";
        });

        Identity("packages drift writes one capture file under ZolaClient logs and logs packages_capture", () =>
        {
            var checker = File.ReadAllText(Path.Combine(ClientRoot(), "Zola.Client", "Identity", "DriftChecker.cs"));
            var app = File.ReadAllText(Path.Combine(ClientRoot(), "Zola.Client", "App.xaml.cs"));
            var log = File.ReadAllText(Path.Combine(ClientRoot(), "Zola.Client", "Identity", "IdentityLog.cs"));
            return checker.Contains("TryWritePackagesCapture", StringComparison.Ordinal)
                && checker.Contains("drift-pip-freeze-", StringComparison.Ordinal)
                && checker.Contains("_packagesCaptureWritten", StringComparison.Ordinal)
                && checker.Contains("PackagesCaptureFileName", StringComparison.Ordinal)
                && checker.Contains("UTF8Encoding(encoderShouldEmitUTF8Identifier: false)", StringComparison.Ordinal)
                && app.Contains("IdentityLog.DriftPackagesCapture", StringComparison.Ordinal)
                && log.Contains("drift packages_capture=", StringComparison.Ordinal)
                && IdentityLog.DriftPackagesCapture("x.txt") == "drift packages_capture=x.txt";
        });

        Identity("status write uses File.Move overwrite; SingleInstanceLock splits acquire then write", () =>
        {
            var status = File.ReadAllText(Path.Combine(ClientRoot(), "Zola.Client", "Identity", "InstanceStatusFile.cs"));
            var gate = File.ReadAllText(Path.Combine(ClientRoot(), "Zola.Client", "Identity", "SingleInstanceLock.cs"));
            var acquireSig = "public static SingleInstanceLock TryAcquire(string mutexName, string statusPath)";
            return status.Contains("File.Move(tmp, path, overwrite: true)", StringComparison.Ordinal)
                && !status.Contains("File.Copy", StringComparison.Ordinal)
                && gate.Contains(acquireSig, StringComparison.Ordinal)
                && gate.Contains("TryWriteStatus", StringComparison.Ordinal)
                && !gate.Contains("TryAcquire(string mutexName, string statusPath, BuildRoleInfo", StringComparison.Ordinal);
        });

        Identity("drift uses HermesLaunchResolver; no hard-coded hermes-agent path", () =>
        {
            var app = File.ReadAllText(Path.Combine(ClientRoot(), "Zola.Client", "App.xaml.cs"));
            return app.Contains("HermesLaunchResolver.TryResolve", StringComparison.Ordinal)
                && !app.Contains(@"C:\Users\test\Dev\hermes-agent", StringComparison.Ordinal)
                && app.Contains("hermes_root", StringComparison.Ordinal);
        });

        Identity("role: missing file is dev", () =>
        {
            var dir = NewIdentityTempDir();
            var r = BuildRole.Resolve(dir, "1.0.0+abc");
            return r.Role == IdentityConstants.RoleDev && r.Why == "missing";
        });

        Identity("role: valid stable when commit matches", () =>
        {
            var dir = NewIdentityTempDir();
            File.WriteAllText(Path.Combine(dir, IdentityConstants.RoleFileName),
                """{"role":"stable","tag":"fix-s51f","commit":"abc123","manifest":"stable-manifest.json"}""");
            var r = BuildRole.Resolve(dir, "1.0.0+abc123");
            return r.Role == IdentityConstants.RoleStable && r.Tag == "fix-s51f" && r.Why == "ok";
        });

        Identity("role: commit mismatch is dev", () =>
        {
            var dir = NewIdentityTempDir();
            File.WriteAllText(Path.Combine(dir, IdentityConstants.RoleFileName),
                """{"role":"stable","tag":"t","commit":"aaa","manifest":"stable-manifest.json"}""");
            var r = BuildRole.Resolve(dir, "1.0.0+bbb");
            return r.Role == IdentityConstants.RoleDev && r.Why == "commit_mismatch";
        });

        Identity("role: unreadable json is dev", () =>
        {
            var dir = NewIdentityTempDir();
            File.WriteAllText(Path.Combine(dir, IdentityConstants.RoleFileName), "{not-json");
            var r = BuildRole.Resolve(dir, "1.0.0+abc");
            return r.Role == IdentityConstants.RoleDev && r.Why == "unreadable";
        });

        Identity("refuse texts name stable, dev, and unknown", () =>
        {
            return RefuseMessages.ForHolder("stable", "fix-s51f").Contains("stable, fix-s51f")
                && RefuseMessages.ForHolder("dev", null).Contains("dev")
                && RefuseMessages.Unknown.Contains("Another Zola")
                && RefuseMessages.ForHolder("stable", "fix-s51f").Contains("Close it before starting another");
        });

        Identity("stale status is ignored when mutex is free (read helper)", () =>
        {
            var path = Path.Combine(NewIdentityTempDir(), "instance.json");
            InstanceStatusFile.WriteAtomic(path, new InstanceStatus("stable", "t", 1, "x", DateTimeOffset.Now.ToString("o")));
            var read = InstanceStatusFile.TryRead(path);
            InstanceStatusFile.TryDelete(path);
            return read is not null && !File.Exists(path);
        });

        Identity("drift notice posts once wording with components; no drift posts nothing", () =>
        {
            var none = DriftNotice.FromResult(new DriftCheckResult { Completed = true });
            var drift = DriftNotice.FromResult(new DriftCheckResult
            {
                Completed = true,
                HermesHeadDrift = true,
                PackagesDrift = true,
                PluginsDrift = true,
                PluginDriftFileCount = 2,
            });
            return !none.PostNotice
                && drift.PostNotice
                && drift.NoticeText.Contains("Hermes code")
                && drift.NoticeText.Contains("Python packages")
                && drift.NoticeText.Contains("plugins")
                && drift.LogComponents.Contains(IdentityConstants.ComponentHermesHead)
                && drift.PluginFileCount == 2;
        });

        Identity("drift incomplete and no-drift post nothing", () =>
        {
            var incomplete = DriftNotice.FromResult(DriftCheckResult.Incomplete("missing_rules"));
            var clean = DriftNotice.FromResult(new DriftCheckResult { Completed = true });
            return !incomplete.PostNotice && !clean.PostNotice;
        });

        Identity("digest empty UTF-8 matches known SHA-256", () =>
            HermesDigests.Sha256HexUtf8("") == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855");

        Identity("v2 digest changes when file content changes after already modified", () =>
        {
            var root = NewIdentityTempDir();
            RunGit(root, "init");
            RunGit(root, "config", "user.email", "t@t");
            RunGit(root, "config", "user.name", "t");
            var file = Path.Combine(root, "a.txt");
            File.WriteAllText(file, "one");
            RunGit(root, "add", "a.txt");
            RunGit(root, "commit", "-m", "c1");
            File.WriteAllText(file, "two");
            var git = HermesDigests.FindGit()!;
            var d1 = HermesDigests.LocalEditDigestV2(root, git);
            File.WriteAllText(file, "three");
            var d2 = HermesDigests.LocalEditDigestV2(root, git);
            return d1.Ok && d2.Ok && d1.Text != d2.Text;
        });

        Identity("v2 digest changes when untracked file content changes", () =>
        {
            var root = NewIdentityTempDir();
            RunGit(root, "init");
            var file = Path.Combine(root, "u.txt");
            File.WriteAllText(file, "a");
            var git = HermesDigests.FindGit()!;
            var d1 = HermesDigests.LocalEditDigestV2(root, git);
            File.WriteAllText(file, "b");
            var d2 = HermesDigests.LocalEditDigestV2(root, git);
            return d1.Ok && d2.Ok && d1.Text != d2.Text;
        });

        Identity("failing git is not completed (never empty hash as success)", () =>
        {
            var fake = Path.Combine(NewIdentityTempDir(), "git.bat");
            File.WriteAllText(fake, "@echo off\r\nexit /b 2\r\n");
            var cap = HermesDigests.LocalEditDigestV2(NewIdentityTempDir(), fake);
            return !cap.Ok && cap.Reason != null && cap.Reason.StartsWith("exit:");
        });

        Identity("v1 join strips trailing LF like proc1-stable array -join", () =>
        {
            var freezeFixture = "aiohttp==3.14.3\npypdf==6.19.0\nyarl==1.25.1";
            var porcelainFixture = " M tracked.py\n?? untracked.txt";
            var freezeHash = HermesDigests.Sha256HexUtf8(freezeFixture);
            var porcHash = HermesDigests.Sha256HexUtf8(porcelainFixture);
            return HermesDigests.JoinAsV1CommandOutput(freezeFixture + "\n") == freezeFixture
                && HermesDigests.JoinAsV1CommandOutput(porcelainFixture + "\r\n") == porcelainFixture
                && HermesDigests.Sha256HexUtf8(HermesDigests.JoinAsV1CommandOutput(freezeFixture + "\n")) == freezeHash
                && HermesDigests.Sha256HexUtf8(HermesDigests.JoinAsV1CommandOutput(porcelainFixture + "\n")) == porcHash;
        });

        Identity("v2 digest stable across two runs on one fixture", () =>
        {
            var root = NewIdentityTempDir();
            RunGit(root, "init");
            RunGit(root, "config", "user.email", "t@t");
            RunGit(root, "config", "user.name", "t");
            File.WriteAllText(Path.Combine(root, "a.txt"), "one");
            RunGit(root, "add", "a.txt");
            RunGit(root, "commit", "-m", "c1");
            File.WriteAllText(Path.Combine(root, "a.txt"), "two");
            File.WriteAllText(Path.Combine(root, "u.txt"), "untracked");
            var git = HermesDigests.FindGit()!;
            var d1 = HermesDigests.LocalEditDigestV2(root, git);
            var d2 = HermesDigests.LocalEditDigestV2(root, git);
            return d1.Ok && d2.Ok && d1.Text == d2.Text && d1.Text != HermesDigests.Sha256HexUtf8("");
        });

        Identity("package freeze diff names added removed changed", () =>
        {
            var promoted = DriftChecker.ParseFreezeMap("aiohttp==3.14.3\npypdf==6.19.0\nyarl==1.25.1\n");
            var live = DriftChecker.ParseFreezeMap("aiohttp==3.14.4\npypdf==6.19.0\nnewpkg==1.0.0\n");
            DriftChecker.DiffFreezeMaps(promoted, live, out var added, out var removed, out var changed);
            var line = IdentityLog.DriftPackagesDiff(added, removed, changed);
            return added.Count == 1 && added[0].StartsWith("newpkg==", StringComparison.Ordinal)
                && removed.Count == 1 && removed[0].StartsWith("yarl==", StringComparison.Ordinal)
                && changed.Count == 1 && changed[0].Contains("aiohttp==3.14.3->aiohttp==3.14.4", StringComparison.Ordinal)
                && line.Contains("added=", StringComparison.Ordinal)
                && line.Contains("removed=", StringComparison.Ordinal)
                && line.Contains("changed=", StringComparison.Ordinal)
                && DriftNotice.FromResult(new DriftCheckResult
                {
                    Completed = true,
                    PackagesDrift = true,
                    PackagesAdded = added,
                }).NoticeText.Contains("Python packages", StringComparison.Ordinal);
        });

        Identity("v1 pip-freeze manifest is unsupported_algorithm not drift", () =>
        {
            var dir = NewIdentityTempDir();
            var manifest = Path.Combine(dir, "stable-manifest.json");
            File.WriteAllText(manifest,
                """
                {"hermes_head":"x","hermes_local_edit_digest":"y","pip_freeze_digest":"z",
                "plugins_tag":{},"digest_algorithms":{"hermes_local_edit":"v2-content","pip_freeze":"v1-pip-freeze"},
                "plugin_compare_rules":{"maps":[],"named_excludes":[],"tts_rel":"zola-tts/deepgram_tts.py"}}
                """);
            var r = DriftChecker.Run(manifest, dir, dir, TimeSpan.FromSeconds(5));
            return !r.Completed
                && r.IncompleteReason == "unsupported_algorithm:v1-pip-freeze"
                && !r.PackagesDrift;
        });

        Identity("v2-pip-freeze-clean equal with and without PYTHONPATH", () =>
        {
            var hermes = @"C:\Users\test\Dev\hermes-agent";
            if (!File.Exists(Path.Combine(hermes, ".venv", "Scripts", "python.exe")))
            {
                return false;
            }

            var saved = Environment.GetEnvironmentVariable("PYTHONPATH");
            try
            {
                Environment.SetEnvironmentVariable("PYTHONPATH", hermes);
                var withPp = HermesDigests.PipFreezeDigest(hermes);
                Environment.SetEnvironmentVariable("PYTHONPATH", null);
                var withoutPp = HermesDigests.PipFreezeDigest(hermes);
                return withPp.Ok && withoutPp.Ok && withPp.Text == withoutPp.Text;
            }
            finally
            {
                Environment.SetEnvironmentVariable("PYTHONPATH", saved);
            }
        });

        Identity("v2-content equal with and without GIT_DIR", () =>
        {
            var root = NewIdentityTempDir();
            RunGit(root, "init");
            RunGit(root, "config", "user.email", "t@t");
            RunGit(root, "config", "user.name", "t");
            File.WriteAllText(Path.Combine(root, "a.txt"), "one");
            RunGit(root, "add", "a.txt");
            RunGit(root, "commit", "-m", "c1");
            File.WriteAllText(Path.Combine(root, "a.txt"), "two");
            var git = HermesDigests.FindGit()!;
            var saved = Environment.GetEnvironmentVariable("GIT_DIR");
            try
            {
                Environment.SetEnvironmentVariable("GIT_DIR", Path.Combine(NewIdentityTempDir(), "nope"));
                var withGit = HermesDigests.LocalEditDigestV2(root, git);
                Environment.SetEnvironmentVariable("GIT_DIR", null);
                var withoutGit = HermesDigests.LocalEditDigestV2(root, git);
                return withGit.Ok && withoutGit.Ok && withGit.Text == withoutGit.Text;
            }
            finally
            {
                Environment.SetEnvironmentVariable("GIT_DIR", saved);
            }
        });
    }

    private static string NewIdentityTempDir()
    {
        var p = Path.Combine(Path.GetTempPath(), "proc1-id-check-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(p);
        return p;
    }

    private static void RunGit(string root, params string[] args)
    {
        var git = HermesDigests.FindGit() ?? throw new InvalidOperationException("git missing");
        var all = new List<string> { "-C", root };
        all.AddRange(args);
        var cap = HermesDigests.Capture(git, all, 30000);
        if (!cap.Ok)
        {
            throw new InvalidOperationException(cap.Reason ?? "git failed");
        }
    }
}
