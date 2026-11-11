namespace Zola.Client.Identity;

// PROC1-ID: refusal pop-up wording (Brian + Claude) — PROC1-D7
public static class RefuseMessages
{
    public static string ForHolder(string? role, string? tag)
    {
        if (string.Equals(role, IdentityConstants.RoleStable, StringComparison.Ordinal)
            && !string.IsNullOrWhiteSpace(tag))
        {
            return string.Format(IdentityConstants.RefuseStableFormat, tag);
        }

        if (string.Equals(role, IdentityConstants.RoleDev, StringComparison.Ordinal)
            || string.Equals(role, IdentityConstants.RoleStable, StringComparison.Ordinal))
        {
            return IdentityConstants.RefuseDevText;
        }

        return IdentityConstants.RefuseUnknownText;
    }

    public static string Unknown => IdentityConstants.RefuseUnknownText;
}
