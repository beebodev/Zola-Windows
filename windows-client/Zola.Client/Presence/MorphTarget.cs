namespace Zola.Client.Presence;

internal static class MorphTargets
{
    internal const int MorphTargetCount = 15;
}

// P3-RENDER: K3 index order; names are not imported — P3-D02
internal enum MorphTarget
{
    BlinkLeft = 0,
    BlinkRight = 1,
    BlinkBoth = 2,
    SquintEyes = 3,
    WideAlertEyes = 4,
    BrowRaise = 5,
    BrowFurrow = 6,
    NostrilFlare = 7,
    JawOpen = 8,
    OpenAH = 9,
    MidOpenEhUh = 10,
    ClosedMBP = 11,
    RoundOOW = 12,
    WideEE = 13,
    TeethFV = 14,
}
