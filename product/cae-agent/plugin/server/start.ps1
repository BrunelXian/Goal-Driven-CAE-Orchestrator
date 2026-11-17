param([Parameter(Mandatory=$true)][ValidateSet('gdcae-core','abqjobpilot')][string]$Service)
$ErrorActionPreference = 'Stop'
$plugin = (Get-Item -LiteralPath $PSScriptRoot).Parent
$cache = $plugin.Parent.Parent.Parent
if ($cache.Name -ne 'cache' -or $cache.Parent.Name -ne 'plugins') { throw 'INSTALLED_CODEX_ADAPTER_REQUIRED' }
$profileFile = Join-Path $cache.Parent.Parent.FullName 'cae-agent/deployment.json'
$cfg = Get-Content -Raw -Encoding UTF8 -LiteralPath $profileFile | ConvertFrom-Json
function Assert-Digest($Path,$Expected) {
    if (-not [IO.Path]::IsPathRooted($Path) -or $Expected -notmatch '^[0-9a-f]{64}$' -or
        (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash -ne $Expected) { throw 'DEPLOYMENT_IDENTITY_CHANGED' }
}
if ([IO.Path]::GetFullPath($cfg.adapter_root) -ne $plugin.FullName) { throw 'ADAPTER_BINDING_CHANGED' }
$adapterManifest = Join-Path $plugin.FullName 'manifest.json'
Assert-Digest $adapterManifest $cfg.adapter_sha256
$adapter = Get-Content -Raw -Encoding UTF8 -LiteralPath $adapterManifest | ConvertFrom-Json
Assert-Digest $PSCommandPath $adapter.files.'server/start.ps1'
$serviceManifest = Join-Path $cfg.service_root 'manifest.json'
Assert-Digest $serviceManifest $cfg.service_sha256
$runtime = Get-Content -Raw -Encoding UTF8 -LiteralPath $serviceManifest | ConvertFrom-Json
$entry = Join-Path $cfg.service_root 'serve.py'
Assert-Digest $entry $runtime.files.'serve.py'
Assert-Digest $cfg.python $cfg.python_sha256
& $cfg.python -I -B $entry $Service --profile $profileFile --adapter $plugin.FullName
exit $LASTEXITCODE
