[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidateSet('claim','inspect','record','verify')][string]$Action,
    [Parameter(Mandatory)][string]$HostId,
    [Parameter(Mandatory)][string]$ProjectId,
    [Parameter(Mandatory)][string]$ManifestSha256,
    [string]$RequestId, [string]$ThreadId, [string]$Title,
    [string]$ObservedProjectId, [string]$ObservedTitle
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
function Digest([string]$value) {
    $h=[Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($h.ComputeHash([Text.Encoding]::UTF8.GetBytes($value)))).Replace('-','').ToLowerInvariant() }
    finally { $h.Dispose() }
}
function Save-State($state,[bool]$first) {
    $temp=Join-Path $dir ([guid]::NewGuid().ToString('N')+'.tmp')
    $stream=[IO.File]::Open($temp,'CreateNew','Write','None')
    try {
        $bytes=[Text.Encoding]::UTF8.GetBytes(($state | ConvertTo-Json -Compress))
        $stream.Write($bytes,0,$bytes.Length)
        $stream.Flush($true)
    } finally { $stream.Dispose() }
    try {
        if ($first) { [IO.File]::Move($temp,$file) }
        else {
            $backup=Join-Path $dir ([guid]::NewGuid().ToString('N')+'.bak')
            [IO.File]::Replace($temp,$file,$backup)
            [IO.File]::Delete($backup)
        }
    } finally { if ([IO.File]::Exists($temp)) { [IO.File]::Delete($temp) } }
}
try {
    foreach ($id in @($HostId,$ProjectId)) {
        if ($id -cnotmatch '^[a-zA-Z0-9._:-]{1,160}$') { throw 'INVALID_HOST_PROJECT' }
    }
    $root=(Get-Item -LiteralPath $PSScriptRoot).Parent.FullName
    $manifest=Join-Path $root 'package-manifest.json'
    if ($ManifestSha256 -notmatch '^[a-fA-F0-9]{64}$' -or (Get-FileHash -LiteralPath $manifest).Hash -ne $ManifestSha256) { throw 'PACKAGE_MANIFEST_MISMATCH' }
    $files=(Get-Content -Raw -Encoding UTF8 -LiteralPath $manifest | ConvertFrom-Json).files
    if ((Get-FileHash -LiteralPath $PSCommandPath).Hash -ne $files.'scripts/main-handoff.ps1') { throw 'HANDOFF_SCRIPT_MISMATCH' }
    $checks=Join-Path $PSScriptRoot 'runtime-checks.ps1'
    if ((Get-FileHash -LiteralPath $checks).Hash -ne $files.'scripts/runtime-checks.ps1') { throw 'PACKAGE_IDENTITY_MISMATCH' }
    . $checks
    $key=Digest ("gdcae-main-handoff-v1`n"+$HostId+"`n"+$ProjectId)
    $dir=Join-Path $env:LOCALAPPDATA 'GDCAE\project-main-handoffs\v1'
    $file=Join-Path $dir ($key+'.json')
    Assert-LocalTreePath $file
    if ($Action -eq 'inspect' -and ![IO.File]::Exists($file)) {
        @{state='ABSENT';may_create=$false} | ConvertTo-Json; exit 0
    }
    [void][IO.Directory]::CreateDirectory($dir)
    $guard=Join-Path $dir ($key+'.lock')
    Assert-LocalTreePath $guard
    $lock=[IO.File]::Open($guard,'OpenOrCreate','ReadWrite','None')
    try {
        $mayCreate=$false
        if (![IO.File]::Exists($file)) {
            if ($Action -ne 'claim') { throw 'HANDOFF_NOT_CLAIMED' }
            if ($Title -cnotmatch '^[A-Za-z0-9][A-Za-z0-9_-]{0,31} Main$') { throw 'INVALID_MAIN_TITLE' }
            $state=[pscustomobject]@{schema='gdcae-main-handoff-v1';host_id=$HostId;project_id=$ProjectId;request_id=$key;title=$Title;thread_id='';state='CREATE_UNKNOWN'}
            Save-State $state $true
            $mayCreate=$true
        } else {
            $state=Get-Content -Raw -Encoding UTF8 -LiteralPath $file | ConvertFrom-Json
            if ($state.schema -cne 'gdcae-main-handoff-v1' -or $state.host_id -cne $HostId -or $state.project_id -cne $ProjectId -or $state.request_id -cne $key -or $state.state -notin 'CREATE_UNKNOWN','REF_RECORDED','VERIFIED') { throw 'HANDOFF_CONFLICT' }
            if ($Action -in 'record','verify') {
                if ($RequestId -cne $key -or $ThreadId -cnotmatch '^[a-zA-Z0-9._:-]{1,160}$') { throw 'INVALID_RECEIPT' }
                if ($state.thread_id -and $state.thread_id -cne $ThreadId) { throw 'MAIN_ALREADY_BOUND' }
                if ($Action -eq 'record' -and $state.state -eq 'CREATE_UNKNOWN') {
                    $state.thread_id=$ThreadId; $state.state='REF_RECORDED'; Save-State $state $false
                } elseif ($Action -eq 'verify') {
                    if ($state.thread_id -cne $ThreadId -or $ObservedProjectId -cne $ProjectId -or $ObservedTitle -cne $state.title) { throw 'HOST_READBACK_MISMATCH' }
                    $state.state='VERIFIED'; Save-State $state $false
                }
            }
        }
        $state | Select-Object *,@{Name='may_create';Expression={$mayCreate}} | ConvertTo-Json
    } finally { $lock.Dispose() }
} catch { [Console]::Error.WriteLine($_.Exception.Message); exit 2 }
