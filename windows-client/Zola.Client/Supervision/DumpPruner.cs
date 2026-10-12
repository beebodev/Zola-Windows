namespace Zola.Client;

// P9-SUPERVISE: the client deletes dump files older than DumpRetentionDays; it does not follow junctions — P9-D02
public static class DumpPruner
{
    public static void PruneOnStartup()
    {
        try
        {
            var folder = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "ZolaClient",
                "dumps");
            var dir = new DirectoryInfo(folder);
            if (!dir.Exists || dir.Attributes.HasFlag(FileAttributes.ReparsePoint))
            {
                return;
            }

            var now = DateTimeOffset.UtcNow;
            foreach (var file in dir.EnumerateFiles())
            {
                if (file.Attributes.HasFlag(FileAttributes.ReparsePoint))
                {
                    continue;
                }

                if (Supervision.SupervisionConstants.RetentionExpired(
                        file.LastWriteTimeUtc,
                        now,
                        Supervision.SupervisionConstants.DumpRetentionDays))
                {
                    file.Delete();
                }
            }
        }
        catch
        {
        }
    }
}
