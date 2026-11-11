using System.Threading;

namespace Zola.Client.Identity;

// PROC1-ID: one Zola per Windows session (Local\ mutex) — PROC1-D7
public sealed class SingleInstanceLock : IDisposable
{
    private readonly Mutex _mutex;
    private readonly string _statusPath;
    private bool _owned;

    private SingleInstanceLock(Mutex mutex, string statusPath, bool owned)
    {
        _mutex = mutex;
        _statusPath = statusPath;
        _owned = owned;
    }

    public bool Owned => _owned;

    public string StatusPath => _statusPath;

    // PROC1-ID: acquire only; status is written after BuildRole once the lock is owned — PROC1-D7
    public static SingleInstanceLock TryAcquire(string mutexName, string statusPath)
    {
        var mutex = new Mutex(initiallyOwned: false, mutexName, out _);
        var owned = false;
        try
        {
            owned = mutex.WaitOne(0);
        }
        catch (AbandonedMutexException)
        {
            // PROC1-ID: crashed holder — reclaim, do not refuse — PROC1-D7
            owned = true;
        }

        return new SingleInstanceLock(mutex, statusPath, owned);
    }

    public bool TryWriteStatus(BuildRoleInfo role, string exePath, out string? failReason)
    {
        failReason = null;
        if (!_owned)
        {
            failReason = "not_owned";
            return false;
        }

        try
        {
            var status = new InstanceStatus(
                role.Role,
                role.Tag,
                Environment.ProcessId,
                exePath,
                DateTimeOffset.Now.ToString("o"));
            InstanceStatusFile.WriteAtomic(_statusPath, status);
            return true;
        }
        catch (Exception ex)
        {
            failReason = ex.GetType().Name;
            return false;
        }
    }

    public InstanceStatus? ReadHolderStatus() => InstanceStatusFile.TryRead(_statusPath);

    public void Dispose()
    {
        if (_owned)
        {
            InstanceStatusFile.TryDelete(_statusPath);
            try
            {
                _mutex.ReleaseMutex();
            }
            catch
            {
            }

            _owned = false;
        }

        _mutex.Dispose();
    }
}
