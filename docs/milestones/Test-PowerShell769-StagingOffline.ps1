#requires -Version 5.1
# Offline only: extract functions, never execute the production top level.
# Synthetic files stay under a new user TEMP directory. No native write API calls.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$base = $PSScriptRoot
$production = Join-Path $base 'Stage-PowerShell769-Approved.ps1'
$card = Join-Path $base 'POWERSHELL769_STATIC_GATE_ACTION_CARD_2026-11-01.md'
$tokens=$null; $errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($production,[ref]$tokens,[ref]$errors)
if (@($errors).Count) { throw 'PRODUCTION_PARSE_ERROR' }
$definitions = @{}
foreach($function in $ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst]},$true)) {
    $definitions[$function.Name]=$function.Extent.Text
    . ([ScriptBlock]::Create($function.Extent.Text))
}
$cardText=[IO.File]::ReadAllText($card)
$bootstrap=[regex]::Match($cardText,'(?s)```powershell\r?\n(.*?)\r?\n```').Groups[1].Value
$bootstrapAst=[Management.Automation.Language.Parser]::ParseInput($bootstrap,[ref]$tokens,[ref]$errors)
if (@($errors).Count) { throw 'BOOTSTRAP_PARSE_ERROR' }
foreach($function in $bootstrapAst.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst]},$true)) {
    . ([ScriptBlock]::Create($function.Extent.Text))
}
$fixtureRoot=Join-Path $env:TEMP ('GDCAE769-OFFLINE-'+[Guid]::NewGuid().ToString('N'))
$null=[IO.Directory]::CreateDirectory($fixtureRoot)
$passed=[Collections.Generic.List[string]]::new()
function Check([bool]$Condition,[string]$Name) { if(-not $Condition){throw ('FAILED_'+$Name)}; $passed.Add($Name) }
function Reject([ScriptBlock]$Action,[string]$Name) {
    $rejected=$false
    try { & $Action | Out-Null } catch { $rejected=$true }
    Check $rejected $Name
}

Check ((Get-StaticJobObservation $true $true) -eq $true) 'job_true_admitted_recorded'
Check ((Get-StaticJobObservation $true $false) -eq $false) 'job_false_admitted_recorded'
Reject {Get-StaticJobObservation $false $false} 'job_query_failure_rejected'
$hostFacts=@{Edition='Desktop';Version='5.1';Is64Bit=$true;Interactive=$true;LanguageMode='FullLanguage';
    Path='C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe';Signature='Valid';
    Signer='CN=Microsoft Windows, O=Microsoft Corporation, C=US';Admin=$true;Impersonated=$false}
Assert-StagingHostFacts $hostFacts
Check $true 'valid_host_facts'
foreach($case in @(
    @('Admin',$false),@('Impersonated',$true),@('Path','X:\untrusted\pwsh.exe'),
    @('Edition','Core'),@('Version','4.0'),@('Is64Bit',$false),@('Interactive',$false),
    @('LanguageMode','ConstrainedLanguage'),@('Signature','UnknownError'),@('Signer','CN=Other'))) {
    $invalid=$hostFacts.Clone();$invalid[$case[0]]=$case[1]
    Reject {Assert-StagingHostFacts $invalid} ('host_reject_'+$case[0])
}
$expectedSize=117493760L
$expectedHash='50d33c7494aaf82b987cfd4de3f232d04f91fdd4c0deeca8a669cced3e7cf8f9'
Assert-StagingFileIdentity $expectedSize $expectedHash
Check $true 'approved_file_identity'
Reject {Assert-StagingFileIdentity 10 $expectedHash} 'wrong_file_size'
Reject {Assert-StagingFileIdentity $expectedSize ('0'*64)} 'wrong_file_hash'
$sig=@{Status='Valid';SignerCertificate=@{Subject='CN=Microsoft Corporation, O=Microsoft Corporation, C=US'};TimeStamperCertificate=@{Subject='timestamp'}}
Assert-StagingSignatureFacts $sig
Check $true 'valid_signature_facts'
foreach($state in @('NotSigned','HashMismatch','UnknownError')) {
    $bad=$sig.Clone();$bad.Status=$state
    Reject {Assert-StagingSignatureFacts $bad} ('signature_'+$state)
}
$bad=$sig.Clone();$bad.SignerCertificate=@{Subject='CN=Other'}
Reject {Assert-StagingSignatureFacts $bad} 'non_microsoft_signature'
$bad=$sig.Clone();$bad.TimeStamperCertificate=$null
Reject {Assert-StagingSignatureFacts $bad} 'missing_timestamp'
Assert-StagingRegistrationFacts $false $false $false
Check $true 'registration_absent_admitted'
Reject {Assert-StagingRegistrationFacts $true $false $false} 'distribution_marker_conflict'
Reject {Assert-StagingRegistrationFacts $false $true $false} 'app_path_conflict'
Reject {Assert-StagingRegistrationFacts $false $false $true} 'existing_install_target_conflict'

# Real .NET ACL objects in memory, never Set-Acl on filesystem objects.
$adminSid=[Security.Principal.SecurityIdentifier]::new('S-1-5-32-544')
$systemSid=[Security.Principal.SecurityIdentifier]::new('S-1-5-18')
$script:fixtureAcl=[Security.AccessControl.DirectorySecurity]::new()
$script:fixtureAttributes=[IO.FileAttributes]::Directory
function Get-Acl {param($LiteralPath) return $script:fixtureAcl}
function Get-Item {param($LiteralPath,[switch]$Force) return [pscustomobject]@{Attributes=$script:fixtureAttributes;PSIsContainer=$true}}
$script:fixtureAcl.SetSecurityDescriptorSddlForm('O:BAG:BAD:P(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)')
Assert-ExactSecurity 'synthetic' $true
Check $true 'exact_directory_dacl'
foreach($sddl in @(
    'O:SYG:BAD:P(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)',
    'O:BAG:BAD:(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)',
    'O:BAG:BAD:P(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)(A;;FR;;;BU)',
    'O:BAG:BAD:P(A;;FA;;;SY)(A;;FA;;;BA)',
    'O:BAG:BAD:P(A;OICI;FA;;;SY)(A;OICI;FR;;;BA)')) {
    $script:fixtureAcl=[Security.AccessControl.DirectorySecurity]::new()
    $script:fixtureAcl.SetSecurityDescriptorSddlForm($sddl)
    Reject {Assert-ExactSecurity 'synthetic' $true} ('reject_dacl_'+$passed.Count)
}
$script:fixtureAttributes=[IO.FileAttributes]::ReparsePoint
Reject {Assert-PlainPath 'synthetic'} 'reparse_rejected'
$script:fixtureAttributes=[IO.FileAttributes]::Directory
$trusted=@($adminSid.Value,$systemSid.Value)
$script:fixtureAcl=[Security.AccessControl.DirectorySecurity]::new()
$script:fixtureAcl.SetSecurityDescriptorSddlForm('O:BAG:BAD:P(A;;FA;;;BA)(A;;FA;;;SY)(A;;FR;;;BU)(A;OICIIO;FA;;;CO)')
Assert-Ancestor 'synthetic' $trusted
Check $true 'ancestor_readonly_and_inherit_only_allowed'
foreach($mask in @(0x10000,0x40,0x40000,0x80000,0x100,0x10)) {
    $script:fixtureAcl=[Security.AccessControl.DirectorySecurity]::new()
    $script:fixtureAcl.SetSecurityDescriptorSddlForm(('O:BAG:BAD:P(A;;FA;;;BA)(A;;0x{0:X8};;;BU)' -f $mask))
    Reject {Assert-Ancestor 'synthetic' $trusted} ('ancestor_mutation_'+$mask)
}

foreach($gate in @('HOST','REGISTRATION','SOURCE','CONFIRMATION')) {
    Check ((Get-StagingFailureStatus $false $gate) -ceq ('BLOCKED_'+$gate)) ('before_write_'+$gate)
}
foreach($gate in @('CREATE_CALL','PARTIAL_DIRECTORY','COPY','INTENT_PERSISTENCE','FLUSH','RECEIPT','HANDLE_RELEASE')) {
    Check ((Get-StagingFailureStatus $true $gate) -ceq ('UNKNOWN_'+$gate)) ('after_intent_'+$gate)
}

# Verify emitted interop metadata only. Do not call any emitted P/Invoke.
$native=Initialize-StagingNative
$methods=@($native.GetMethods([Reflection.BindingFlags]'Public,Static,DeclaredOnly'))
Check ($methods.Count -eq 3) 'only_three_native_declarations'
foreach($method in $methods) {
    $import=$method.GetCustomAttributes([Runtime.InteropServices.DllImportAttribute],$false)[0]
    Check ($import.Value -eq 'kernel32.dll' -and $import.SetLastError -and $import.ExactSpelling) ('native_metadata_'+$method.Name)
}

# Creation wrapper exercised against a fake managed type, never kernel32.
class StagingOfflineFakeNative {
    static [int]$Calls=0
    static [bool]$Fail=$false
    static [bool] CreateDirectoryW([string]$Path,[IntPtr]$Attributes) {
        if($Path -ne 'synthetic-no-filesystem-target'){throw 'WRONG_FAKE_PATH'}
        if([Runtime.InteropServices.Marshal]::ReadInt32($Attributes,0) -ne 24){throw 'BAD_ATTRIBUTES_SIZE'}
        if([Runtime.InteropServices.Marshal]::ReadIntPtr($Attributes,8) -eq [IntPtr]::Zero){throw 'MISSING_CREATION_DACL'}
        if([Runtime.InteropServices.Marshal]::ReadInt32($Attributes,16) -ne 0){throw 'INHERIT_HANDLE'}
        [StagingOfflineFakeNative]::Calls++
        return -not [StagingOfflineFakeNative]::Fail
    }
}
$creationAcl=[Security.AccessControl.DirectorySecurity]::new()
$creationAcl.SetSecurityDescriptorSddlForm('O:BAG:BAD:P(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)')
New-StagingDirectoryAtomic ([StagingOfflineFakeNative]) 'synthetic-no-filesystem-target' $creationAcl.GetSecurityDescriptorBinaryForm()
Check ([StagingOfflineFakeNative]::Calls -eq 1) 'creation_descriptor_passed_in_first_call'
[StagingOfflineFakeNative]::Fail=$true
Reject {New-StagingDirectoryAtomic ([StagingOfflineFakeNative]) 'synthetic-no-filesystem-target' $creationAcl.GetSecurityDescriptorBinaryForm()} 'creation_failure_not_retried'
Check ([StagingOfflineFakeNative]::Calls -eq 2) 'one_call_per_attempt'

# Actual Write-StagingRecord function with synthetic files and injected IO faults.
function Assert-ExactSecurity {param($Path,$Directory) if($script:recordFault -eq 'acl'){throw 'FIXTURE_ACL'}}
$script:recordFault='none'
class StagingOfflineRecordStream : IDisposable {
    [IO.FileStream]$Inner
    [string]$Fault
    [string]$Path
    StagingOfflineRecordStream([string]$Path,[string]$Fault) {
        $this.Path=$Path;$this.Fault=$Fault
        $this.Inner=[IO.File]::Open($Path,[IO.FileMode]::CreateNew,[IO.FileAccess]::ReadWrite,[IO.FileShare]::Read)
    }
    [void]Write([byte[]]$Bytes,[int]$Offset,[int]$Count) {
        if($this.Fault -eq 'write'){$this.Inner.Write($Bytes,$Offset,1);throw 'FIXTURE_PARTIAL_WRITE'}
        $this.Inner.Write($Bytes,$Offset,$Count)
    }
    [void]Flush([bool]$Disk) {if($this.Fault -eq 'flush'){throw 'FIXTURE_FLUSH'};$this.Inner.Flush($Disk)}
    [void]Dispose() {
        $this.Inner.Dispose()
        if($this.Fault -eq 'dispose'){throw 'FIXTURE_DISPOSE'}
        if($this.Fault -eq 'readback'){[IO.File]::WriteAllText($this.Path,'corrupt')}
    }
}
function New-PrivateFile {param($Path)
    if($script:recordFault -eq 'create'){throw 'FIXTURE_CREATE'}
    return [StagingOfflineRecordStream]::new($Path,$script:recordFault)
}
$record=[ordered]@{attempt_id='SYNTHETIC';status='STAGING_CHECKS_COMPLETE_PENDING_FINAL_CONSOLE'}
$recordPath=Join-Path $fixtureRoot 'record-good.json'
$recordHash=Write-StagingRecord $recordPath $record
Check ($recordHash -ceq (Microsoft.PowerShell.Utility\Get-FileHash -LiteralPath $recordPath -Algorithm SHA256).Hash.ToLowerInvariant()) 'record_flush_and_readback_digest'
Reject {Write-StagingRecord $recordPath $record} 'record_cannot_overwrite'
foreach($fault in @('create','acl','write','flush','dispose','readback')) {
    $script:recordFault=$fault
    $faultPath=Join-Path $fixtureRoot ('record-'+$fault+'.json')
    $result='UNEXPECTED_SUCCESS'
    try {$null=Write-StagingRecord $faultPath $record}
    catch {$result=Get-StagingFailureStatus $true 'RECEIPT_PERSISTENCE'}
    Check ($result -ceq 'UNKNOWN_RECEIPT_PERSISTENCE') ('record_fault_'+$fault)
}

# Bootstrap tests execute harmless synthetic snapshots only.
foreach($policy in @('Restricted','AllSigned','Bypass','Undefined')) {
    Reject {Assert-PinnedLoaderPolicy 'FullLanguage' $policy} ('loader_policy_'+$policy)
}
Reject {Assert-PinnedLoaderPolicy 'ConstrainedLanguage' 'RemoteSigned'} 'loader_constrained_language'
$snapshotPath=Join-Path $fixtureRoot 'snapshot.ps1'
[IO.File]::WriteAllText($snapshotPath,"'ORIGINAL_SNAPSHOT'",[Text.UTF8Encoding]::new($false))
$snapshotHash=(Microsoft.PowerShell.Utility\Get-FileHash -LiteralPath $snapshotPath -Algorithm SHA256).Hash.ToLowerInvariant()
$snapshot=Get-PinnedStageBlock $snapshotPath $snapshotHash
[IO.File]::WriteAllText($snapshotPath,"throw 'REPLACEMENT_EXECUTED'",[Text.UTF8Encoding]::new($false))
Check ((& $snapshot) -ceq 'ORIGINAL_SNAPSHOT') 'path_replaced_after_capture_uses_original_bytes'
Reject {Get-PinnedStageBlock $snapshotPath $snapshotHash} 'modified_snapshot_hash_rejected'
$utf8Path=Join-Path $fixtureRoot 'invalid-utf8.ps1'
[IO.File]::WriteAllBytes($utf8Path,[byte[]]@(0xC3,0x28))
$utf8Hash=(Microsoft.PowerShell.Utility\Get-FileHash -LiteralPath $utf8Path -Algorithm SHA256).Hash.ToLowerInvariant()
Reject {Get-PinnedStageBlock $utf8Path $utf8Hash} 'invalid_utf8_rejected'
Microsoft.PowerShell.Management\Set-Content -LiteralPath $snapshotPath -Stream 'Zone.Identifier' -Value "[ZoneTransfer]`r`nZoneId=3"
$newHash=(Microsoft.PowerShell.Utility\Get-FileHash -LiteralPath $snapshotPath -Algorithm SHA256).Hash.ToLowerInvariant()
Reject {Get-PinnedStageBlock $snapshotPath $newHash} 'remote_marker_rejected_without_policy_bypass'

# Actual production control-flow invariants, not a second workflow implementation.
$source=[IO.File]::ReadAllText($production)
$topTry=@($ast.EndBlock.Statements | Where-Object {$_ -is [Management.Automation.Language.TryStatementAst]})[0]
$tryText=$topTry.Body.Extent.Text
Check ($tryText.IndexOf('$writeIntent = $true') -lt $tryText.IndexOf('New-StagingDirectoryAtomic $native')) 'intent_precedes_real_create_call'
Check ($tryText.IndexOf('STAGING_INTENT.safe.json') -lt $tryText.IndexOf('$inputStream.CopyTo')) 'durable_unknown_intent_precedes_copy'
Check ($tryText -notmatch "status = 'POWERSHELL7_STAGING_VERIFIED'") 'no_success_before_receipt'
Check ($topTry.CatchClauses[0].Body.Extent.Text -match 'Get-StagingFailureStatus \$writeIntent \$gate') 'real_catch_uses_unknown_after_intent'
Check ($topTry.CatchClauses[0].Body.Extent.Text -match '\$checksComplete = \$false') 'caught_fault_clears_success_eligibility'
$finallyText=$topTry.Finally.Extent.Text
Check ($finallyText.IndexOf('Write-StagingRecord $receiptPath') -lt $finallyText.IndexOf("status = 'POWERSHELL7_STAGING_VERIFIED'")) 'receipt_success_precedes_console_success'
Check ($finallyText -match 'UNKNOWN_RECEIPT_PERSISTENCE' -and $finallyText -match "Get-StagingFailureStatus \`$writeIntent 'HANDLE_RELEASE'") 'finally_failures_cannot_pass'
$commandNames=@($ast.FindAll({param($n) $n -is [Management.Automation.Language.CommandAst]},$true) | ForEach-Object {$_.GetCommandName()})
Check (@($commandNames | Where-Object {$_ -match '^(Add-Type|Start-Process|msiexec(\.exe)?|Set-Acl|Remove-Item|Set-ExecutionPolicy|Invoke-Expression)$'}).Count -eq 0) 'no_compiler_installer_acl_repair_cleanup_or_policy_change'
Check ($source -notmatch "throw 'HOST_IN_JOB'") 'no_blanket_job_rejection'
Check ($source -match 'O:BAG:BAD:P\(A;OICI;FA;;;SY\)\(A;OICI;FA;;;BA\)') 'creation_security_descriptor_preserved'
Check ($bootstrap -notmatch '& \$Path|& \$p\b') 'bootstrap_never_executes_mutable_path'

# Execute the real production catch/finally blocks with synthetic state and IO.
# Do not invoke its try body, host probes or native filesystem functions.
$productionCatch=[ScriptBlock]::Create($topTry.CatchClauses[0].Body.Extent.Text.Trim().Substring(1).TrimEnd().TrimEnd('}'))
$productionFinally=[ScriptBlock]::Create($topTry.Finally.Extent.Text.Trim().Substring(1).TrimEnd().TrimEnd('}'))
class StagingOfflineBadHandle : IDisposable { [void]Dispose(){throw 'FIXTURE_HANDLE_CLOSE'} }
function Exercise-Finalization([string]$Name,[bool]$Intent,[bool]$Secure,[bool]$Complete,[bool]$Caught,[string]$Fault,[bool]$BadHandle) {
    $stage=Join-Path $fixtureRoot $Name
    $null=[IO.Directory]::CreateDirectory($stage)
    $writeIntent=$Intent;$secureStage=$Secure;$checksComplete=$Complete;$created=$Secure
    $gate='INJECTED';$script:recordFault=$Fault
    $receipt=[ordered]@{status='STAGING_CHECKS_COMPLETE_PENDING_FINAL_CONSOLE';attempt_id='SYNTHETIC'}
    $locks=[Collections.Generic.List[IDisposable]]::new()
    if($BadHandle){$locks.Add([StagingOfflineBadHandle]::new())}
    if($Caught){try {throw 'INJECTED_FAILURE'} catch {. $productionCatch}}
    $output=. $productionFinally
    return ($output | ConvertFrom-Json)
}
$r=Exercise-Finalization 'prewrite' $false $false $false $true 'none' $false
Check ($r.status -ceq 'BLOCKED_INJECTED') 'actual_catch_prewrite_blocked'
$r=Exercise-Finalization 'partial-create' $true $false $false $true 'none' $false
Check ($r.status -ceq 'UNKNOWN_INJECTED') 'actual_catch_partial_creation_unknown'
$r=Exercise-Finalization 'late-fault' $true $true $true $true 'none' $false
Check ($r.status -ceq 'UNKNOWN_INJECTED') 'actual_late_fault_not_promoted_to_pass'
foreach($fault in @('create','write','flush','dispose','readback')) {
    $r=Exercise-Finalization ('final-'+$fault) $true $true $true $false $fault $false
    Check ($r.status -ceq 'UNKNOWN_RECEIPT_PERSISTENCE') ('actual_finalization_'+$fault+'_unknown')
}
$r=Exercise-Finalization 'handle-close' $true $true $true $false 'none' $true
Check ($r.status -ceq 'UNKNOWN_HANDLE_RELEASE') 'actual_handle_release_cannot_pass'
$r=Exercise-Finalization 'complete' $true $true $true $false 'none' $false
Check ($r.status -ceq 'POWERSHELL7_STAGING_VERIFIED' -and $r.receipt_persistence_confirmed) 'actual_finalization_validated_success'
$disk=[IO.File]::ReadAllText((Join-Path $fixtureRoot 'complete\POWERSHELL7_STAGING_RECEIPT.safe.json')) | ConvertFrom-Json
Check ($disk.status -ceq 'STAGING_CHECKS_COMPLETE_PENDING_FINAL_CONSOLE') 'disk_record_alone_never_claims_verified'
$summary=[ordered]@{
    status='OFFLINE_PASS';count=$passed.Count;cases=@($passed)
    runtime=[string]$PSVersionTable.PSVersion;edition=$PSVersionTable.PSEdition
    production_top_level_executed=$false;native_staging_calls=0
    admin_staging_or_installation_performed=$false
    fixture_root=$fixtureRoot
    limitations='No actual administrator/NTFS staging, kernel32 write call, external termination or power-loss experiment; fault injection and static flow checks only.'
}
$json=$summary | ConvertTo-Json -Depth 5
[IO.File]::WriteAllText((Join-Path $fixtureRoot 'offline-results.json'),$json,[Text.UTF8Encoding]::new($false))
$json
