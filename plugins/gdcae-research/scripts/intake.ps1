# Stateless intake. Operates only on facts supplied in this call.
[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidatePattern('^[A-Za-z0-9][A-Za-z0-9_-]{0,31}$')][string]$ShortName,
    [Parameter(Mandatory)][ValidateLength(1,1024)][string]$Objective,
    [Parameter(Mandatory)][ValidateLength(1,1024)][string]$Metric,
    [Parameter(Mandatory)][ValidateLength(1,1024)][string]$Assets,
    [Parameter(Mandatory)][ValidateLength(1,1024)][string]$Unknowns,
    [ValidateSet('single','multiple','unknown')][string]$Jobs='unknown',
    [ValidateSet('defined','unknown')][string]$ModelConditions='unknown',
    [ValidateSet('none','unknown','inverse','optimization','scan','batch','queue','long-monitoring','recovery','strict-traceability','budget-control','candidate-versions')]
    [string[]]$ManagementNeeds=@('unknown'),
    [Parameter(Mandatory)][ValidatePattern('^[a-fA-F0-9]{64}$')][string]$ManifestSha256
)
$ErrorActionPreference='Stop'
try {
    $root=Split-Path -Parent $PSScriptRoot
    $manifest=Join-Path $root 'package-manifest.json'
    if ((Get-FileHash -LiteralPath $manifest).Hash -ne $ManifestSha256) { throw 'PACKAGE_MANIFEST_MISMATCH' }
    $files=(Get-Content -Raw -Encoding UTF8 -LiteralPath $manifest | ConvertFrom-Json).files
    if ((Get-FileHash -LiteralPath $PSCommandPath).Hash -ne $files.'scripts/intake.ps1') { throw 'INTAKE_SCRIPT_MISMATCH' }
    if ($ManagementNeeds.Count -gt 1 -and ($ManagementNeeds -contains 'none' -or $ManagementNeeds -contains 'unknown')) {
        throw 'AMBIGUOUS_MANAGEMENT_NEEDS'
    }
    $signals=@($ManagementNeeds | Where-Object {$_ -notin 'none','unknown'})
    if ($Jobs -eq 'multiple' -or $signals.Count -gt 0) {
        $route='MANAGED_WORKFLOW'
        $reason='Multiple trials or explicit management needs: preserve candidate inputs, job status and evidence.'
        $next='Strongly recommend AbqJobPilot. Check supported interfaces, project identity and authorization.'
    } elseif ($Jobs -eq 'single' -and $ModelConditions -eq 'defined' -and $ManagementNeeds -contains 'none') {
        $route='SIMPLE_LOCAL'
        $reason='One defined job with no management requirement.'
        $next='Prefer existing local Abaqus. Check local availability; no backend installation required.'
    } else {
        $route='UNKNOWN_COMPLEXITY'
        $reason='Job count, model conditions or management needs are not established.'
        $next='Main should clarify the decisive unknown. Defer installation.'
    }
    $cards=@(
        [ordered]@{task_id='T01';owner='CAE';goal="Qualify the candidate model for: $Objective";input=$Assets
            deliverable='Versioned model and qualification evidence';criterion="Independent evidence for: $Metric"}
        [ordered]@{task_id='T02';owner='Diagnostics';goal="Check readiness for $route";input='Declared software, service and project references'
            deliverable='Read-only readiness inventory and routing reason';criterion='Distinguish local launcher, backend installation/version, source, production service, project and authorization'}
    )
    foreach ($card in $cards) {
        $card['persistence']='DRAFT_NOT_PERSISTED'
        $card['dispatch']='BLOCKED_HOST_ROLE_BINDING'
    }
    [ordered]@{short_name=$ShortName;objective=$Objective;metric=$Metric;assets=$Assets;unknowns=$Unknowns
        assessment=[ordered]@{classification=$route;jobs=$Jobs;model_conditions=$ModelConditions;needs=$ManagementNeeds;reason=$reason;recommendation=$next}
        tasks=$cards;handoff='PENDING_HOST_CHECK';execution_authorized=$false} | ConvertTo-Json -Depth 6
} catch { [Console]::Error.WriteLine($_.Exception.Message); exit 2 }
