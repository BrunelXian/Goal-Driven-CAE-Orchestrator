[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidateSet('bind','doctor','main','agreement')][string]$Action,
    [string]$PythonExe, [string]$ManifestSha256, [string]$BindingSha256,
    [string]$ProjectRoot, [string]$OutputDirectory, [string]$Operation, [string]$InputFile,
    [string]$Selector, [string]$AgreementRoot
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
function Assert-FileHash([string]$Path, [string]$Expected, [string]$Code) {
    if ($Expected -notmatch '^[0-9a-fA-F]{64}$' -or
        (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash -ne $Expected) { throw $Code }
}
function Assert-Absolute([string]$Path) {
    if ($Path -notmatch '^[A-Za-z]:[\\/]' -or [IO.Path]::GetFullPath($Path) -ne $Path) {
        throw 'EXPLICIT_ABSOLUTE_LOCAL_PATH_REQUIRED'
    }
}
$pluginRoot = (Get-Item -LiteralPath $PSScriptRoot).Parent.FullName
$manifestPath = Join-Path $pluginRoot 'package-manifest.json'
$driver = Join-Path $PSScriptRoot 'main.py'
try {
    if (($Operation -or $InputFile -or $Selector) -and $Action -ne 'agreement') { throw 'INVALID_AGREEMENT_ARGUMENTS' }
    if ($AgreementRoot -and $Action -ne 'main') { throw 'INVALID_AGREEMENT_ARGUMENTS' }
    if ($Action -eq 'bind') {
        Assert-Absolute $PythonExe
        if ($BindingSha256 -or $ProjectRoot -or $OutputDirectory) { throw 'INVALID_BIND_ARGUMENTS' }
        $actionArgs = @('bind','--manifest-sha256',$ManifestSha256,'--selected-python',$PythonExe)
    } else {
        if ($PythonExe -or $ManifestSha256) { throw 'INTERPRETER_OVERRIDE_DENIED' }
        $bindingPath = Join-Path $env:LOCALAPPDATA 'GDCAE\gdcae-research\0.2.0-preview.6\binding.json'
        Assert-FileHash $bindingPath $BindingSha256 'BINDING_RECEIPT_MISMATCH'
        $binding = Get-Content -LiteralPath $bindingPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($binding.plugin -ne $pluginRoot -or $binding.version -ne '0.2.0-preview.6') { throw 'INSTALLATION_IDENTITY_MISMATCH' }
        $ManifestSha256 = $binding.package_manifest_sha256
        $PythonExe = $binding.runtime.interpreter
        Assert-Absolute $PythonExe
        foreach ($file in $binding.runtime.runtime_files.PSObject.Properties) {
            Assert-FileHash $file.Name $file.Value 'WORKSPACE_RUNTIME_MISMATCH'
        }
        $actionArgs = @($Action,'--binding-sha256',$BindingSha256)
        if ($Action -eq 'main') {
            Assert-Absolute $ProjectRoot
            Assert-Absolute $OutputDirectory
            $actionArgs += @('--project-root',$ProjectRoot,'--output',$OutputDirectory)
            if ($AgreementRoot) { Assert-Absolute $AgreementRoot; $actionArgs += @('--agreement-root',$AgreementRoot) }
        }
        if ($Action -eq 'agreement') {
            Assert-Absolute $ProjectRoot
            if ($OutputDirectory -or -not $Operation) { throw 'INVALID_AGREEMENT_ARGUMENTS' }
            $actionArgs += @('--project-root',$ProjectRoot,'--operation',$Operation)
            if ($InputFile) { Assert-Absolute $InputFile; $actionArgs += @('--input-file',$InputFile) }
            if ($Selector) { $actionArgs += @('--selector',$Selector) }
        }
    }
    Assert-FileHash $manifestPath $ManifestSha256 'PACKAGE_MANIFEST_MISMATCH'
    $manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
    Assert-FileHash $PSCommandPath $manifest.files.'scripts/launch.ps1' 'LAUNCHER_IDENTITY_MISMATCH'
    Assert-FileHash $driver $manifest.files.'scripts/main.py' 'DRIVER_IDENTITY_MISMATCH'
    $checks = Join-Path $PSScriptRoot 'runtime-checks.ps1'
    Assert-FileHash $checks $manifest.files.'scripts/runtime-checks.ps1' 'RUNTIME_CHECKER_MISMATCH'
    . $checks
    $specPath = Join-Path $pluginRoot 'runtime/cpython-windows.json'
    Assert-FileHash $specPath $manifest.files.'runtime/cpython-windows.json' 'RUNTIME_POLICY_MISMATCH'
    $spec = Get-Content -Raw -LiteralPath $specPath -Encoding UTF8 | ConvertFrom-Json
    $managedRoot = Get-RuntimeParent
    if ($PythonExe.StartsWith($managedRoot+'\', [StringComparison]::OrdinalIgnoreCase)) {
        $expectedRoot = Join-Path $managedRoot $spec.directory
        if ($PythonExe -ne (Join-Path $expectedRoot 'python.exe')) { throw 'UNREGISTERED_MANAGED_PATH' }
        Assert-RuntimeTree $expectedRoot $spec
    }
    & $PythonExe -I -B -S $driver @actionArgs
    exit $LASTEXITCODE
} catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 2
}

