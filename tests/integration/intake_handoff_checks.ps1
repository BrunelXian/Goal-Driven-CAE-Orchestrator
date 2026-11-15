param(
    [Parameter(Mandatory)][string]$Plugin,
    [Parameter(Mandatory)][string]$ManifestPin,
    [Parameter(Mandatory)][string]$FreshSettings
)
$ErrorActionPreference = 'Stop'
if (Test-Path -LiteralPath $FreshSettings) { throw 'Fresh synthetic settings required' }
$previousSettings = $env:LOCALAPPDATA
try {
    $env:LOCALAPPDATA = [IO.Path]::GetFullPath($FreshSettings)
    $script = Join-Path $Plugin 'scripts/main-handoff.ps1'
    $base = @('-NoProfile','-NonInteractive','-File',$script,'-HostId','fixture','-ProjectId','study',
              '-ManifestSha256',$ManifestPin)
    function Invoke-Receipt([string[]]$Flags, [string]$ExpectedError) {
        $output = & pwsh @base @Flags 2>&1
        if ($ExpectedError) {
            if ($LASTEXITCODE -ne 2 -or ($output -join ' ') -notmatch $ExpectedError) {throw "Expected $ExpectedError"}
        } else {
            if ($LASTEXITCODE -ne 0) {throw "Failed receipt operation"}
            $output | ConvertFrom-Json
        }
    }
    $first = Invoke-Receipt @('-Action','claim','-Title','LoadInv Main')
    $retry = Invoke-Receipt @('-Action','claim','-Title','LoadInv Main')
    if (!$first.may_create -or $retry.may_create -or $retry.state -ne 'CREATE_UNKNOWN') { throw 'Duplicate create' }
    Invoke-Receipt @('-Action','claim','-Title','Other Main') 'MAIN_TITLE_CONFLICT'
    $receipt = @('-RequestId',$first.request_id,'-ThreadId','synthetic-main')
    $r = Invoke-Receipt (@('-Action','record') + $receipt)
    if ($r.state -ne 'REF_RECORDED') { throw 'Missing pending readback' }
    Invoke-Receipt @('-Action','record','-RequestId',$first.request_id,'-ThreadId','other') 'MAIN_ALREADY_BOUND'
    Invoke-Receipt (@('-Action','verify','-ObservedProjectId','wrong','-ObservedTitle','LoadInv Main') + $receipt) 'HOST_READBACK_MISMATCH'
    $r = Invoke-Receipt (@('-Action','verify','-ObservedProjectId','study','-ObservedTitle','LoadInv Main') + $receipt)
    $reread = Invoke-Receipt @('-Action','inspect','-Title','LoadInv Main')
    if ($r.state -ne 'VERIFIED' -or $reread.thread_id -ne 'synthetic-main' -or $reread.may_create) { throw 'Wrong final identity' }
    'PASS: interrupted create, retry, title conflict, pending readback, conflicting thread, wrong project, verified reuse'
} finally { $env:LOCALAPPDATA = $previousSettings }
