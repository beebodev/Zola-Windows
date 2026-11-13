using System.Diagnostics;
using Zola.Client;
using Zola.Client.Identity;

internal sealed partial class CheckRunner
{
    private void RunDevProfileRows()
    {
        Identity("dev refuse texts are eight distinct sentences, one per failure", () =>
        {
            var values = Enum.GetValues<DevProfileFailure>();
            if (values.Length != DevProfileRefuse.All.Count)
            {
                return false;
            }

            var seen = new HashSet<string>(StringComparer.Ordinal);
            var covered = new HashSet<DevProfileFailure>();
            foreach (var pair in DevProfileRefuse.All)
            {
                if (DevProfileRefuse.Text(pair.Failure) != pair.Text || !seen.Add(pair.Text))
                {
                    return false;
                }

                covered.Add(pair.Failure);
            }

            return seen.Count == values.Length
                && values.All(covered.Contains)
                && DevProfileRefuse.MissingFolder.EndsWith(@"Set it up with tools\dev\New-DevProfile.ps1.", StringComparison.Ordinal)
                && DevProfileRefuse.PhonePairingFiles.EndsWith("The dev profile contains phone pairing files.", StringComparison.Ordinal)
                && DevProfileRefuse.SettingsPointAtLive.EndsWith("Its settings point at the live profile.", StringComparison.Ordinal);
        });

        Identity("dev refuse sentences live only in DevProfileRefuse", () =>
        {
            var root = Path.Combine(ClientRoot(), "Zola.Client");
            var hits = new List<string>();
            foreach (var file in EnumerateClientSources(root))
            {
                if (File.ReadAllText(file).Contains("This dev build can't confirm", StringComparison.Ordinal))
                {
                    hits.Add(Path.GetFileName(file));
                }
            }

            return hits.Count == 1 && hits[0] == "DevProfileRefuse.cs";
        });

        Identity("path literals stay in ClientPaths, status file, and the mutex constant", () =>
        {
            var root = Path.Combine(ClientRoot(), "Zola.Client");
            var localAllowed = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
            {
                "ClientPaths.cs",
                "InstanceStatusFile.cs",
                "IdentityConstants.cs",
            };
            foreach (var file in EnumerateClientSources(root))
            {
                var name = Path.GetFileName(file);
                var text = File.ReadAllText(file);
                if (text.Contains("SpecialFolder.LocalApplicationData", StringComparison.Ordinal)
                    && !localAllowed.Contains(name))
                {
                    return false;
                }

                if (name.Equals("ClientPaths.cs", StringComparison.OrdinalIgnoreCase))
                {
                    continue;
                }

                if (text.Contains("\"zola\"", StringComparison.Ordinal)
                    || text.Contains("\"zola-dev\"", StringComparison.Ordinal))
                {
                    return false;
                }
            }

            return true;
        });

        Identity("startup order is lock, role, path plan, validation, then the first write", () =>
        {
            var app = File.ReadAllText(Path.Combine(ClientRoot(), "Zola.Client", "App.xaml.cs"));
            var order = new[]
            {
                "SingleInstanceLock.TryAcquire",
                "BuildRole.Resolve",
                "ClientPaths.ForRole",
                "DevProfileValidation.TryValidate",
                "DevProfileRefuse.Text",
                "ClientPaths.Install",
                "IdentityLog.RoleLine",
                "DumpPruner.PruneOnStartup",
                "new HermesProcessManager",
            };
            var at = -1;
            foreach (var token in order)
            {
                var next = app.IndexOf(token, StringComparison.Ordinal);
                if (next <= at)
                {
                    return false;
                }

                at = next;
            }

            var guard = app.IndexOf("if (!paths.IsDev)", StringComparison.Ordinal);
            var secret = app.IndexOf("PhoneLaunchSecret", StringComparison.Ordinal);
            var phone = app.IndexOf("new PhoneProcess", StringComparison.Ordinal);
            var start = app.IndexOf("_phone.Start()", StringComparison.Ordinal);
            return guard > 0 && guard < secret && secret < phone
                && app.Contains("if (_phone is not null)", StringComparison.Ordinal)
                && start > phone
                && app.Contains("ZOLA_DEEPGRAM_KEY_PATH", StringComparison.Ordinal) == false
                && File.ReadAllText(Path.Combine(ClientRoot(), "Zola.Client", "HermesProcessManager.cs"))
                    .Contains("ClientPaths.DeepgramEnvVar", StringComparison.Ordinal)
                && File.ReadAllText(Path.Combine(ClientRoot(), "Zola.Client", "Presence", "TtsPlaybackMonitor.cs"))
                    .Contains("ServeProfileMatcher.Classify", StringComparison.Ordinal);
        });

        Identity("stable path plan matches today's paths", () =>
        {
            var local = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            var paths = ClientPaths.ForRole(IdentityConstants.RoleStable, local);
            return paths.ProfileName == ClientPaths.ProfileStable
                && paths.ProfileDirectory == Path.Combine(local, "hermes", "profiles", "zola")
                && paths.ClientDataRoot == Path.Combine(local, "ZolaClient")
                && paths.LogsDirectory == Path.Combine(local, "ZolaClient", "logs")
                && paths.SupervisorLogPath == Path.Combine(local, "ZolaClient", "logs", "supervisor.log")
                && paths.ServeStderrPath == Path.Combine(local, "ZolaClient", "logs", "serve-stderr", "serve-stderr.log")
                && paths.VoiceTimelinePath == Path.Combine(local, "ZolaClient", "logs", "voice-timeline.log")
                && paths.DisplayStateLogPath == Path.Combine(local, "ZolaClient", "logs", "display-state.log")
                && paths.ToolEventsLogPath == Path.Combine(local, "ZolaClient", "logs", "tool-events.log")
                && paths.CodeReadLogPath == Path.Combine(local, "ZolaClient", "logs", "code-read.log")
                && paths.ProactiveLogPath == Path.Combine(local, "ZolaClient", "logs", "proactive.log")
                && paths.PresenceLogPath == Path.Combine(local, "ZolaClient", "logs", "presence.log")
                && paths.DriftCaptureDirectory == Path.Combine(local, "ZolaClient", "logs")
                && paths.DumpsDirectory == Path.Combine(local, "ZolaClient", "dumps")
                && paths.DebugDirectory == Path.Combine(local, "ZolaClient", "debug")
                && paths.WakeTokenPath == Path.Combine(local, "hermes", "profiles", "zola", ClientPaths.WakeModelRelativePath)
                && paths.WatcherOutputPath == Path.Combine(local, "hermes", "profiles", "zola", "logs", "zola_watcher.out.log")
                && paths.PhoneOutputPath == Path.Combine(local, "hermes", "profiles", "zola", "logs", "zola_phone.out.log")
                && paths.DeepgramKeyPath == Path.Combine(local, "ZolaClient", "secrets", "deepgram_api_key")
                && paths.HermesRootAuthPath == Path.Combine(local, "hermes", "auth.json")
                && InstanceStatusFile.DefaultPath == Path.Combine(local, "Zola", "run", "instance.json")
                && !paths.IsDev;
        });

        Identity("dev path plan keeps only the Deepgram key on a live root", () =>
        {
            var local = Path.Combine(Path.GetTempPath(), "proc1-dev-plan-" + Guid.NewGuid().ToString("N"));
            var paths = ClientPaths.ForRole(IdentityConstants.RoleDev, local);
            if (paths.ProfileName != ClientPaths.ProfileDev || !paths.IsDev)
            {
                return false;
            }

            foreach (var plan in paths.PlanPaths)
            {
                var live = paths.IsUnderLive(plan);
                if (ClientPaths.PathsEqual(plan, paths.DeepgramKeyPath))
                {
                    if (!live)
                    {
                        return false;
                    }

                    continue;
                }

                if (live || !paths.IsUnderDev(plan))
                {
                    return false;
                }
            }

            return !ClientPaths.IsUnder(paths.ProfileDirectory, paths.LiveProfileDirectory)
                && !ClientPaths.IsUnder(paths.ProfileDirectory, paths.NativeHermesRoot)
                && paths.ProfileDirectory == Path.Combine(local, "hermes-dev", "profiles", "zola-dev")
                && paths.ExpectedProfileDirectory == paths.ProfileDirectory
                && paths.HermesRootAuthPath == Path.Combine(local, "hermes-dev", "auth.json")
                && paths.DeepgramKeyPath == Path.Combine(local, "ZolaClient", "secrets", "deepgram_api_key")
                && InstanceStatusFile.DefaultPath.EndsWith(Path.Combine("Zola", "run", "instance.json"), StringComparison.OrdinalIgnoreCase);
        });

        Identity("missing dev folder maps to the setup sentence and writes nothing", () =>
            FailureLeavesRootsUnchanged(DevProfileFailure.MissingFolder, static (local, paths) => paths));

        Identity("a profile that is not zola-dev maps to that sentence", () =>
            FailureLeavesRootsUnchanged(DevProfileFailure.NotDevProfile, static (local, paths) =>
            {
                Directory.CreateDirectory(paths.LiveProfileDirectory);
                return paths.WithProfileDirectory(paths.LiveProfileDirectory);
            }));

        Identity("a dev profile under the native Hermes root refuses", () =>
            FailureLeavesRootsUnchanged(DevProfileFailure.NotDevProfile, static (local, paths) =>
            {
                var native = Path.Combine(paths.NativeHermesRoot, "profiles", ClientPaths.ProfileDev);
                Directory.CreateDirectory(native);
                return paths.WithProfileDirectory(native);
            }));

        Identity("a plan path on a live root maps to that sentence", () =>
            FailureLeavesRootsUnchanged(DevProfileFailure.PathPointsAtLive, static (local, paths) =>
            {
                Directory.CreateDirectory(paths.ProfileDirectory);
                return paths.WithExtraPlanPath(Path.Combine(paths.LiveProfileDirectory, "notes.txt"));
            }));

        Identity("a junction into the live profile maps to the link sentence", () =>
            FailureLeavesRootsUnchanged(DevProfileFailure.LinkIntoLive, static (local, paths) =>
            {
                var liveLogs = Path.Combine(paths.LiveProfileDirectory, "logs");
                Directory.CreateDirectory(liveLogs);
                Directory.CreateDirectory(paths.ProfileDirectory);
                var link = Path.Combine(paths.ProfileDirectory, "logs");
                MakeJunction(link, liveLogs);
                return paths;
            }));

        Identity("a phone plugin in the dev profile maps to that sentence", () =>
            FailureLeavesRootsUnchanged(DevProfileFailure.PhonePluginPresent, static (local, paths) =>
            {
                Directory.CreateDirectory(paths.PhonePluginDirectory);
                return paths;
            }));

        Identity("a file in pairing maps to the phone pairing sentence", () =>
            FailureLeavesRootsUnchanged(DevProfileFailure.PhonePairingFiles, static (local, paths) =>
            {
                var pairing = Path.Combine(paths.ProfileDirectory, "pairing");
                Directory.CreateDirectory(pairing);
                File.WriteAllText(Path.Combine(pairing, "device"), "x");
                return paths;
            }));

        Identity("a nested file in pairing maps to the phone pairing sentence", () =>
            FailureLeavesRootsUnchanged(DevProfileFailure.PhonePairingFiles, static (local, paths) =>
            {
                var nested = Path.Combine(paths.ProfileDirectory, "pairing", "nested");
                Directory.CreateDirectory(nested);
                File.WriteAllText(Path.Combine(nested, "device"), "x");
                return paths;
            }));

        Identity("a file in phone maps to the phone pairing sentence", () =>
            FailureLeavesRootsUnchanged(DevProfileFailure.PhonePairingFiles, static (local, paths) =>
            {
                var phone = Path.Combine(paths.ProfileDirectory, "phone");
                Directory.CreateDirectory(phone);
                File.WriteAllText(Path.Combine(phone, "device"), "x");
                return paths;
            }));

        Identity("no dev model credential while a root auth.json exists maps to that sentence and does not open the live auth file", () =>
        {
            var local = NewDevTemp();
            try
            {
                var paths = ClientPaths.ForRole(IdentityConstants.RoleDev, local);
                Directory.CreateDirectory(paths.ProfileDirectory);
                Directory.CreateDirectory(Path.GetDirectoryName(paths.HermesRootAuthPath)!);
                File.WriteAllText(paths.HermesRootAuthPath, "{\"credential_pool\":{}}");
                var liveAuth = Path.Combine(paths.LiveProfileDirectory, "auth.json");
                Directory.CreateDirectory(paths.LiveProfileDirectory);
                File.WriteAllText(liveAuth, "live-sentinel");
                var before = File.ReadAllBytes(liveAuth);
                var io = new RecordingDevIo(DevProfileIo.Real);
                var ok = DevProfileValidation.TryValidate(paths, io, out var failure, out var count);
                var after = File.ReadAllBytes(liveAuth);
                var openedLive = io.Reads.Concat(io.Exists).Concat(io.Directories)
                    .Any(path => path.Contains($"{Path.DirectorySeparatorChar}profiles{Path.DirectorySeparatorChar}zola{Path.DirectorySeparatorChar}", StringComparison.OrdinalIgnoreCase));
                var readRoot = io.Reads.Any(path => ClientPaths.PathsEqual(path, paths.HermesRootAuthPath));
                return !ok
                    && failure == DevProfileFailure.NoOwnModelCredential
                    && DevProfileRefuse.Text(failure) == DevProfileRefuse.NoOwnModelCredential
                    && count == 0
                    && !openedLive
                    && !readRoot
                    && before.AsSpan().SequenceEqual(after);
            }
            finally
            {
                DeleteDevTemp(local);
            }
        });

        Identity("a providers openai-codex object counts while a root auth.json exists", () =>
            DevCredentialWhileRootExists("{\"providers\":{\"openai-codex\":{}}}", expectOk: true, expectCount: 1));

        Identity("a credential_pool openai-codex row counts while a root auth.json exists", () =>
            DevCredentialWhileRootExists("{\"credential_pool\":{\"openai-codex\":[{}]}}", expectOk: true, expectCount: 1));

        Identity("providers and pool rows both count, and a null block does not", () =>
            DevCredentialWhileRootExists(
                "{\"providers\":{\"openai-codex\":{}},\"credential_pool\":{\"openai-codex\":[{},{}]}}",
                expectOk: true,
                expectCount: 3)
            && DevCredentialWhileRootExists(
                "{\"providers\":{\"openai-codex\":null},\"credential_pool\":{\"openai-codex\":[]}}",
                expectOk: false,
                expectCount: 0));

        Identity("empty pairing and phone folders still pass", () =>
        {
            var local = NewDevTemp();
            try
            {
                var paths = ClientPaths.ForRole(IdentityConstants.RoleDev, local);
                Directory.CreateDirectory(Path.Combine(paths.ProfileDirectory, "pairing", "nested"));
                Directory.CreateDirectory(Path.Combine(paths.ProfileDirectory, "phone"));
                return DevProfileValidation.TryValidate(paths, out _, out var count) && count == 0;
            }
            finally
            {
                DeleteDevTemp(local);
            }
        });

        Identity("settings that name the live profile map to that sentence", () =>
            FailureLeavesRootsUnchanged(DevProfileFailure.SettingsPointAtLive, static (local, paths) =>
            {
                Directory.CreateDirectory(paths.ProfileDirectory);
                File.WriteAllText(
                    paths.ConfigPath,
                    "tts:\n  command: " + Path.Combine(paths.LiveProfileDirectory, "zola-tts", "deepgram_tts.py") + "\n");
                return paths;
            }));

        Identity("a dev config that only names zola-dev passes, and zola does not match zola-dev", () =>
        {
            var local = NewDevTemp();
            try
            {
                var paths = ClientPaths.ForRole(IdentityConstants.RoleDev, local);
                Directory.CreateDirectory(paths.ProfileDirectory);
                File.WriteAllText(
                    paths.ConfigPath,
                    "plugins:\n  enabled: zola_tools,zola_workspace\n  command: "
                    + Path.Combine(paths.ExpectedProfileDirectory, "zola-tts", "deepgram_tts.py")
                    + "\n  client: " + Path.Combine(paths.ClientDataRoot, "logs") + "\n");
                var ok = DevProfileValidation.TryValidate(paths, out _, out var count);
                var devCmd = "python -m hermes_cli.main -p zola-dev serve --isolated --host 127.0.0.1 --port 0";
                var stableCmd = "python -m hermes_cli.main -p zola serve --isolated --host 127.0.0.1 --port 0";
                var devxCmd = "python -m hermes_cli.main -p zola-devx serve --isolated --host 127.0.0.1 --port 0";
                var profileEq = "python -m hermes_cli.main --profile=zola serve --isolated --host 127.0.0.1 --port 0";
                return ok
                    && count == 0
                    && ServeProfileMatcher.Classify(devCmd, ClientPaths.ProfileDev, out _) == ServeProfileMatch.ThisProfile
                    && ServeProfileMatcher.Classify(stableCmd, ClientPaths.ProfileDev, out var stableFlag) == ServeProfileMatch.OtherProfile
                    && stableFlag == "zola"
                    && ServeProfileMatcher.Classify(devxCmd, ClientPaths.ProfileDev, out var devxFlag) == ServeProfileMatch.OtherProfile
                    && devxFlag == "zola-devx"
                    && ServeProfileMatcher.Classify(profileEq, ClientPaths.ProfileDev, out var equalsFlag) == ServeProfileMatch.OtherProfile
                    && equalsFlag == "zola"
                    && ServeProfileMatcher.Classify(profileEq, ClientPaths.ProfileStable, out _) == ServeProfileMatch.ThisProfile
                    && ServeProfileMatcher.Classify(devCmd, ClientPaths.ProfileStable, out _) == ServeProfileMatch.OtherProfile
                    && !ServeProfileMatcher.IsDedicatedServe(stableCmd, ClientPaths.ProfileDev)
                    && !ServeProfileMatcher.IsDedicatedServe(devxCmd, ClientPaths.ProfileDev)
                    && !ServeProfileMatcher.IsDedicatedServe(devCmd, ClientPaths.ProfileStable)
                    && !ServeProfileMatcher.IsDedicatedServe(profileEq, ClientPaths.ProfileDev)
                    && ServeProfileMatcher.IsDedicatedServe(profileEq, ClientPaths.ProfileStable);
            }
            finally
            {
                DeleteDevTemp(local);
            }
        });

        Identity("other-profile log is one line of fields and is not written before a path plan", () =>
        {
            var local = NewDevTemp();
            try
            {
                OtherProfileLog.ResetForTests();
                OtherProfileLog.Once(9, "zola");
                var paths = ClientPaths.ForRole(IdentityConstants.RoleDev, local);
                if (File.Exists(paths.SupervisorLogPath))
                {
                    return false;
                }

                Directory.CreateDirectory(paths.LogsDirectory);
                ClientPaths.Install(paths);
                OtherProfileLog.ResetForTests();
                OtherProfileLog.Once(42, "zola");
                OtherProfileLog.Once(42, "zola-dev");
                OtherProfileLog.Once(43, "not a flag");
                var log = File.ReadAllText(paths.SupervisorLogPath);
                return log.Contains("other_profile pid=42 profile=zola action=ignored", StringComparison.Ordinal)
                    && !log.Contains("pid=42 profile=zola-dev", StringComparison.Ordinal)
                    && log.Contains("other_profile pid=43 profile=unknown action=ignored", StringComparison.Ordinal)
                    && !log.Contains("serve --isolated", StringComparison.Ordinal);
            }
            finally
            {
                ClientPaths.ResetForTests();
                DeleteDevTemp(local);
            }
        });

        Identity("the other profile is not attached or killed", () =>
        {
            var client = Path.Combine(ClientRoot(), "Zola.Client");
            if (File.Exists(Path.Combine(client, "ProcessEnvironmentReader.cs")))
            {
                return false;
            }

            foreach (var file in EnumerateClientSources(client))
            {
                if (File.ReadAllText(file).Contains("ProcessEnvironmentReader", StringComparison.Ordinal))
                {
                    return false;
                }
            }

            var manager = File.ReadAllText(Path.Combine(client, "HermesProcessManager.cs"));
            var accept = manager.IndexOf("ServeProfileMatcher.Classify(commandLine, _paths.ProfileName, out var flag)", StringComparison.Ordinal);
            var other = manager.IndexOf("ServeProfileMatch.OtherProfile", accept, StringComparison.Ordinal);
            var logged = manager.IndexOf("OtherProfileLog.Once(pid, flag)", other, StringComparison.Ordinal);
            var refused = manager.IndexOf("return false", logged, StringComparison.Ordinal);
            var mine = manager.IndexOf("return match == ServeProfileMatch.ThisProfile", refused, StringComparison.Ordinal);
            var supervision = File.ReadAllText(Path.Combine(client, "HermesProcessManager.Supervision.cs"));
            var gate = supervision.IndexOf("if (!AcceptServe(commandLine, pid))", StringComparison.Ordinal);
            var added = supervision.IndexOf("pids.Add(pid)", gate, StringComparison.Ordinal);
            var killList = supervision.IndexOf("foreach (var pid in FindDedicatedServePids())", StringComparison.Ordinal);
            var kill = supervision.IndexOf("TryKillPid(pid)", killList, StringComparison.Ordinal);
            var playback = File.ReadAllText(Path.Combine(client, "Presence", "TtsPlaybackMonitor.cs"));
            var playOther = playback.IndexOf("ServeProfileMatch.OtherProfile", StringComparison.Ordinal);
            var playSkip = playback.IndexOf("continue", playOther, StringComparison.Ordinal);
            var playMine = playback.IndexOf("ServeProfileMatch.ThisProfile", playSkip, StringComparison.Ordinal);
            var playReturn = playback.IndexOf("return pid", playMine, StringComparison.Ordinal);
            var acceptBody = accept >= 0 && mine > accept ? manager.Substring(accept, mine - accept) : "";
            return accept > 0 && other > accept && logged > other && refused > logged && mine > refused
                && gate > 0 && added > gate
                && killList > 0 && kill > killList
                && playOther > 0 && playSkip > playOther && playMine > playSkip && playReturn > playMine
                && !acceptBody.Contains("HERMES_HOME", StringComparison.Ordinal);
        });

        Identity("a dev config that names the shared Deepgram key still passes", () =>
        {
            var local = NewDevTemp();
            try
            {
                var paths = ClientPaths.ForRole(IdentityConstants.RoleDev, local);
                Directory.CreateDirectory(paths.ProfileDirectory);
                File.WriteAllText(
                    paths.ConfigPath,
                    "key: " + paths.DeepgramKeyPath + "\ncommand: "
                    + Path.Combine(paths.ExpectedProfileDirectory, "zola-tts", "deepgram_tts.py") + "\n");
                var ok = DevProfileValidation.TryValidate(paths, out _, out var count);
                File.WriteAllText(
                    paths.ConfigPath,
                    "logs: " + Path.Combine(paths.LiveClientDataRoot, "logs") + "\n");
                var liveLogs = !DevProfileValidation.TryValidate(paths, out var failure, out _);
                return ok && count == 0 && liveLogs && failure == DevProfileFailure.SettingsPointAtLive;
            }
            finally
            {
                DeleteDevTemp(local);
            }
        });

        Identity("google store path is only under HERMES_HOME", () =>
        {
            var auth = File.ReadAllText(Path.Combine(RepoRoot(), "hermes-plugins", "zola_workspace", "auth.py"));
            var store = auth.IndexOf("def store_path()", StringComparison.Ordinal);
            var dir = auth.IndexOf("def _store_dir()", StringComparison.Ordinal);
            return store > 0 && dir > 0
                && auth.Contains("return get_hermes_home() / STORE_DIR_NAME", StringComparison.Ordinal)
                && auth.Contains("return _store_dir() / TOKEN_FILENAME", StringComparison.Ordinal)
                && auth.Contains("TOKEN_FILENAME = \"token.dpapi\"", StringComparison.Ordinal)
                && !auth.Contains("profiles\\zola", StringComparison.Ordinal)
                && !auth.Contains("profiles/zola", StringComparison.Ordinal);
        });

        Identity("phone reads, pairing, and code redeem require the launch secret", () =>
        {
            var runtime = File.ReadAllText(Path.Combine(RepoRoot(), "hermes-plugins", "zola_phone", "runtime.py"));
            var secret = runtime.IndexOf("def _secret_ok", StringComparison.Ordinal);
            var request = runtime.IndexOf("def local_request", StringComparison.Ordinal);
            return secret > 0 && request > secret
                && runtime.Contains("reason=\"unauthorized\"", StringComparison.Ordinal)
                && runtime.Contains("\"reason\": \"unauthorized\"", StringComparison.Ordinal);
        });
    }

    private static bool DevCredentialWhileRootExists(string authJson, bool expectOk, int expectCount)
    {
        var local = NewDevTemp();
        try
        {
            var paths = ClientPaths.ForRole(IdentityConstants.RoleDev, local);
            Directory.CreateDirectory(paths.ProfileDirectory);
            Directory.CreateDirectory(Path.GetDirectoryName(paths.HermesRootAuthPath)!);
            File.WriteAllText(paths.HermesRootAuthPath, "{\"credential_pool\":{}}");
            File.WriteAllText(paths.DevAuthPath, authJson);
            var liveAuth = Path.Combine(paths.LiveProfileDirectory, "auth.json");
            Directory.CreateDirectory(paths.LiveProfileDirectory);
            File.WriteAllText(liveAuth, "live-sentinel");
            var before = File.ReadAllBytes(liveAuth);
            var io = new RecordingDevIo(DevProfileIo.Real);
            var ok = DevProfileValidation.TryValidate(paths, io, out var failure, out var count);
            var after = File.ReadAllBytes(liveAuth);
            var openedLive = io.Reads.Concat(io.Exists).Concat(io.Directories)
                .Any(path => path.Contains($"{Path.DirectorySeparatorChar}profiles{Path.DirectorySeparatorChar}zola{Path.DirectorySeparatorChar}", StringComparison.OrdinalIgnoreCase));
            var readRoot = io.Reads.Any(path => ClientPaths.PathsEqual(path, paths.HermesRootAuthPath));
            if (openedLive || readRoot || !before.AsSpan().SequenceEqual(after) || count != expectCount)
            {
                return false;
            }

            return expectOk
                ? ok
                : !ok
                    && failure == DevProfileFailure.NoOwnModelCredential
                    && DevProfileRefuse.Text(failure) == DevProfileRefuse.NoOwnModelCredential;
        }
        finally
        {
            DeleteDevTemp(local);
        }
    }

    private static bool FailureLeavesRootsUnchanged(
        DevProfileFailure expected,
        Func<string, ClientPaths, ClientPaths> arrange)
    {
        var local = NewDevTemp();
        try
        {
            var paths = arrange(local, ClientPaths.ForRole(IdentityConstants.RoleDev, local));
            var before = SnapshotTree(local);
            var ok = DevProfileValidation.TryValidate(paths, out var failure, out _);
            var after = SnapshotTree(local);
            return !ok
                && failure == expected
                && DevProfileRefuse.Text(failure) == DevProfileRefuse.Text(expected)
                && before.SequenceEqual(after);
        }
        finally
        {
            DeleteDevTemp(local);
        }
    }

    private static List<string> SnapshotTree(string root)
    {
        var list = new List<string>();
        if (!Directory.Exists(root))
        {
            return list;
        }

        foreach (var file in Directory.EnumerateFileSystemEntries(root, "*", SearchOption.AllDirectories))
        {
            var info = new FileInfo(file);
            var kind = info.Attributes.HasFlag(FileAttributes.Directory) ? "d" : "f";
            list.Add(kind + "|" + Path.GetRelativePath(root, file));
        }

        list.Sort(StringComparer.OrdinalIgnoreCase);
        return list;
    }

    private static string NewDevTemp()
    {
        var path = Path.Combine(Path.GetTempPath(), "proc1-dev-check-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(path);
        return path;
    }

    private static void DeleteDevTemp(string root)
    {
        if (!Directory.Exists(root))
        {
            return;
        }

        foreach (var dir in Directory.EnumerateDirectories(root, "*", SearchOption.AllDirectories).OrderByDescending(path => path.Length))
        {
            var info = new DirectoryInfo(dir);
            if (info.Attributes.HasFlag(FileAttributes.ReparsePoint))
            {
                info.Delete();
            }
        }

        Directory.Delete(root, recursive: true);
    }

    private static void MakeJunction(string link, string target)
    {
        var start = new ProcessStartInfo(
            "cmd.exe",
            "/c mklink /J \"" + link + "\" \"" + target + "\"")
        {
            CreateNoWindow = true,
            UseShellExecute = false,
            RedirectStandardError = true,
            RedirectStandardOutput = true,
        };
        using var process = Process.Start(start) ?? throw new InvalidOperationException("mklink did not start");
        process.WaitForExit(10000);
        if (process.ExitCode != 0)
        {
            throw new InvalidOperationException(process.StandardError.ReadToEnd());
        }
    }

    private static string RepoRoot() => Path.GetFullPath(Path.Combine(ClientRoot(), ".."));

    private static IEnumerable<string> EnumerateClientSources(string root)
    {
        foreach (var file in Directory.EnumerateFiles(root, "*.cs", SearchOption.AllDirectories))
        {
            var sep = Path.DirectorySeparatorChar;
            if (file.Contains($"{sep}bin{sep}", StringComparison.OrdinalIgnoreCase)
                || file.Contains($"{sep}obj{sep}", StringComparison.OrdinalIgnoreCase))
            {
                continue;
            }

            yield return file;
        }
    }
}

internal sealed class RecordingDevIo : IDevProfileIo
{
    private readonly IDevProfileIo _inner;

    public RecordingDevIo(IDevProfileIo inner) => _inner = inner;

    public List<string> Reads { get; } = new();

    public List<string> Exists { get; } = new();

    public List<string> Directories { get; } = new();

    public bool DirectoryExists(string path)
    {
        Directories.Add(path);
        return _inner.DirectoryExists(path);
    }

    public bool FileExists(string path)
    {
        Exists.Add(path);
        return _inner.FileExists(path);
    }

    public string? ReadAllText(string path)
    {
        Reads.Add(path);
        return _inner.ReadAllText(path);
    }

    public string? LinkTarget(string path) => _inner.LinkTarget(path);

    public bool ContainsAnyFile(string directory) => _inner.ContainsAnyFile(directory);
}
