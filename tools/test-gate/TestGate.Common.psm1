# PROC1-GATE shared helpers - PowerShell 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Expand-GatePath {
    param([Parameter(Mandatory)][string]$Path)
    return [Environment]::ExpandEnvironmentVariables($Path)
}

function Get-HermesRoot {
    $root = [Environment]::GetEnvironmentVariable('ZOLA_HERMES_ROOT', 'User')
    if ([string]::IsNullOrWhiteSpace($root)) { return $null }
    return $root.TrimEnd('\')
}

function Get-HermesPython {
    param([Parameter(Mandatory)][string]$HermesRoot)
    return (Join-Path $HermesRoot '.venv\Scripts\python.exe')
}

function Get-CommitRecord {
    param([Parameter(Mandatory)][string]$RepoRoot)
    Push-Location $RepoRoot
    try {
        $head = ("$(git rev-parse HEAD 2>$null)").Trim()
        $branch = ("$(git rev-parse --abbrev-ref HEAD 2>$null)").Trim()
        $porcelain = @(git status --porcelain 2>$null)
        if (-not $porcelain) { $porcelain = @() }
        return [ordered]@{
            head               = $head
            branch             = $branch
            porcelain          = @($porcelain)
            dirty              = ($porcelain.Count -gt 0)
            hermes_agent_head  = ''
            hermes_agent_dirty = $false
        }
    } finally {
        Pop-Location
    }
}

function Add-HermesRecord {
    param($Record, [string]$HermesRoot)
    if ([string]::IsNullOrWhiteSpace($HermesRoot) -or -not (Test-Path -LiteralPath $HermesRoot)) {
        $Record.hermes_agent_head = ''
        $Record.hermes_agent_dirty = $false
        return
    }
    Push-Location $HermesRoot
    try {
        $Record.hermes_agent_head = ("$(git rev-parse HEAD 2>$null)").Trim()
        $porc = @(git status --porcelain 2>$null)
        $Record.hermes_agent_dirty = ($porc.Count -gt 0)
    } finally {
        Pop-Location
    }
}

function Test-MutexHeld {
    param([Parameter(Mandatory)][string]$Name)
    try {
        $opened = [System.Threading.Mutex]::OpenExisting($Name)
        $opened.Dispose()
        return $true
    } catch [System.Threading.WaitHandleCannotBeOpenedException] {
        return $false
    } catch [System.UnauthorizedAccessException] {
        return $true
    } catch {
        return $true
    }
}

function Test-ZolaRunningForGate {
    param([string]$DetailOut = '')
    $client = Test-MutexHeld -Name 'Local\ZolaClient'
    $phone = Test-MutexHeld -Name 'Local\ZolaPhone'
    if ($DetailOut) {
        if ($client -and $phone) { return 'both' }
        if ($client) { return 'client' }
        if ($phone) { return 'phone' }
        return 'none'
    }
    return ($client -or $phone)
}

function Get-ZolaRunningInfraReason {
    $client = Test-MutexHeld -Name 'Local\ZolaClient'
    $phone = Test-MutexHeld -Name 'Local\ZolaPhone'
    if ($client) { return 'stable Zola is running; close Zola for a clean run' }
    if ($phone) { return 'a zola-phone process is running; close Zola for a clean run' }
    return 'stable is running; close Zola for a clean run'
}

function New-ClearedSuiteEnvironment {
    param(
        [Parameter(Mandatory)]$SuiteDef,
        [hashtable]$Extra = @{}
    )
    $envMap = @{}
    foreach ($entry in [System.Environment]::GetEnvironmentVariables('Process').GetEnumerator()) {
        $envMap[$entry.Key] = [string]$entry.Value
    }
    $clear = @('PYTHONPATH', 'PYTHONHOME', 'VIRTUAL_ENV', 'HERMES_HOME', 'PIP_INDEX_URL', 'PIP_EXTRA_INDEX_URL', 'PIP_REQUIRE_VIRTUALENV', 'PIP_TARGET', 'PIP_FIND_LINKS')
    if ($SuiteDef.ClearEnvNames) { $clear = @($SuiteDef.ClearEnvNames) }
    foreach ($name in $clear) {
        if ($envMap.ContainsKey($name)) { $envMap.Remove($name) }
    }
    foreach ($k in $Extra.Keys) {
        $envMap[$k] = [string]$Extra[$k]
    }
    return $envMap
}

# --- Native: job object + CREATE_SUSPENDED ---
$script:GateNativeSrc = @"
using System;
using System.Runtime.InteropServices;
using System.Text;

public static class GateNative {
  public const uint CREATE_SUSPENDED = 0x00000004;
  public const uint CREATE_UNICODE_ENVIRONMENT = 0x00000400;
  public const uint CREATE_BREAKAWAY_FROM_JOB = 0x01000000;
  public const uint JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000;
  public const int JobObjectExtendedLimitInformation = 9;
  public const int JobObjectBasicProcessIdList = 3;

  [StructLayout(LayoutKind.Sequential)]
  public struct STARTUPINFO {
    public int cb;
    public IntPtr lpReserved, lpDesktop, lpTitle;
    public int dwX, dwY, dwXSize, dwYSize, dwXCountChars, dwYCountChars, dwFillAttribute, dwFlags;
    public short wShowWindow, cbReserved2;
    public IntPtr lpReserved2, hStdInput, hStdOutput, hStdError;
  }
  [StructLayout(LayoutKind.Sequential)]
  public struct PROCESS_INFORMATION {
    public IntPtr hProcess, hThread;
    public int dwProcessId, dwThreadId;
  }
  [StructLayout(LayoutKind.Sequential)]
  public struct SECURITY_ATTRIBUTES {
    public int nLength;
    public IntPtr lpSecurityDescriptor;
    public int bInheritHandle;
  }
  [StructLayout(LayoutKind.Sequential)]
  public struct JOBOBJECT_BASIC_LIMIT_INFORMATION {
    public long PerProcessUserTimeLimit, PerJobUserTimeLimit;
    public uint LimitFlags;
    public UIntPtr MinimumWorkingSetSize, MaximumWorkingSetSize;
    public uint ActiveProcessLimit;
    public UIntPtr Affinity;
    public uint PriorityClass, SchedulingClass;
  }
  [StructLayout(LayoutKind.Sequential)]
  public struct IO_COUNTERS {
    public ulong ReadOperationCount, WriteOperationCount, OtherOperationCount;
    public ulong ReadTransferCount, WriteTransferCount, OtherTransferCount;
  }
  [StructLayout(LayoutKind.Sequential)]
  public struct JOBOBJECT_EXTENDED_LIMIT_INFORMATION {
    public JOBOBJECT_BASIC_LIMIT_INFORMATION BasicLimitInformation;
    public IO_COUNTERS IoInfo;
    public UIntPtr ProcessMemoryLimit, JobMemoryLimit, PeakProcessMemoryUsed, PeakJobMemoryUsed;
  }

  [DllImport("kernel32.dll", SetLastError=true, CharSet=CharSet.Unicode)]
  public static extern bool CreateProcess(string lpApplicationName, string lpCommandLine,
    IntPtr lpProcessAttributes, IntPtr lpThreadAttributes, bool bInheritHandles,
    uint dwCreationFlags, IntPtr lpEnvironment, string lpCurrentDirectory,
    ref STARTUPINFO lpStartupInfo, out PROCESS_INFORMATION lpProcessInformation);

  [DllImport("kernel32.dll", SetLastError=true)] public static extern uint ResumeThread(IntPtr hThread);
  [DllImport("kernel32.dll", SetLastError=true)] public static extern bool CloseHandle(IntPtr h);
  [DllImport("kernel32.dll", SetLastError=true, CharSet=CharSet.Unicode)]
  public static extern IntPtr CreateJobObject(IntPtr a, string n);
  [DllImport("kernel32.dll", SetLastError=true)]
  public static extern bool AssignProcessToJobObject(IntPtr job, IntPtr proc);
  [DllImport("kernel32.dll", SetLastError=true)]
  public static extern bool TerminateJobObject(IntPtr job, uint code);
  [DllImport("kernel32.dll", SetLastError=true)]
  public static extern bool SetInformationJobObject(IntPtr job, int cls, IntPtr info, uint len);
  [DllImport("kernel32.dll", SetLastError=true)]
  public static extern bool QueryInformationJobObject(IntPtr job, int cls, IntPtr info, uint len, IntPtr ret);
  [DllImport("kernel32.dll", SetLastError=true)]
  public static extern bool GetExitCodeProcess(IntPtr h, out uint code);
  [DllImport("kernel32.dll", SetLastError=true)]
  public static extern uint WaitForSingleObject(IntPtr h, uint ms);
  [DllImport("kernel32.dll", SetLastError=true)]
  public static extern bool TerminateProcess(IntPtr h, uint code);

  public static IntPtr CreateKillOnCloseJob() {
    IntPtr job = CreateJobObject(IntPtr.Zero, null);
    if (job == IntPtr.Zero) return IntPtr.Zero;
    var info = new JOBOBJECT_EXTENDED_LIMIT_INFORMATION();
    info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
    int len = Marshal.SizeOf(typeof(JOBOBJECT_EXTENDED_LIMIT_INFORMATION));
    IntPtr ptr = Marshal.AllocHGlobal(len);
    try {
      Marshal.StructureToPtr(info, ptr, false);
      if (!SetInformationJobObject(job, JobObjectExtendedLimitInformation, ptr, (uint)len)) {
        CloseHandle(job); return IntPtr.Zero;
      }
    } finally { Marshal.FreeHGlobal(ptr); }
    return job;
  }

  public static IntPtr BuildEnvironmentBlock(string[] entries) {
    // UTF-16 null-separated, double-null terminated
    var sb = new StringBuilder();
    foreach (var e in entries) { sb.Append(e); sb.Append('\0'); }
    sb.Append('\0');
    byte[] bytes = Encoding.Unicode.GetBytes(sb.ToString());
    IntPtr p = Marshal.AllocHGlobal(bytes.Length);
    Marshal.Copy(bytes, 0, p, bytes.Length);
    return p;
  }

  public static int[] QueryJobPids(IntPtr job) {
    // Buffer: two DWORDs + up to 256 ULONG_PTR
    int capacity = 256;
    int size = 8 + IntPtr.Size * capacity;
    IntPtr buf = Marshal.AllocHGlobal(size);
    try {
      for (int i = 0; i < size; i++) Marshal.WriteByte(buf, i, 0);
      if (!QueryInformationJobObject(job, JobObjectBasicProcessIdList, buf, (uint)size, IntPtr.Zero)) {
        return new int[0];
      }
      int assigned = Marshal.ReadInt32(buf, 0);
      int inList = Marshal.ReadInt32(buf, 4);
      int n = Math.Min(inList, capacity);
      int[] pids = new int[n];
      for (int i = 0; i < n; i++) {
        if (IntPtr.Size == 8)
          pids[i] = (int)Marshal.ReadInt64(buf, 8 + 8 * i);
        else
          pids[i] = Marshal.ReadInt32(buf, 8 + 4 * i);
      }
      return pids;
    } finally { Marshal.FreeHGlobal(buf); }
  }
}
"@
if (-not ('GateNative' -as [type])) {
    Add-Type -TypeDefinition $script:GateNativeSrc -ErrorAction Stop
}

function Start-GateProcess {
    param(
        [Parameter(Mandatory)][string]$FilePath,
        [Parameter(Mandatory)][string]$Arguments,
        [Parameter(Mandatory)][string]$WorkingDirectory,
        [Parameter(Mandatory)][hashtable]$Environment,
        [Parameter(Mandatory)][string]$StdOutPath,
        [Parameter(Mandatory)][string]$StdErrPath
    )
    $cmdExe = "$env:SystemRoot\System32\cmd.exe"
    $inner = '"' + $FilePath + '" ' + $Arguments + ' >"' + $StdOutPath + '" 2>"' + $StdErrPath + '"'
    $commandLine = '"' + $cmdExe + '" /c "' + $inner + '"'

    $entries = @()
    foreach ($k in ($Environment.Keys | Sort-Object)) {
        $entries += ($k + '=' + $Environment[$k])
    }
    $envBlock = [GateNative]::BuildEnvironmentBlock([string[]]$entries)
    $job = [GateNative]::CreateKillOnCloseJob()
    $si = New-Object GateNative+STARTUPINFO
    $si.cb = [Runtime.InteropServices.Marshal]::SizeOf($si)
    $pi = New-Object GateNative+PROCESS_INFORMATION
    $baseFlags = [GateNative]::CREATE_SUSPENDED -bor [GateNative]::CREATE_UNICODE_ENVIRONMENT
    # Prefer breakaway so the suite root is only in our kill-on-close job. Under hosts
    # that disallow breakaway (e.g. Cursor agent job), fall back to nested job assign.
    $flags = $baseFlags -bor [GateNative]::CREATE_BREAKAWAY_FROM_JOB
    $ok = [GateNative]::CreateProcess(
        $cmdExe,
        $commandLine,
        [IntPtr]::Zero, [IntPtr]::Zero,
        $false,
        $flags,
        $envBlock,
        $WorkingDirectory,
        [ref]$si,
        [ref]$pi
    )
    if (-not $ok) {
        $si = New-Object GateNative+STARTUPINFO
        $si.cb = [Runtime.InteropServices.Marshal]::SizeOf($si)
        $pi = New-Object GateNative+PROCESS_INFORMATION
        $ok = [GateNative]::CreateProcess(
            $cmdExe,
            $commandLine,
            [IntPtr]::Zero, [IntPtr]::Zero,
            $false,
            $baseFlags,
            $envBlock,
            $WorkingDirectory,
            [ref]$si,
            [ref]$pi
        )
    }
    [Runtime.InteropServices.Marshal]::FreeHGlobal($envBlock)
    if (-not $ok) {
        $err = [ComponentModel.Win32Exception]::new([Runtime.InteropServices.Marshal]::GetLastWin32Error()).Message
        if ($job -ne [IntPtr]::Zero) { [void][GateNative]::CloseHandle($job) }
        throw "CreateProcess failed: $err"
    }
    $assigned = $false
    if ($job -ne [IntPtr]::Zero) {
        $assigned = [GateNative]::AssignProcessToJobObject($job, $pi.hProcess)
        if (-not $assigned) {
            $jobErr = [ComponentModel.Win32Exception]::new([Runtime.InteropServices.Marshal]::GetLastWin32Error()).Message
            [void][GateNative]::TerminateProcess($pi.hProcess, 1)
            [void][GateNative]::CloseHandle($pi.hThread)
            [void][GateNative]::CloseHandle($pi.hProcess)
            [void][GateNative]::CloseHandle($job)
            throw "AssignProcessToJobObject failed: $jobErr"
        }
    }
    [void][GateNative]::ResumeThread($pi.hThread)
    [void][GateNative]::CloseHandle($pi.hThread)
    return [pscustomobject]@{
        ProcessHandle = $pi.hProcess
        ProcessId     = $pi.dwProcessId
        Job           = $job
        JobAssigned   = $assigned
        OutPath       = $StdOutPath
        ErrPath       = $StdErrPath
    }
}

function Get-GateJobLeftovers {
    param($Handle)
    if ($null -eq $Handle -or $Handle.Job -eq [IntPtr]::Zero) { return @() }
    $pids = @([GateNative]::QueryJobPids($Handle.Job))
    $alive = @()
    foreach ($pid in $pids) {
        if ($pid -le 0) { continue }
        $p = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($p) {
            $alive += [pscustomobject]@{ Pid = $pid; Name = $p.ProcessName }
        }
    }
    return $alive
}

function Wait-GateProcess {
    param(
        $Handle,
        [int]$TimeoutSec
    )
    $ms = [uint32]([Math]::Max(1, $TimeoutSec) * 1000)
    $wait = [GateNative]::WaitForSingleObject($Handle.ProcessHandle, $ms)
    $timedOut = ($wait -eq 0x102) # WAIT_TIMEOUT
    if ($timedOut) {
        if ($Handle.Job -ne [IntPtr]::Zero) {
            [void][GateNative]::TerminateJobObject($Handle.Job, 1)
        }
        [void][GateNative]::WaitForSingleObject($Handle.ProcessHandle, 15000)
    }
    $leftovers = @(Get-GateJobLeftovers -Handle $Handle)
    if ($leftovers.Count -gt 0) {
        if ($Handle.Job -ne [IntPtr]::Zero) {
            [void][GateNative]::TerminateJobObject($Handle.Job, 1)
        }
        Start-Sleep -Milliseconds 200
        $leftovers = @(Get-GateJobLeftovers -Handle $Handle)
    }
    $stdout = ''
    $stderr = ''
    if (Test-Path -LiteralPath $Handle.OutPath) { $stdout = [IO.File]::ReadAllText($Handle.OutPath) }
    else { [IO.File]::WriteAllText($Handle.OutPath, '') }
    if (Test-Path -LiteralPath $Handle.ErrPath) { $stderr = [IO.File]::ReadAllText($Handle.ErrPath) }
    else { [IO.File]::WriteAllText($Handle.ErrPath, '') }
    $code = [uint32]0
    [void][GateNative]::GetExitCodeProcess($Handle.ProcessHandle, [ref]$code)
    if ($Handle.Job -ne [IntPtr]::Zero) {
        # Final leftover check before close (close kills remaining via KILL_ON_JOB_CLOSE)
        $leftovers = @(Get-GateJobLeftovers -Handle $Handle)
        if ($leftovers.Count -gt 0) {
            [void][GateNative]::TerminateJobObject($Handle.Job, 1)
            Start-Sleep -Milliseconds 100
            $leftovers = @(Get-GateJobLeftovers -Handle $Handle)
        }
        [void][GateNative]::CloseHandle($Handle.Job)
        $Handle.Job = [IntPtr]::Zero
    }
    [void][GateNative]::CloseHandle($Handle.ProcessHandle)
    return [pscustomobject]@{
        TimedOut  = $timedOut
        ExitCode  = [int]$code
        StdOut    = $stdout
        StdErr    = $stderr
        Combined  = ($stdout + "`n" + $stderr)
        Leftovers = $leftovers
    }
}

function Parse-UnittestOutput {
    param([string]$Text, [int]$ExitCode)
    $ran = $null
    $ranMatches = [regex]::Matches($Text, 'Ran\s+(\d+)\s+tests?\s+in\s+')
    if ($ranMatches.Count -gt 0) {
        $ran = [int]$ranMatches[$ranMatches.Count - 1].Groups[1].Value
    }
    $failed = 0; $errors = 0; $skipped = 0
    if ($Text -match 'FAILED\s*\(([^)]*)\)') {
        $inner = $Matches[1]
        if ($inner -match 'failures\s*=\s*(\d+)') { $failed = [int]$Matches[1] }
        if ($inner -match 'errors\s*=\s*(\d+)') { $errors = [int]$Matches[1] }
        if ($inner -match 'skipped\s*=\s*(\d+)') { $skipped = [int]$Matches[1] }
    } elseif ($Text -match '(?m)^OK\s*\(([^)]*)\)') {
        $inner = $Matches[1]
        if ($inner -match 'skipped\s*=\s*(\d+)') { $skipped = [int]$Matches[1] }
    }
    # Python 3.12 -v: "test_x (pkg.mod.Class.test_x) ... skipped 'why'"
    # With docstring: "test_x (pkg.mod.Class.test_x)\nDoc line. ... skipped 'why'"
    # Skip id = dotted id inside the parentheses.
    $skipItems = @()
    $skipRx = [regex]::new(
        '(?m)^[^\r\n(]+\(([^)\r\n]+)\)(?:\r?\n(?![^\r\n(]+\([^)\r\n]+\))[^\r\n]*?)?\s*\.\.\.\s+skipped\s+(?:''([^'']*)''|"([^"]*)")',
        [Text.RegularExpressions.RegexOptions]::Multiline
    )
    foreach ($m in $skipRx.Matches($Text)) {
        $reason = $m.Groups[2].Value
        if (-not $reason) { $reason = $m.Groups[3].Value }
        $skipItems += [pscustomobject]@{ id = $m.Groups[1].Value; reason = $reason }
    }
    if ($skipped -eq 0 -and $skipItems.Count -gt 0) { $skipped = $skipItems.Count }
    $okLine = ($Text -match '(?m)^OK\s*$') -or ($Text -match '(?m)^OK\s*\(')
    $failedLine = ($Text -match '(?m)^FAILED\b')
    $noTests = ($Text -match 'NO TESTS RAN') -or ($ran -eq 0) -or ($ExitCode -eq 5 -and ($null -eq $ran -or $ran -eq 0))
    $marker = ($null -ne $ran) -and ($okLine -or $failedLine -or $noTests)
    $passed = 0
    if ($null -ne $ran) { $passed = [Math]::Max(0, $ran - $failed - $errors - $skipped) }
    return [pscustomobject]@{
        Marker    = $marker
        Ran       = $ran
        Passed    = $passed
        Failed    = ($failed + $errors)
        Skipped   = $skipped
        SkipItems = $skipItems
        ZeroFail  = [bool]$noTests
        Ok        = [bool]($okLine -and -not $failedLine -and -not $noTests)
    }
}

function Parse-SummaryPs1 {
    param([string]$Text)
    if ($Text -match '====\s*SUMMARY\s+pass=(\d+)\s+fail=(\d+)\s*====') {
        return [pscustomobject]@{ Marker = $true; Passed = [int]$Matches[1]; Failed = [int]$Matches[2]; Skipped = 0; SkipItems = @() }
    }
    return [pscustomobject]@{ Marker = $false; Passed = 0; Failed = 0; Skipped = 0; SkipItems = @() }
}

function Parse-ChecksOutput {
    param([string]$Text, [int]$ExitCode)
    $passLines = @([regex]::Matches($Text, '(?m)^PASS '))
    $failLines = @([regex]::Matches($Text, '(?m)^FAIL '))
    $coverage = ($Text -match '(?m)^coverage:')
    return [pscustomobject]@{
        Marker = [bool]$coverage
        Passed = $passLines.Count
        Failed = $failLines.Count
        Skipped = 0
        SkipItems = @()
        ExitOk = ($ExitCode -eq 0)
    }
}

function Parse-KotlinXml {
    param([string]$ResultDir, [datetime]$RunStartUtc)
    if (-not (Test-Path -LiteralPath $ResultDir)) {
        return [pscustomobject]@{ Marker = $false; Passed = 0; Failed = 0; Skipped = 0; SkipItems = @(); Reason = 'missing test-results dir' }
    }
    $files = @(Get-ChildItem -LiteralPath $ResultDir -Filter 'TEST-*.xml' -File -ErrorAction SilentlyContinue)
    if ($files.Count -eq 0) {
        return [pscustomobject]@{ Marker = $false; Passed = 0; Failed = 0; Skipped = 0; SkipItems = @(); Reason = 'no TEST-*.xml' }
    }
    $tests = 0; $failures = 0; $errors = 0; $skipped = 0
    $skipItems = @()
    foreach ($f in $files) {
        if ($f.LastWriteTimeUtc -lt $RunStartUtc) {
            return [pscustomobject]@{ Marker = $false; Passed = 0; Failed = 0; Skipped = 0; SkipItems = @(); Reason = "stale XML $($f.Name)" }
        }
        [xml]$doc = Get-Content -LiteralPath $f.FullName -Raw
        $s = $doc.testsuite
        $tests += [int]$s.GetAttribute('tests')
        $failures += [int]$s.GetAttribute('failures')
        $errors += [int]$s.GetAttribute('errors')
        $skAttr = $s.GetAttribute('skipped')
        if ($skAttr) { $skipped += [int]$skAttr }
        foreach ($case in @($s.SelectNodes('testcase'))) {
            if ($null -eq $case) { continue }
            $skippedNodes = @($case.SelectNodes('skipped'))
            foreach ($skippedNode in $skippedNodes) {
                $id = [string]$case.GetAttribute('name')
                $cn = $case.GetAttribute('classname')
                if ($cn) { $id = "$cn.$id" }
                $reason = [string]$skippedNode.GetAttribute('message')
                if (-not $reason -and $skippedNode.InnerText) { $reason = [string]$skippedNode.InnerText }
                $skipItems += [pscustomobject]@{ id = $id; reason = $reason }
            }
        }
    }
    return [pscustomobject]@{
        Marker    = $true
        Passed    = [Math]::Max(0, $tests - $failures - $errors - $skipped)
        Failed    = ($failures + $errors)
        Skipped   = $skipped
        SkipItems = $skipItems
        Reason    = ''
    }
}

function Test-SkipAllowances {
    param(
        $Floor,
        [int]$SkippedCount,
        $SkipItems
    )
    $allowed = @()
    if ($Floor.allowed_skips) { $allowed = @($Floor.allowed_skips) }
    if ($SkippedCount -eq 0 -and (@($SkipItems).Count -eq 0)) {
        return [pscustomobject]@{ Ok = $true; Reason = '' }
    }
    $items = @($SkipItems)
    if ($items.Count -eq 0 -and $SkippedCount -gt 0) {
        return [pscustomobject]@{ Ok = $false; Reason = "skipped=$SkippedCount but no skip identities parsed" }
    }
    if ($SkippedCount -ne $items.Count) {
        return [pscustomobject]@{ Ok = $false; Reason = "skip count/identity mismatch (count=$SkippedCount identities=$($items.Count))" }
    }
    foreach ($item in $items) {
        $match = $false
        foreach ($a in $allowed) {
            $aid = [string]$a.id
            $areason = [string]$a.reason
            if ($aid -eq [string]$item.id -and $areason -eq [string]$item.reason) {
                $match = $true
                break
            }
        }
        if (-not $match) {
            return [pscustomobject]@{ Ok = $false; Reason = "unexpected skip id=$($item.id) reason=$($item.reason)" }
        }
    }
    if ($items.Count -gt $allowed.Count) {
        return [pscustomobject]@{ Ok = $false; Reason = "skip count $($items.Count) > allowed $($allowed.Count)" }
    }
    return [pscustomobject]@{ Ok = $true; Reason = '' }
}

function Classify-SuiteResult {
    param(
        [Parameter(Mandatory)]$Floor,
        [AllowEmptyString()][string]$InfraReason = '',
        [bool]$HasMarker,
        [int]$Passed,
        [int]$Failed,
        [int]$Skipped,
        $SkipItems = @(),
        [bool]$ZeroTestsFail,
        [bool]$ExitSuccess
    )
    if ($InfraReason) {
        return [pscustomobject]@{ Result = 'INFRA'; Reason = $InfraReason }
    }
    if (-not $HasMarker) {
        return [pscustomobject]@{ Result = 'INFRA'; Reason = 'missing completion marker' }
    }
    if ($ZeroTestsFail) {
        return [pscustomobject]@{ Result = 'FAIL'; Reason = 'zero tests / NO TESTS RAN / exit 5' }
    }
    if ($Failed -gt 0) {
        return [pscustomobject]@{ Result = 'FAIL'; Reason = "failures=$Failed" }
    }
    if (-not $ExitSuccess) {
        return [pscustomobject]@{ Result = 'FAIL'; Reason = 'nonzero exit with marker' }
    }
    if ($Passed -lt [int]$Floor.min_passed) {
        return [pscustomobject]@{ Result = 'FAIL'; Reason = "passed $Passed < floor $($Floor.min_passed)" }
    }
    $skipCheck = Test-SkipAllowances -Floor $Floor -SkippedCount $Skipped -SkipItems $SkipItems
    if (-not $skipCheck.Ok) {
        return [pscustomobject]@{ Result = 'FAIL'; Reason = $skipCheck.Reason }
    }
    return [pscustomobject]@{ Result = 'PASS'; Reason = '' }
}

function Get-ToolVersions {
    param([string]$JavaHome, [string]$AndroidHome, [string]$HermesPython)
    $dotnet = ''
    try { $dotnet = ("$(dotnet --version 2>&1)").Trim() } catch {}
    $java = ''
    $javaExe = if ($JavaHome) { Join-Path $JavaHome 'bin\java.exe' } else { $null }
    if ($javaExe -and (Test-Path -LiteralPath $javaExe)) {
        try {
            # java -version writes to stderr; stringify ErrorRecords
            $java = (@(& $javaExe -version 2>&1 | ForEach-Object { "$_" }) | Select-Object -First 1)
            if ($java) { $java = $java.Trim() }
        } catch {}
    }
    $gradle = ''
    $python = ''
    if ($HermesPython -and (Test-Path $HermesPython)) {
        try { $python = ("$(& $HermesPython --version 2>&1)").Trim() } catch {}
    }
    return [ordered]@{
        dotnet = $dotnet
        java   = $java
        gradle = $gradle
        python = $python
    }
}

Export-ModuleMember -Function *
