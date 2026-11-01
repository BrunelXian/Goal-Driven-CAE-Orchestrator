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
        # External human hash verification is still required before invoking this
        # entry file. No self-check can authenticate an already replaced script.
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
    Assert-NewDeployment $plan
    Assert-Sources $plan
    if ($Mode -eq 'DryRun') {
        [ordered]@{ status='DRY_RUN_NO_CHANGES'; accounts=2; files=$plan.source_files.Count;
            roots=@($plan.code_root,$plan.state_root); activation='BLOCKED'; owner_started=$false } | ConvertTo-Json -Compress
        return
    }
    Assert-IndependentAdmin $HumanApproval 'APPROVE_FOUNDATION_ONLY'
    # Passwords never appear in command arguments, plan, logs or receipts.
    $passwords = @{}
    foreach ($name in $plan.accounts) { $passwords[$name] = Read-Host "New password for $name" -AsSecureString }
    # Repeat collision/source checks immediately before any mutation.
    Assert-NewDeployment $plan
    Assert-Sources $plan
    $bootstrapIntent = "$($plan.staging_root)/deployment-intent.json"
    if (Test-Path -LiteralPath $bootstrapIntent) { throw 'PRIOR_INTENT_NO_RETRY' }
    Write-Receipt $bootstrapIntent ([ordered]@{schema='gdcae-foundation-intent-v1'; plan_sha256=$script:PlanHash;
        host_sha256=$plan.host_sha256; status='ROOT_CREATION_INTENT'; roots=@($plan.state_root,$plan.code_root)})
    New-ProtectedDirectory $plan.state_root @{}
    New-ProtectedDirectory "$($plan.state_root)/deployment" @{}
    $receiptPath = "$($plan.state_root)/deployment/receipt.json"
    $receipt = [ordered]@{ schema='gdcae-foundation-receipt-v1'; plan_sha256=$script:PlanHash;
        host_sha256=$plan.host_sha256; status='IN_PROGRESS'; accounts=@(); files=@(); intent=$null;
        owner_started=$false; capability_created=$false; activated=$false }
    Write-Receipt $receiptPath $receipt
    try {
        foreach ($name in $plan.accounts) {
            $receipt.intent = "CREATE_DISABLED_ACCOUNT:$name"; Write-Receipt $receiptPath $receipt
            $account = New-LocalUser -Name $name -Password $passwords[$name] -Disabled -Description 'GDCAE approved foundation only' -ErrorAction Stop
            $receipt.accounts += @{ name=$name; sid=$account.SID.Value; enabled=$false }
            $receipt.intent = $null; Write-Receipt $receiptPath $receipt
            $receipt.intent = "ADD_USERS_GROUP:$name"; Write-Receipt $receiptPath $receipt
            Add-LocalGroupMember -SID 'S-1-5-32-545' -Member $account -ErrorAction Stop
            $receipt.intent = $null; Write-Receipt $receiptPath $receipt
        }
        $research = $receipt.accounts[0].sid; $issuer = $receipt.accounts[1].sid
        $receipt.intent = 'CREATE_CODE_ROOT'; Write-Receipt $receiptPath $receipt
        New-ProtectedDirectory $plan.code_root @{ $research='ReadAndExecute'; $issuer='ReadAndExecute' }
        # State root remains admin-owned/immutable. Issuer can traverse/read, not create root children.
        Set-NewRootSecurity $plan.state_root @{ $issuer='ReadAndExecute' }
        foreach ($relative in @('config','projects','audit','review')) {
            $receipt.intent = "CREATE_STATE_CHILD:$relative"; Write-Receipt $receiptPath $receipt
            $rights = if ($relative -eq 'config') { 'ReadAndExecute' } else { 'Modify' }
            New-ProtectedDirectory "$($plan.state_root)/$relative" @{ $issuer=$rights }
        }
        foreach ($item in $plan.source_files) {
            $receipt.intent = 'COPY_PINNED_FILE'; Write-Receipt $receiptPath $receipt
            Copy-PinnedFile $plan.code_root $item @{ $research='ReadAndExecute'; $issuer='ReadAndExecute' }
            $receipt.files += @{ destination=$item.destination; sha256=$item.sha256 }
        }
        $receipt.intent = $null
        # Deliberately leave both accounts disabled. Enabling/login is a separately
        # reviewed human activation step, not an implicit effect of source staging.
        $receipt.status = 'FOUNDATION_STAGED_ACCOUNTS_DISABLED_ACTIVATION_BLOCKED'
        Write-Receipt $receiptPath $receipt
        Write-Receipt $bootstrapIntent ([ordered]@{schema='gdcae-foundation-intent-v1'; plan_sha256=$script:PlanHash;
            host_sha256=$plan.host_sha256; status=$receipt.status; roots=@($plan.state_root,$plan.code_root)})
        [ordered]@{status=$receipt.status; accounts=2; files=$receipt.files.Count; activation='BLOCKED'} | ConvertTo-Json -Compress
    } catch {
        $receipt.status = 'PARTIAL_UNKNOWN_NO_RETRY'
        Write-Receipt $receiptPath $receipt
        # No auto rollback, adoption, account removal or secret-bearing error output.
        throw 'DEPLOYMENT_PARTIAL_MANUAL_RECONCILIATION_REQUIRED'
    } finally {
        foreach ($password in $passwords.Values) { $password.Dispose() }
    }
} catch {
    [ordered]@{ status='BLOCKED'; code='DEPLOYMENT_GUARD_OR_OPERATION_FAILED'; mutated='CHECK_PRIVATE_RECEIPT_IF_APPLY' } | ConvertTo-Json -Compress
    exit 1
}
