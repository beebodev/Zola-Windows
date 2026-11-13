@{
    GateVersion = '1.0.0'
    # Paths recorded only here (not inherited). Hermes root comes from User ZOLA_HERMES_ROOT at runtime.
    JavaHome    = 'C:\Program Files\Android\Android Studio\jbr'
    AndroidHome = '%LOCALAPPDATA%\Android\Sdk'

    ClearEnvNames = @(
        'PYTHONPATH', 'PYTHONHOME', 'VIRTUAL_ENV', 'HERMES_HOME',
        'PIP_INDEX_URL', 'PIP_EXTRA_INDEX_URL', 'PIP_REQUIRE_VIRTUALENV', 'PIP_TARGET', 'PIP_FIND_LINKS'
    )

    Suites = @(
        @{
            Name             = 'client_checks'
            WorkingDirectory = ''
            Kind             = 'checks'
            TimeoutSec       = 300
            NeedsZolaClosed  = $false
            PromoteOnly      = $false
            NeedsPythonPath  = $false
            NeedsAndroid     = $false
            DiscoverS        = ''
            DiscoverT        = ''
            ScriptRelative   = ''
            Command          = @('dotnet', 'run', '--project', 'windows-client\Zola.Client.Checks\Zola.Client.Checks.csproj', '-c', 'Release')
        }
        @{
            Name             = 'stable_scripts'
            WorkingDirectory = ''
            Kind             = 'summary_ps1'
            TimeoutSec       = 720
            NeedsZolaClosed  = $false
            PromoteOnly      = $false
            NeedsPythonPath  = $false
            NeedsAndroid     = $false
            DiscoverS        = ''
            DiscoverT        = ''
            ScriptRelative   = 'tools\stable\Test-StableScripts.ps1'
            Command          = @()
        }
        @{
            Name             = 'dev_tools'
            WorkingDirectory = ''
            Kind             = 'summary_ps1'
            TimeoutSec       = 60
            NeedsZolaClosed  = $false
            PromoteOnly      = $false
            NeedsPythonPath  = $false
            NeedsAndroid     = $false
            DiscoverS        = ''
            DiscoverT        = ''
            ScriptRelative   = 'tools\dev\Test-DevTools.ps1'
            Command          = @()
        }
        @{
            Name             = 'zola_workspace'
            WorkingDirectory = 'hermes-plugins\zola_workspace'
            Kind             = 'unittest'
            TimeoutSec       = 360
            NeedsZolaClosed  = $false
            PromoteOnly      = $false
            NeedsPythonPath  = $true
            NeedsAndroid     = $false
            DiscoverS        = 'tests'
            DiscoverT        = 'tests'
            ScriptRelative   = ''
            Command          = @()
        }
        @{
            Name             = 'zola_memory'
            WorkingDirectory = 'hermes-plugins\zola_memory'
            Kind             = 'unittest'
            TimeoutSec       = 60
            NeedsZolaClosed  = $false
            PromoteOnly      = $false
            NeedsPythonPath  = $true
            NeedsAndroid     = $false
            DiscoverS        = 'tests'
            DiscoverT        = '.'
            ScriptRelative   = ''
            Command          = @()
        }
        @{
            Name             = 'zola_tools'
            WorkingDirectory = 'hermes-plugins\zola_tools'
            Kind             = 'unittest'
            TimeoutSec       = 60
            NeedsZolaClosed  = $false
            PromoteOnly      = $false
            NeedsPythonPath  = $true
            NeedsAndroid     = $false
            DiscoverS        = 'tests'
            DiscoverT        = '.'
            ScriptRelative   = ''
            Command          = @()
        }
        @{
            Name             = 'zola_tts'
            WorkingDirectory = 'hermes-plugins\zola_tts'
            Kind             = 'unittest'
            TimeoutSec       = 60
            NeedsZolaClosed  = $false
            PromoteOnly      = $false
            NeedsPythonPath  = $true
            NeedsAndroid     = $false
            DiscoverS        = 'tests'
            DiscoverT        = '.'
            ScriptRelative   = ''
            Command          = @()
        }
        @{
            Name             = 'zola_phone'
            WorkingDirectory = 'hermes-plugins\zola_phone'
            Kind             = 'unittest'
            TimeoutSec       = 120
            NeedsZolaClosed  = $true
            PromoteOnly      = $false
            NeedsPythonPath  = $true
            NeedsAndroid     = $false
            DiscoverS        = 'tests'
            DiscoverT        = '.'
            ScriptRelative   = ''
            Command          = @()
        }
        @{
            Name             = 'kotlin_unit'
            WorkingDirectory = 'android-companion'
            Kind             = 'kotlin_unit'
            TimeoutSec       = 600
            NeedsZolaClosed  = $false
            PromoteOnly      = $false
            NeedsPythonPath  = $false
            NeedsAndroid     = $true
            DiscoverS        = ''
            DiscoverT        = ''
            ScriptRelative   = ''
            Command          = @()
        }
        @{
            Name             = 'assemble_debug'
            WorkingDirectory = 'android-companion'
            Kind             = 'assemble_debug'
            TimeoutSec       = 600
            NeedsZolaClosed  = $false
            PromoteOnly      = $true
            NeedsPythonPath  = $false
            NeedsAndroid     = $true
            DiscoverS        = ''
            DiscoverT        = ''
            ScriptRelative   = ''
            Command          = @()
        }
        @{
            Name             = 'gate_self'
            WorkingDirectory = ''
            Kind             = 'gate_self'
            TimeoutSec       = 120
            NeedsZolaClosed  = $false
            PromoteOnly      = $false
            NeedsPythonPath  = $false
            NeedsAndroid     = $false
            DiscoverS        = ''
            DiscoverT        = ''
            ScriptRelative   = 'tools\test-gate\Test-TestGate.ps1'
            Command          = @()
        }
    )
}
