namespace Zola.Client.Supervision;

// P9-SUPERVISE: stderr is written only after both icacls calls exit 0 — P9-D02
public readonly record struct StderrAclDecision(bool MayWrite, bool Applied, bool LogFailure);

public static class StderrAcl
{
    public static StderrAclDecision Evaluate(bool alreadyApplied, bool failureLogged, int? inheritanceExit, int? grantExit)
    {
        if (alreadyApplied)
        {
            return new StderrAclDecision(MayWrite: true, Applied: true, LogFailure: false);
        }

        if (inheritanceExit == 0 && grantExit == 0)
        {
            return new StderrAclDecision(MayWrite: true, Applied: true, LogFailure: false);
        }

        return new StderrAclDecision(MayWrite: false, Applied: false, LogFailure: !failureLogged);
    }
}
