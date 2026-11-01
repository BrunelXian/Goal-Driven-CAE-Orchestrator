# Offline only. Parse production source; run the coordinator with in-memory fakes.
# Never invoke the production file, native installer, signature network checks or registry.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$sourcePath = Join-Path $PSScriptRoot 'Install-PowerShell769-Approved.ps1'
$tokens = $null; $parseErrors = $null
$ast = [Management.Automation.Language.Parser]::ParseFile($sourcePath, [ref]$tokens, [ref]$parseErrors)
$script:checks = 0
function Assert-Test([bool] $Condition, [string] $Name) {
    if (-not $Condition) { throw "OFFLINE_TEST_FAILED: $Name" }
    $script:checks++
}
Assert-Test ($parseErrors.Count -eq 0) 'syntax'
$text = [IO.File]::ReadAllText($sourcePath)
$main = $ast.Find({ param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Invoke-769ApprovedInstall' }, $true)
Assert-Test ($null -ne $main) 'coordinator present'
$commands = @($ast.FindAll({ param($n) $n -is [Management.Automation.Language.CommandAst] }, $true))
Assert-Test (@($commands | Where-Object { $_.GetCommandName() -eq 'Start-Process' }).Count -eq 1) 'one launch site'
Assert-Test (@($commands | Where-Object { $_.GetCommandName() -match '^(Remove-Item|Stop-Process|Restart-Computer|Set-Acl|Set-ItemProperty|Invoke-Expression)$' }).Count -eq 0) 'no repair mutation or eval'
Assert-Test ($text -notmatch '(?im)-Verb\s+RunAs|ExecutionPolicy|IsProcessInJob|Win32_Product') 'no elevation bypass Job gate or product repair query'
$open = '[IO.File]::Open($source, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read)'
Assert-Test (($main.Extent.Text.Split(@($open), [StringSplitOptions]::None).Count - 1) -eq 1) 'exact readonly source open'
# Replace ONLY the source handle creation in extracted coordinator for a synthetic handle.
$mainFake = $main.Extent.Text.Replace($open, '(New-TestSourceHandle)')
$expectedArgs = '/i "C:\Users\wuxia\AppData\Local\GDCAE-PowerShell-769-Qualification-20261031-A01\PowerShell-7.6.9-win-x64.msi" /qb /norestart INSTALLFOLDER="C:\Program Files\PowerShell" ADD_PATH=0 ADD_EXPLORER_CONTEXT_MENU_OPENPOWERSHELL=0 ADD_FILE_CONTEXT_MENU_RUNPOWERSHELL=0 ENABLE_PSREMOTING=0 REGISTER_MANIFEST=0 USE_MU=0 ENABLE_MU=0 DISABLE_TELEMETRY=0 LAUNCHAPPONEXIT=0 REBOOT=ReallySuppress'
$fixture = {
    param($MainText, $Fault, $Code)
    $script:fault = $Fault; $script:code = $Code; $script:launches = 0
    $script:counts = @{}; $script:arguments = $null; $script:binary = $null
    $script:handle = $null; $script:lockedAtLaunch = $false; $script:promptCount = 0
    function Hit($Name) {
        if (-not $script:counts.ContainsKey($Name)) { $script:counts[$Name] = 0 }
        $script:counts[$Name]++
        if ($script:fault -eq ($Name + ':' + $script:counts[$Name])) { throw 'PRIVATE_FIXTURE_VALUE_MUST_NOT_LEAK' }
    }
    function Assert-769Host { Hit 'host' }
    function Assert-769Conflicts { Hit 'conflict' }
    function Assert-769Paths($Source) { Hit 'path' }
    function Assert-769Bytes($Stream, $Source, $Expected) { Hit 'bytes' }
    function Assert-769SourceSignature($Source) { Hit 'chain' }
    function Assert-769Signature($Path) { Hit 'signature' }
    function New-TestSourceHandle {
        Hit 'open'
        $script:handle = [pscustomobject]@{ Closed = $false; FailClose = ($script:fault -eq 'close') }
        $script:handle | Add-Member ScriptMethod Dispose { if ($this.FailClose) { throw 'PRIVATE_CLOSE_FAILURE' }; $this.Closed = $true }
        return $script:handle
    }
    function Read-Host($Prompt) {
        $script:promptCount++
        Hit 'prompt'
        if ($script:fault -eq 'decline') { return 'NO' }
        return 'INSTALL_769_ONCE'
    }
    function Start-Process($FilePath, $ArgumentList, [switch] $Wait, [switch] $PassThru) {
        $script:launches++
        $script:binary = $FilePath; $script:arguments = $ArgumentList
        $script:lockedAtLaunch = (-not $script:handle.Closed) -and $Wait -and $PassThru
        Hit 'launch'
        $fake = [pscustomobject]@{ ExitCode = $script:code }
        $fake | Add-Member ScriptMethod Dispose {}
        return $fake
    }
    . ([scriptblock]::Create($MainText))
    $json = Invoke-769ApprovedInstall
    [pscustomobject]@{
        Receipt = ($json | ConvertFrom-Json); Raw = $json; Launches = $script:launches
        Arguments = $script:arguments; Binary = $script:binary; Handle = $script:handle
        LockedAtLaunch = $script:lockedAtLaunch; PromptCount = $script:promptCount
    }
}
function Run-Case($Fault, $Code, $Status, $Launches) {
    $result = & $fixture $mainFake $Fault $Code
    Assert-Test ($result.Receipt.status -ceq $Status) "status $Fault $Code"
    Assert-Test ($result.Launches -eq $Launches) "launch count $Fault"
    Assert-Test ($result.Raw -notmatch 'PRIVATE_|Users\\|S-1-') "sanitized $Fault"
    if ($null -ne $result.Handle -and $Fault -ne 'close') { Assert-Test $result.Handle.Closed "source close $Fault" }
    if ($Launches -gt 0) {
        Assert-Test ($result.Arguments -ceq $expectedArgs) "frozen arguments $Fault"
        Assert-Test ($result.Binary -ceq 'C:\Windows\System32\msiexec.exe') "fixed installer $Fault"
        Assert-Test $result.LockedAtLaunch "held handle and wait $Fault"
        Assert-Test ($result.PromptCount -eq 1) "one prompt $Fault"
    }
    return $result
}
$ok = Run-Case '' 0 'INSTALLER_EXIT_0_PENDING_READONLY_VERIFICATION' 1
Assert-Test $ok.Receipt.source_recheck_passed 'postcheck completed'
Assert-Test (-not $ok.Receipt.strong_same_user_isolation_claimed) 'accepted residual risk'
$null = Run-Case '' 3010 'PENDING_REBOOT_STOP' 1
$null = Run-Case '' 1603 'INSTALLER_NONZERO_STOP' 1
$null = Run-Case '' 1602 'INSTALLER_NONZERO_STOP' 1
$null = Run-Case '' $null 'UNKNOWN_INSTALL_STOP' 1
foreach ($fault in @('host:1', 'conflict:1', 'path:1', 'open:1', 'bytes:1', 'chain:1',
    'signature:1', 'prompt:1', 'decline', 'conflict:2', 'path:2', 'bytes:2')) {
    $null = Run-Case $fault 0 'BLOCKED_PREFLIGHT' 0
}
foreach ($fault in @('launch:1', 'path:3', 'bytes:3', 'signature:2')) {
    $null = Run-Case $fault 0 'UNKNOWN_INSTALL_STOP' 1
}
$null = Run-Case 'close' 0 'UNKNOWN_SOURCE_HANDLE_CLOSE' 1
# Exercise the real size gate with a synthetic memory stream; no hash/path/network work.
$bytesFunction = $ast.Find({ param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Assert-769Bytes' }, $true)
. ([scriptblock]::Create($bytesFunction.Extent.Text))
$tiny = [IO.MemoryStream]::new([byte[]]@(1,2,3))
try {
    $blocked = $false
    try { Assert-769Bytes $tiny 'SYNTHETIC_ONLY' 'NOT_A_HASH' } catch { $blocked = $_.Exception.Message -ceq 'MSI_SIZE_MISMATCH' }
    Assert-Test $blocked 'real size guard rejects synthetic wrong length'
} finally { $tiny.Dispose() }
# Same-byte bootstrap principle: hash and execute a harmless captured byte array after
# the simulated source variable has changed. No filesystem writes or production invocation.
$snapshot = [Text.Encoding]::UTF8.GetBytes("'SNAPSHOT_OK'")
$sha = [Security.Cryptography.SHA256]::Create()
try {
    $pinned = [BitConverter]::ToString($sha.ComputeHash($snapshot))
    $changedSource = [Text.Encoding]::UTF8.GetBytes("'WRONG_SOURCE'")
    Assert-Test ([BitConverter]::ToString($sha.ComputeHash($snapshot)) -ceq $pinned) 'snapshot digest'
    Assert-Test ([BitConverter]::ToString($sha.ComputeHash($changedSource)) -cne $pinned) 'replacement rejected'
    Assert-Test ((& ([scriptblock]::Create([Text.Encoding]::UTF8.GetString($snapshot)))) -ceq 'SNAPSHOT_OK') 'execute captured bytes'
} finally { $sha.Dispose() }
# Test the EXACT published bootstrap with only its read expression and pinned hash
# replaced by harmless in-memory fixture values. Never execute the installer snapshot.
$card = [IO.File]::ReadAllText((Join-Path $PSScriptRoot 'POWERSHELL769_PACKAGED_INSTALL_ACTION_CARD_2026-11-01.md'))
$match = [regex]::Match($card, '(?s)```powershell\r?\n(.*?)\r?\n```')
Assert-Test $match.Success 'published bootstrap exists'
$bootstrap = $match.Groups[1].Value
$bt = $null; $be = $null
$bootstrapAst = [Management.Automation.Language.Parser]::ParseInput($bootstrap, [ref]$bt, [ref]$be)
Assert-Test ($be.Count -eq 0) 'bootstrap syntax'
Assert-Test (([regex]::Matches($bootstrap, 'ReadAllBytes')).Count -eq 1) 'single snapshot read'
$scriptBytes = [IO.File]::ReadAllBytes($sourcePath)
$sha = [Security.Cryptography.SHA256]::Create()
try {
    $scriptHash = [BitConverter]::ToString($sha.ComputeHash($scriptBytes)).Replace('-', '').ToLowerInvariant()
    Assert-Test $bootstrap.Contains("'$scriptHash'") 'card pins current script'
    $fixtureBytes = [Text.Encoding]::UTF8.GetBytes("'BOOTSTRAP_FIXTURE_OK'")
    $fixtureHash = [BitConverter]::ToString($sha.ComputeHash($fixtureBytes)).Replace('-', '').ToLowerInvariant()
    $readExpression = "[IO.File]::ReadAllBytes('$sourcePath')"
    Assert-Test $bootstrap.Contains($readExpression) 'exact pinned script path'
    $fixtureBootstrap = $bootstrap.Replace($readExpression, '$fixtureBytes').Replace($scriptHash, $fixtureHash)
    Assert-Test ((& ([scriptblock]::Create($fixtureBootstrap))) -ceq 'BOOTSTRAP_FIXTURE_OK') 'exact bootstrap success'
    $fixtureBytes = [Text.Encoding]::UTF8.GetBytes("throw 'UNVERIFIED_BYTES_EXECUTED'")
    $rejected = $false
    try { & ([scriptblock]::Create($fixtureBootstrap)) } catch { $rejected = $_.Exception.Message -ceq 'SCRIPT_HASH_MISMATCH_STOP' }
    Assert-Test $rejected 'exact bootstrap mismatch stops before execution'
} finally { $sha.Dispose() }
[ordered]@{ status = 'OFFLINE_TEST_PASS'; checks = $script:checks; native_installer_launches = 0; production_script_executed = $false; powershell = $PSVersionTable.PSVersion.ToString() } | ConvertTo-Json -Compress
