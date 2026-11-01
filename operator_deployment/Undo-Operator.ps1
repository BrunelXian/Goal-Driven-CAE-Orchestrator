#requires -Version 7.4
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$PlanPath,
    [ValidateSet('DryRun','Apply')][string]$Mode = 'DryRun',
    [string]$ApprovedPlanSha256 = '',
    [string]$HumanApproval = ''
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
try {
    if ($Mode -eq 'Apply') {
        $trusted = 'C:\ProgramData\GDCAE Operator Preparation'
        if ([IO.Path]::GetFullPath($PSScriptRoot) -cne $trusted -or
            [IO.Path]::GetDirectoryName([IO.Path]::GetFullPath($PlanPath)) -cne $trusted) { throw 'ADMIN_STAGING_REQUIRED' }
        foreach ($p in @($trusted,$PSCommandPath,(Join-Path $trusted 'Operator.Common.ps1'),$PlanPath)) {
            if ((Get-Item -LiteralPath $p -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'REPARSE_REJECTED' }
            $acl = Get-Acl -LiteralPath $p
            if ($acl.GetOwner([Security.Principal.SecurityIdentifier]).Value -notin @('S-1-5-18','S-1-5-32-544')) { throw 'UNTRUSTED_BOOTSTRAP_OWNER' }
            foreach ($rule in $acl.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier])) {
                if ($rule.AccessControlType -eq 'Allow' -and
                    $rule.IdentityReference.Value -notin @('S-1-5-18','S-1-5-32-544')) { throw 'WRITABLE_BOOTSTRAP' }
            }
        }
        $parent = [IO.Path]::GetDirectoryName($trusted)
        $installer = ([Security.Principal.NTAccount]'NT SERVICE\TrustedInstaller').Translate([Security.Principal.SecurityIdentifier]).Value
        $allowedOwners = @('S-1-5-18','S-1-5-32-544',$installer)
        while ($parent) {
            if ((Get-Item -LiteralPath $parent -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'BOOTSTRAP_PARENT_REPARSE' }
            $acl = Get-Acl -LiteralPath $parent
            if ($acl.GetOwner([Security.Principal.SecurityIdentifier]).Value -notin $allowedOwners) { throw 'BOOTSTRAP_PARENT_OWNER' }
            foreach ($rule in $acl.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier])) {
                if ($rule.PropagationFlags -band [Security.AccessControl.PropagationFlags]::InheritOnly) { continue }
                if ($rule.AccessControlType -eq 'Allow' -and ([long]$rule.FileSystemRights -band 0x500D0040) -and
                    $rule.IdentityReference.Value -notin $allowedOwners) { throw 'BOOTSTRAP_PARENT_REPLACEABLE' }
            }
            $parent = [IO.Path]::GetDirectoryName($parent)
        }
    }
    . (Join-Path $PSScriptRoot 'Operator.Common.ps1')
    $plan = Read-OperatorPlan $PlanPath $ApprovedPlanSha256 ($Mode -eq 'Apply')
    $receiptPath = "$($plan.state_root)/deployment/receipt.json"
    Assert-NoReparse $receiptPath
    $receipt = Get-Content -LiteralPath $receiptPath -Raw | ConvertFrom-Json -AsHashtable
    if ($receipt.schema -ne 'gdcae-foundation-receipt-v1' -or $receipt.plan_sha256 -cne $script:PlanHash -or
        $receipt.host_sha256 -cne $plan.host_sha256 -or $receipt.activated -ne $false -or
        $receipt.owner_started -ne $false -or $receipt.capability_created -ne $false -or
        $receipt.intent -ne $null -or $receipt.status -notin @('FOUNDATION_STAGED_ACCOUNTS_DISABLED_ACTIVATION_BLOCKED','ROLLED_BACK_DISABLED')) {
        throw 'UNKNOWN_OR_ACTIVATED_RECEIPT_NO_AUTOMATIC_UNDO'
    }
    if ($receipt.accounts.Count -ne 2) { throw 'ACCOUNT_RECEIPT_INCOMPLETE' }
    for ($i=0; $i -lt 2; $i++) {
        $record = $receipt.accounts[$i]
        $user = Get-LocalUser -Name $plan.accounts[$i] -ErrorAction Stop
        if ($record.name -cne $plan.accounts[$i] -or $user.SID.Value -cne $record.sid) { throw 'IDENTITY_CHANGED' }
        if ($user.Enabled) { throw 'ACCOUNT_ENABLED_REQUIRES_SEPARATE_REVIEW' }
    }
    # Never disable an account after unrecorded activation/use: existing sessions
    # and processes would survive disable. This script does not inspect or kill them.
    if (@(Get-ChildItem -LiteralPath "$($plan.state_root)/projects" -Force).Count -ne 0 -or
        @(Get-ChildItem -LiteralPath "$($plan.state_root)/config" -Force).Count -ne 0) { throw 'STATE_USED_STOP_FOR_REVIEW' }
    if ($Mode -eq 'DryRun') {
        [ordered]@{status='UNDO_DRY_RUN_NO_CHANGES'; action='DISABLE_TWO_EXACT_CREATED_ACCOUNTS'; preserve_files=$true} | ConvertTo-Json -Compress
        return
    }
    Assert-IndependentAdmin $HumanApproval 'APPROVE_FOUNDATION_ROLLBACK_ONLY'
    foreach ($record in $receipt.accounts) { Disable-LocalUser -SID $record.sid -ErrorAction Stop }
    $receipt.status = 'ROLLED_BACK_DISABLED'; Write-Receipt $receiptPath $receipt
    [ordered]@{status='ROLLED_BACK_DISABLED'; deleted_files=0; terminated_processes=0} | ConvertTo-Json -Compress
} catch {
    [ordered]@{status='BLOCKED'; code='UNDO_REQUIRES_EXACT_UNUSED_RECEIPT_NO_RETRY'} | ConvertTo-Json -Compress
    exit 1
}
