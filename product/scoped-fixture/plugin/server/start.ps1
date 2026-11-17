param(
    [Parameter(Mandatory=$true)][ValidateSet('gdcae-core','abqjobpilot')][string]$Service,
    [string]$ProfileFile
)
$ErrorActionPreference = 'Stop'
$plugin = (Get-Item -LiteralPath $PSScriptRoot).Parent
if (-not $ProfileFile) {
    $cache = $plugin.Parent.Parent.Parent
    if ($cache.Name -ne 'cache' -or $cache.Parent.Name -ne 'plugins') { throw 'INSTALLED_PLUGIN_PROFILE_REQUIRED' }
    $ProfileFile = Join-Path $cache.Parent.Parent.FullName 'gdcae-scoped-fixture/deployment.json'
}
if (-not [IO.Path]::IsPathRooted($ProfileFile)) { throw 'LOCAL_PROFILE_REQUIRED' }
$cfg = Get-Content -Raw -Encoding UTF8 -LiteralPath $ProfileFile | ConvertFrom-Json
$manifestFile = Join-Path $plugin.FullName 'manifest.json'
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $manifestFile).Hash -ne $cfg.manifest_sha256) { throw 'MANIFEST_CHANGED' }
$manifest = Get-Content -Raw -Encoding UTF8 -LiteralPath $manifestFile | ConvertFrom-Json
$entry = Join-Path $PSScriptRoot 'serve.py'
foreach ($pair in @(@($PSCommandPath,$manifest.files.'server/start.ps1'), @($entry,$manifest.files.'server/serve.py'), @($cfg.python,$cfg.python_sha256))) {
    if ((Get-FileHash -Algorithm SHA256 -LiteralPath $pair[0]).Hash -ne $pair[1]) { throw 'LAUNCH_IDENTITY_CHANGED' }
}
if (-not [IO.Path]::IsPathRooted($cfg.python) -or [IO.Path]::GetFileName($cfg.python) -ne 'python.exe') { throw 'BOUND_PYTHON_REQUIRED' }
& $cfg.python -I -B $entry $Service $ProfileFile
exit $LASTEXITCODE
