param(
    [Parameter(Mandatory)][string]$Plugin,
    [Parameter(Mandatory)][string]$ManifestPin
)
$ErrorActionPreference = 'Stop'
$entry = Join-Path $Plugin 'scripts/intake.ps1'
$facts = @{ShortName='LoadInv'; Objective='Infer F'; Metric='1 mm down +/-0.1 mm'; Assets='Declared model'
           Unknowns='Node and independent reference'; ManifestSha256=$ManifestPin}
function Check($expect, $jobs, $model, [string[]]$needs) {
    $record = & $entry @facts -Jobs $jobs -ModelConditions $model -ManagementNeeds $needs | ConvertFrom-Json
    if ($record.assessment.classification -cne $expect -or $record.execution_authorized -or
        $record.handoff -cne 'PENDING_HOST_CHECK' -or $record.tasks.Count -ne 2 -or
        $record.tasks[0].owner -cne 'CAE' -or $record.tasks[1].owner -cne 'Diagnostics') {
        throw "Intake regression: $expect $needs"
    }
    foreach ($card in $record.tasks) {
        if ($card.persistence -cne 'DRAFT_NOT_PERSISTED' -or $card.dispatch -cne 'BLOCKED_HOST_ROLE_BINDING' -or
            !$card.goal -or !$card.input -or !$card.deliverable -or !$card.criterion) {throw 'Invalid draft'}
    }
}
Check 'SIMPLE_LOCAL' 'single' 'defined' @('none')
Check 'UNKNOWN_COMPLEXITY' 'unknown' 'defined' @('none')
Check 'UNKNOWN_COMPLEXITY' 'single' 'unknown' @('none')
Check 'UNKNOWN_COMPLEXITY' 'single' 'defined' @('unknown')
Check 'MANAGED_WORKFLOW' 'multiple' 'unknown' @('unknown')
foreach ($signal in 'inverse','scan','optimization','batch','queue','long-monitoring','recovery','budget-control','strict-traceability','candidate-versions') {
    Check 'MANAGED_WORKFLOW' 'single' 'defined' @($signal)
}
'PASS: 15 routing cases with complete drafts, pending handoff and no grant'
