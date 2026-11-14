[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidateSet('options','defer','plan','install')][string]$Action,
    [string]$ManifestSha256,
    [ValidateSet('managed')][string]$Choice,
    [switch]$ConfirmDownload
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$plugin=(Get-Item -LiteralPath $PSScriptRoot).Parent.FullName
try {
    if ($Action -eq 'options') {
        Get-Content -LiteralPath (Join-Path $plugin 'references/runtime-options.md') -Raw -Encoding UTF8
        exit 0
    }
    if ($Action -eq 'defer') { 'DEFERRED'; exit 0 }
    if ($Choice -ne 'managed') { throw 'EXPLICIT_CHOICE_REQUIRED' }
    $manifestFile=Join-Path $plugin 'package-manifest.json'
    if ($ManifestSha256 -notmatch '^[0-9a-fA-F]{64}$' -or
        (Get-FileHash -LiteralPath $manifestFile -Algorithm SHA256).Hash -ne $ManifestSha256) { throw 'PACKAGE_MANIFEST_MISMATCH' }
    $manifest=Get-Content -LiteralPath $manifestFile -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($manifest.version -ne '0.2.0-preview.6') { throw 'PACKAGE_VERSION_MISMATCH' }
    foreach ($entry in $manifest.files.PSObject.Properties) {
        if ($entry.Name -eq 'plugin.json') { continue } # The driver checks D01 semantics before activation.
        $file=Join-Path $plugin $entry.Name
        if ((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash -ne $entry.Value) { throw ('PACKAGE_IDENTITY_MISMATCH:'+$entry.Name) }
    }
    . (Join-Path $PSScriptRoot 'runtime-checks.ps1')
    $spec=Get-Content -LiteralPath (Join-Path $plugin 'runtime/cpython-windows.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $parent=Get-RuntimeParent
    $target=Join-Path $parent $spec.directory
    Assert-LocalTreePath $target
    $plan=[ordered]@{source=$spec.url; bytes=$spec.archive_bytes; sha256=$spec.archive_sha256; target=$target;
        expanded_bytes=$spec.expanded_bytes; writes='Private staging, runtime and version-specific binding'; system_changes=$false}
    if ($Action -eq 'plan') { $plan | ConvertTo-Json; exit 0 }
    if (!$ConfirmDownload) { throw 'DOWNLOAD_CONFIRMATION_REQUIRED' }
    if (Test-Path -LiteralPath $target) { throw 'RUNTIME_ALREADY_EXISTS' }
    $receipt=Join-Path $env:LOCALAPPDATA 'GDCAE\gdcae-research\0.2.0-preview.6\binding.json'
    Assert-LocalTreePath $receipt
    if (Test-Path -LiteralPath $receipt) { throw 'BINDING_ALREADY_EXISTS' }
    $drive=[IO.DriveInfo]::new([IO.Path]::GetPathRoot($target))
    Assert-RuntimeSpace $drive.AvailableFreeSpace $spec
    if (![Environment]::Is64BitOperatingSystem -or !(Test-Path -LiteralPath (Join-Path ([Environment]::SystemDirectory) 'ucrtbase.dll'))) { throw 'WINDOWS_X64_UCRT_REQUIRED' }
    [void][IO.Directory]::CreateDirectory($parent)
    $lockPath=Join-Path $parent ($spec.directory+'.install-lock')
    $lock=[IO.File]::Open($lockPath,'CreateNew','Write','None')
    try {
        if (Test-Path -LiteralPath $target) { throw 'RUNTIME_ALREADY_EXISTS' }
        $stage=Join-Path $parent ($spec.directory+'.staging')
        if (Test-Path -LiteralPath $stage) { throw 'PREVIOUS_INSTALL_INCOMPLETE' }
        $payload=Join-Path $stage 'payload'
        [void][IO.Directory]::CreateDirectory($payload)
        $archive=Join-Path $stage 'download.zip'
        Receive-RuntimeArchive $spec $archive
        Expand-RuntimeArchive $archive $payload $spec
        $exe=Join-Path $payload 'python.exe'
        $probe=& $exe -I -B -S (Join-Path $PSScriptRoot 'main.py') preflight --manifest-sha256 $ManifestSha256
        if ($LASTEXITCODE -ne 0) { throw ("STAGED_PREFLIGHT_FAILED: "+($probe -join ' ')) }
        [IO.Directory]::Move($payload,$target)
        [IO.File]::Delete($archive)
        [IO.Directory]::Delete($stage,$false)
        & (Join-Path $PSScriptRoot 'launch.ps1') -Action bind -PythonExe (Join-Path $target 'python.exe') -ManifestSha256 $ManifestSha256
        if ($LASTEXITCODE -ne 0) { throw 'RUNTIME_INSTALLED_BIND_FAILED' }
    } finally {
        $lock.Dispose()
        [IO.File]::Delete($lockPath)
    }
} catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 2
}
