namespace Zola.Client.Identity;

// PROC1-DEV: one fixed sentence per dev-start refusal — PROC1-D4 / PROC1-D5
public enum DevProfileFailure
{
    MissingFolder,
    NotDevProfile,
    PathPointsAtLive,
    LinkIntoLive,
    PhonePluginPresent,
    PhonePairingFiles,
    NoOwnModelCredential,
    SettingsPointAtLive,
}

public static class DevProfileRefuse
{
    public const string MissingFolder =
        @"This dev build can't confirm it's using the dev profile, so it won't start. The zola-dev folder is missing. Set it up with tools\dev\New-DevProfile.ps1.";

    public const string NotDevProfile =
        "This dev build can't confirm it's using the dev profile, so it won't start. The profile is not zola-dev.";

    public const string PathPointsAtLive =
        "This dev build can't confirm it's using the dev profile, so it won't start. A path points at the live profile or ZolaClient.";

    public const string LinkIntoLive =
        "This dev build can't confirm it's using the dev profile, so it won't start. A path is a link into the live profile or ZolaClient.";

    public const string PhonePluginPresent =
        "This dev build can't confirm it's using the dev profile, so it won't start. The dev profile contains the phone plugin.";

    public const string PhonePairingFiles =
        "This dev build can't confirm it's using the dev profile, so it won't start. The dev profile contains phone pairing files.";

    public const string NoOwnModelCredential =
        "This dev build can't confirm it's using the dev profile, so it won't start. Dev has no model sign-in of its own, and a shared Hermes sign-in is present.";

    public const string SettingsPointAtLive =
        "This dev build can't confirm it's using the dev profile, so it won't start. Its settings point at the live profile.";

    public static string Text(DevProfileFailure failure) => failure switch
    {
        DevProfileFailure.MissingFolder => MissingFolder,
        DevProfileFailure.NotDevProfile => NotDevProfile,
        DevProfileFailure.PathPointsAtLive => PathPointsAtLive,
        DevProfileFailure.LinkIntoLive => LinkIntoLive,
        DevProfileFailure.PhonePluginPresent => PhonePluginPresent,
        DevProfileFailure.PhonePairingFiles => PhonePairingFiles,
        DevProfileFailure.NoOwnModelCredential => NoOwnModelCredential,
        DevProfileFailure.SettingsPointAtLive => SettingsPointAtLive,
        _ => throw new ArgumentOutOfRangeException(nameof(failure)),
    };

    public static IReadOnlyList<(DevProfileFailure Failure, string Text)> All { get; } = new (DevProfileFailure, string)[]
    {
        (DevProfileFailure.MissingFolder, MissingFolder),
        (DevProfileFailure.NotDevProfile, NotDevProfile),
        (DevProfileFailure.PathPointsAtLive, PathPointsAtLive),
        (DevProfileFailure.LinkIntoLive, LinkIntoLive),
        (DevProfileFailure.PhonePluginPresent, PhonePluginPresent),
        (DevProfileFailure.PhonePairingFiles, PhonePairingFiles),
        (DevProfileFailure.NoOwnModelCredential, NoOwnModelCredential),
        (DevProfileFailure.SettingsPointAtLive, SettingsPointAtLive),
    };
}
