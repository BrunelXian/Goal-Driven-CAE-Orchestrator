#requires -Version 5.1
# Run manually in an independent elevated Windows PowerShell console only.
# No installer execution, existing-object ACL changes, retries, or cleanup.
[CmdletBinding()]
param([Parameter(Mandatory=$true)][ValidatePattern('^[a-f0-9]{64}$')][string]$PinnedScriptSha256)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$stage = 'C:\ProgramData\GDCAE PowerShell Install 7.6.9'
$source = 'C:\Users\wuxia\AppData\Local\GDCAE-PowerShell-769-Qualification-20261031-A01\PowerShell-7.6.9-win-x64.msi'
$expectedHash = '50d33c7494aaf82b987cfd4de3f232d04f91fdd4c0deeca8a669cced3e7cf8f9'
$expectedSize = 117493760L
$adminSid = [Security.Principal.SecurityIdentifier]::new('S-1-5-32-544')
$systemSid = [Security.Principal.SecurityIdentifier]::new('S-1-5-18')
$created = $false
$secureStage = $false
$writeIntent = $false
$checksComplete = $false
$gate = 'INITIAL'
$locks = [Collections.Generic.List[IDisposable]]::new()
$receipt = [ordered]@{
    schema_version = 2
    attempt_id = [Guid]::NewGuid().ToString('N')
    operator_bootstrap_script_sha256 = $PinnedScriptSha256
    status = 'BLOCKED_NOT_STARTED'
    stage = $stage
    installer_started = $false
    existing_acl_changed = $false
    registry_or_environment_written = $false
    operator_deployment_started = $false
    retry_count = 0
    acceptance_requires_matching_final_console_status = $true
    host_in_job = 'UNKNOWN'
    workload_process_creation_authorized = $false
}

function Get-StagingFailureStatus([bool]$WriteIntent, [string]$Gate) {
    if ($WriteIntent) { return 'UNKNOWN_' + $Gate }
    return 'BLOCKED_' + $Gate
}

function Get-StaticJobObservation([bool]$QuerySucceeded, [bool]$InJob) {
    if (-not $QuerySucceeded) { throw 'JOB_QUERY_UNAVAILABLE' }
    # Both values are admissible for static operations only, not execution hosts.
    return $InJob
}

function Assert-StagingHostFacts($Facts) {
    if ($Facts.Edition -ne 'Desktop' -or [Version]$Facts.Version -lt [Version]'5.1' -or
        -not $Facts.Is64Bit -or -not $Facts.Interactive -or $Facts.LanguageMode -ne 'FullLanguage') {
        throw 'WINDOWS_POWERSHELL_REQUIRED'
    }
    if ($Facts.Path -ine 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe') { throw 'WRONG_HOST' }
    if ($Facts.Signature -ne 'Valid' -or $Facts.Signer -notmatch '(^|, )O=Microsoft Corporation(,|$)') {
        throw 'HOST_SIGNATURE'
    }
    if (-not $Facts.Admin) { throw 'ELEVATED_ADMIN_REQUIRED' }
    if ($Facts.Impersonated) { throw 'IMPERSONATION_NOT_ALLOWED' }
}

function Assert-StagingFileIdentity([long]$Size, [string]$Hash) {
    if ($Size -ne $expectedSize) { throw 'MSI_SIZE' }
    if ($Hash -cne $expectedHash) { throw 'MSI_HASH' }
}

function Assert-StagingSignatureFacts($Signature) {
    if ($Signature.Status -ne 'Valid' -or $null -eq $Signature.SignerCertificate -or
        $Signature.SignerCertificate.Subject -notmatch '(^|, )O=Microsoft Corporation(,|$)' -or
        $null -eq $Signature.TimeStamperCertificate) { throw 'SIGNATURE_GATE' }
}

function Assert-StagingRegistrationFacts([bool]$DistributionPresent, [bool]$AppPathPresent, [bool]$TargetPresent) {
    if ($DistributionPresent) { throw 'DISTRIBUTION_CHANNEL_ALREADY_PRESENT' }
    if ($AppPathPresent) { throw 'APP_PATH_ALREADY_PRESENT' }
    if ($TargetPresent) { throw 'INSTALL_TARGET_ALREADY_EXISTS' }
}

function Initialize-StagingNative {
    # In-process P/Invoke emission: no Add-Type/csc.exe or external compiler.
    $name = [Reflection.AssemblyName]::new('GDCAE769StaticInterop')
    $assembly = [AppDomain]::CurrentDomain.DefineDynamicAssembly($name,[Reflection.Emit.AssemblyBuilderAccess]::Run)
    $module = $assembly.DefineDynamicModule('Native')
    $builder = $module.DefineType('GDCAE769StaticNative',
        [Reflection.TypeAttributes]'Public,Abstract,Sealed')
    $definitions = @(
        @{Name='IsProcessInJob'; Return=[bool]; Args=[Type[]]@([IntPtr],[IntPtr],[bool].MakeByRefType())},
        @{Name='CreateFileW'; Return=[IntPtr]; Args=[Type[]]@([string],[uint32],[uint32],[IntPtr],[uint32],[uint32],[IntPtr])},
        @{Name='CreateDirectoryW'; Return=[bool]; Args=[Type[]]@([string],[IntPtr])}
    )
    $attributeType = [Runtime.InteropServices.DllImportAttribute]
    $constructor = $attributeType.GetConstructor([Type[]]@([string]))
    $fields = [Reflection.FieldInfo[]]@(
        $attributeType.GetField('EntryPoint'),$attributeType.GetField('CharSet'),
        $attributeType.GetField('SetLastError'),$attributeType.GetField('ExactSpelling'))
    foreach ($definition in $definitions) {
        $method = $builder.DefineMethod($definition.Name,
            [Reflection.MethodAttributes]'Public,Static,PinvokeImpl',$definition.Return,$definition.Args)
        $attribute = [Reflection.Emit.CustomAttributeBuilder]::new($constructor,[object[]]@('kernel32.dll'),
            $fields,[object[]]@($definition.Name,[Runtime.InteropServices.CharSet]::Unicode,$true,$true))
        $method.SetCustomAttribute($attribute)
        $method.SetImplementationFlags([Reflection.MethodImplAttributes]::PreserveSig)
    }
    return $builder.CreateType()
}

function Open-StagingDirectoryHandle([Type]$Native, [string]$Path) {
    $handle = $Native::CreateFileW($Path,0x20080,3,[IntPtr]::Zero,3,0x02200000,[IntPtr]::Zero)
    $errorCode = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
    if ($handle -eq [IntPtr](-1)) { throw [ComponentModel.Win32Exception]::new($errorCode) }
    return [Microsoft.Win32.SafeHandles.SafeFileHandle]::new($handle,$true)
}

function New-StagingDirectoryAtomic([Type]$Native, [string]$Path, [byte[]]$Descriptor) {
    # x64 SECURITY_ATTRIBUTES: DWORD at 0, pointer at 8, BOOL at 16, size 24.
    $pin = [Runtime.InteropServices.GCHandle]::Alloc($Descriptor,[Runtime.InteropServices.GCHandleType]::Pinned)
    $attributes = [IntPtr]::Zero
    try {
        $attributes = [Runtime.InteropServices.Marshal]::AllocHGlobal(24)
        [Runtime.InteropServices.Marshal]::Copy([byte[]]::new(24),0,$attributes,24)
        [Runtime.InteropServices.Marshal]::WriteInt32($attributes,0,24)
        [Runtime.InteropServices.Marshal]::WriteIntPtr($attributes,8,$pin.AddrOfPinnedObject())
        if (-not $Native::CreateDirectoryW($Path,$attributes)) {
            throw [ComponentModel.Win32Exception]::new([Runtime.InteropServices.Marshal]::GetLastWin32Error())
        }
    } finally {
        if ($attributes -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::FreeHGlobal($attributes) }
        $pin.Free()
    }
}

function Write-StagingRecord([string]$Path, $Record) {
    $stream = New-PrivateFile $Path
    try {
        Assert-ExactSecurity $Path $false
        $bytes = [Text.UTF8Encoding]::new($false).GetBytes(($Record | ConvertTo-Json -Depth 6))
        $stream.Write($bytes,0,$bytes.Length)
        $stream.Flush($true)
    } finally { $stream.Dispose() }
    Assert-ExactSecurity $Path $false
    $readback = [IO.File]::ReadAllBytes($Path)
    $hash = [Security.Cryptography.SHA256]::Create()
    try {
        $expected = [BitConverter]::ToString($hash.ComputeHash($bytes))
        $actual = [BitConverter]::ToString($hash.ComputeHash($readback))
    } finally { $hash.Dispose() }
    if ($actual -cne $expected) { throw 'RECORD_READBACK_MISMATCH' }
    return $actual.Replace('-','').ToLowerInvariant()
}

function Assert-PlainPath([string]$Path) {
    $item = Get-Item -LiteralPath $Path -Force
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'REPARSE_POINT' }
}

function Assert-Ancestor([string]$Path, [string[]]$TrustedOwners) {
    Assert-PlainPath $Path
    if (-not (Get-Item -LiteralPath $Path -Force).PSIsContainer) { throw 'NOT_DIRECTORY' }
    $acl = Get-Acl -LiteralPath $Path
    if ($acl.GetOwner([Security.Principal.SecurityIdentifier]).Value -notin $TrustedOwners) {
        throw 'UNTRUSTED_ANCESTOR_OWNER'
    }
    $raw = [Security.AccessControl.RawSecurityDescriptor]::new($acl.GetSecurityDescriptorBinaryForm(),0)
    if ($null -eq $raw.DiscretionaryAcl -or $raw.DiscretionaryAcl.Count -eq 0) {
        throw 'UNQUALIFIED_ANCESTOR_DACL'
    }
    # Creating siblings is not permission to replace this protected child.
    # Reject effective nontrusted Allow ACEs enabling replacement or ACL mutation.
    $danger = 0x10000 -bor 0x40 -bor 0x40000 -bor 0x80000 -bor 0x100 -bor 0x10
    foreach ($ace in $raw.DiscretionaryAcl) {
        if (([int]$ace.AceFlags -band [int][Security.AccessControl.AceFlags]::InheritOnly) -ne 0) { continue }
        if ($ace -isnot [Security.AccessControl.CommonAce] -or $ace.IsCallback) {
            throw 'UNSUPPORTED_ANCESTOR_ACE'
        }
        if ($ace.AceQualifier -eq [Security.AccessControl.AceQualifier]::AccessAllowed -and
            $ace.SecurityIdentifier.Value -notin $TrustedOwners -and
            (($ace.AccessMask -band $danger) -ne 0 -or
             ($ace.AccessMask -band 0x10000000) -ne 0 -or
             ($ace.AccessMask -band 0x40000000) -ne 0)) {
            throw 'UNTRUSTED_ANCESTOR_MUTATION_RIGHTS'
        }
    }
}

function Assert-ExactSecurity([string]$Path, [bool]$Directory) {
    Assert-PlainPath $Path
    $acl = Get-Acl -LiteralPath $Path
    if ($acl.GetOwner([Security.Principal.SecurityIdentifier]).Value -ne $adminSid.Value -or
        -not $acl.AreAccessRulesProtected) { throw 'SECURITY_OWNER_OR_INHERITANCE' }
    $rules = @($acl.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier]))
    if ($rules.Count -ne 2) { throw 'SECURITY_RULE_COUNT' }
    $seen = @()
    foreach ($rule in $rules) {
        if ($rule.IdentityReference.Value -notin @($adminSid.Value,$systemSid.Value) -or
            $rule.AccessControlType -ne [Security.AccessControl.AccessControlType]::Allow -or
            $rule.FileSystemRights -ne [Security.AccessControl.FileSystemRights]::FullControl -or
            $rule.IsInherited -or
            $rule.PropagationFlags -ne [Security.AccessControl.PropagationFlags]::None) {
            throw 'SECURITY_UNEXPECTED_RULE'
        }
        $expectedInheritance = [Security.AccessControl.InheritanceFlags]::None
        if ($Directory) {
            $expectedInheritance = [Security.AccessControl.InheritanceFlags]::ContainerInherit -bor
                [Security.AccessControl.InheritanceFlags]::ObjectInherit
        }
        if ($rule.InheritanceFlags -ne $expectedInheritance) { throw 'SECURITY_INHERITANCE_FLAGS' }
        $seen += $rule.IdentityReference.Value
    }
    if (@($seen | Select-Object -Unique).Count -ne 2) { throw 'SECURITY_DUPLICATE_PRINCIPAL' }
}

function Get-ApprovedSignature([string]$Path) {
    $sig = Get-AuthenticodeSignature -LiteralPath $Path
    Assert-StagingSignatureFacts $sig
    $chain = [Security.Cryptography.X509Certificates.X509Chain]::new()
    try {
        $chain.ChainPolicy.RevocationMode = [Security.Cryptography.X509Certificates.X509RevocationMode]::Online
        $chain.ChainPolicy.RevocationFlag = [Security.Cryptography.X509Certificates.X509RevocationFlag]::ExcludeRoot
        $chain.ChainPolicy.VerificationFlags = [Security.Cryptography.X509Certificates.X509VerificationFlags]::NoFlag
        $chain.ChainPolicy.UrlRetrievalTimeout = [TimeSpan]::FromSeconds(20)
        if (-not $chain.Build($sig.SignerCertificate)) { throw 'CERTIFICATE_CHAIN_GATE' }
    } finally { $chain.Dispose() }
    return [ordered]@{
        authenticode = 'Valid'
        microsoft_publisher = $true
        signer_thumbprint = $sig.SignerCertificate.Thumbprint
        online_signer_chain_valid = $true
        timestamp_present = $true
    }
}

function Assert-NoRegistrationConflict {
    $distributionPresent = $false
    $appPathPresent = $false
    $environmentKey = [Microsoft.Win32.Registry]::LocalMachine.OpenSubKey(
        'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',$false)
    if ($null -eq $environmentKey) { throw 'MACHINE_ENVIRONMENT_UNREADABLE' }
    try {
        $distributionPresent = $environmentKey.GetValueNames() -contains 'POWERSHELL_DISTRIBUTION_CHANNEL'
    } finally { $environmentKey.Dispose() }
    foreach ($hive in @([Microsoft.Win32.RegistryHive]::LocalMachine,[Microsoft.Win32.RegistryHive]::CurrentUser)) {
        foreach ($view in @([Microsoft.Win32.RegistryView]::Registry64,[Microsoft.Win32.RegistryView]::Registry32)) {
            $base = [Microsoft.Win32.RegistryKey]::OpenBaseKey($hive,$view)
            try {
                $key = $base.OpenSubKey('Software\Microsoft\Windows\CurrentVersion\App Paths\pwsh.exe',$false)
                if ($null -ne $key) {
                    $key.Dispose()
                    $appPathPresent = $true
                }
            } finally { $base.Dispose() }
        }
    }
    Assert-StagingRegistrationFacts $distributionPresent $appPathPresent `
        (Test-Path -LiteralPath 'C:\Program Files\PowerShell\7')
}

function New-PrivateFile([string]$Path) {
    $security = [Security.AccessControl.FileSecurity]::new()
    $security.SetSecurityDescriptorSddlForm('O:BAG:BAD:P(A;;FA;;;SY)(A;;FA;;;BA)')
    return [IO.FileStream]::new($Path,[IO.FileMode]::CreateNew,
        [Security.AccessControl.FileSystemRights]::FullControl,[IO.FileShare]::None,
        65536,[IO.FileOptions]::None,$security)
}

try {
    $gate = 'INDEPENDENT_ADMIN_HOST'
    $processPath = [Diagnostics.Process]::GetCurrentProcess().MainModule.FileName
    $hostSignature = Get-AuthenticodeSignature -LiteralPath $processPath
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    try {
        $principal = [Security.Principal.WindowsPrincipal]::new($identity)
        $isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    } finally { $identity.Dispose() }
    $impersonated = [Security.Principal.WindowsIdentity]::GetCurrent($true)
    $isImpersonated = $null -ne $impersonated
    if ($isImpersonated) { $impersonated.Dispose() }
    Assert-StagingHostFacts @{
        Edition=$PSVersionTable.PSEdition; Version=$PSVersionTable.PSVersion
        Is64Bit=[Environment]::Is64BitProcess; Interactive=[Environment]::UserInteractive
        LanguageMode=[string]$ExecutionContext.SessionState.LanguageMode
        Path=$processPath; Signature=[string]$hostSignature.Status
        Signer=$hostSignature.SignerCertificate.Subject; Admin=$isAdmin; Impersonated=$isImpersonated
    }

    $native = Initialize-StagingNative
    $gate = 'JOB_OBSERVATION'
    $inJob = $false
    $querySucceeded = $native::IsProcessInJob([IntPtr](-1),[IntPtr]::Zero,[ref]$inJob)
    $receipt.host_in_job = Get-StaticJobObservation $querySucceeded $inJob
    $receipt.elevated_system_windows_powershell_observed = $true
    $receipt.launch_provenance = 'OPERATOR_CONFIRMATION_REQUIRED_NOT_INFERRED_FROM_JOB'

    $gate = 'ANCESTORS_AND_ABSENT_TARGET'
    $volume = [IO.DriveInfo]::new('C:\')
    if ($volume.DriveFormat -ne 'NTFS' -or $volume.DriveType -ne [IO.DriveType]::Fixed) {
        throw 'LOCAL_NTFS_REQUIRED'
    }
    $trustedInstaller = [Security.Principal.NTAccount]::new('NT SERVICE','TrustedInstaller').Translate(
        [Security.Principal.SecurityIdentifier]).Value
    $trusted = @($adminSid.Value,$systemSid.Value,$trustedInstaller)
    foreach ($path in @('C:\','C:\ProgramData')) {
        $locks.Add((Open-StagingDirectoryHandle $native $path))
        Assert-Ancestor $path $trusted
    }
    if (Test-Path -LiteralPath $stage) { throw 'TARGET_ALREADY_EXISTS' }

    $gate = 'REGISTRATION_CONFLICT'
    Assert-NoRegistrationConflict
    $receipt.distribution_channel_absent = $true
    $receipt.app_paths_absent_both_views = $true

    $gate = 'SOURCE_INTEGRITY'
    Assert-PlainPath $source
    $inputStream = [IO.File]::Open($source,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
    $locks.Add($inputStream)
    if ($inputStream.Length -ne $expectedSize) { throw 'SOURCE_SIZE' }
    $hasher = [Security.Cryptography.SHA256]::Create()
    try { $hash = [BitConverter]::ToString($hasher.ComputeHash($inputStream)).Replace('-','').ToLowerInvariant() }
    finally { $hasher.Dispose() }
    Assert-StagingFileIdentity $inputStream.Length $hash
    $null = Get-ApprovedSignature $source
    $inputStream.Position = 0

    $gate = 'OPERATOR_CONFIRMATION'
    Write-Host 'Confirm this console was opened manually outside Codex. Staging only, no installer or workload process launch.'
    if ((Read-Host 'Type STAGE_769_ONCE to confirm') -cne 'STAGE_769_ONCE') { throw 'CONFIRMATION_NOT_GIVEN' }
    $receipt.launch_provenance = 'OPERATOR_CONFIRMED_OUTSIDE_CODEX_NOT_OS_ATTESTED'
    Assert-NoRegistrationConflict
    foreach ($path in @('C:\','C:\ProgramData')) { Assert-Ancestor $path $trusted }

    $gate = 'ATOMIC_PROTECTED_DIRECTORY_CREATION'
    $security = [Security.AccessControl.DirectorySecurity]::new()
    $security.SetSecurityDescriptorSddlForm('O:BAG:BAD:P(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)')
    # From this point onward, failure may have left a directory or partial file.
    # Hard process termination can prevent every catch/finally/receipt operation.
    $writeIntent = $true
    New-StagingDirectoryAtomic $native $stage $security.GetSecurityDescriptorBinaryForm()
    $created = $true
    $locks.Add((Open-StagingDirectoryHandle $native $stage))
    Assert-ExactSecurity $stage $true
    $secureStage = $true

    $gate = 'INTENT_PERSISTENCE'
    $intent = [ordered]@{
        schema_version=2; attempt_id=$receipt.attempt_id; status='UNKNOWN_UNCOMPLETED_ATTEMPT'
        script_sha256=$PinnedScriptSha256; approved_msi_sha256=$expectedHash
        rule='No final matching verified console result means UNKNOWN; never retry or clean up.'
    }
    $null = Write-StagingRecord (Join-Path $stage 'STAGING_INTENT.safe.json') $intent

    $gate = 'COPY_AND_DESTINATION_INTEGRITY'
    $destination = Join-Path $stage 'PowerShell-7.6.9-win-x64.msi'
    $outputStream = New-PrivateFile $destination
    try { $inputStream.CopyTo($outputStream); $outputStream.Flush($true) }
    finally { $outputStream.Dispose() }
    Assert-ExactSecurity $destination $false
    $destinationLock = [IO.File]::Open($destination,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
    $locks.Add($destinationLock)
    $actualHash = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant()
    Assert-StagingFileIdentity $destinationLock.Length $actualHash
    $receipt.signature = Get-ApprovedSignature $destination

    $gate = 'FINAL_READONLY_RECHECK'
    Assert-NoRegistrationConflict
    foreach ($path in @('C:\','C:\ProgramData')) { Assert-Ancestor $path $trusted }
    Assert-ExactSecurity $stage $true
    Assert-ExactSecurity $destination $false
    $receipt.msi = $destination
    $receipt.bytes = $expectedSize
    $receipt.sha256 = $actualHash
    $receipt.owner_builtin_administrators = $true
    $receipt.protected_dacl_only_administrators_system_full_control = $true
    $receipt.ancestors_checked_and_held_against_rename = $true
    $receipt.permission_evidence = 'Exact SID-based DACL and ancestor replacement-right checks; no impersonated-user write probe or all-account security guarantee.'
    $checksComplete = $true
    $receipt.status = 'STAGING_CHECKS_COMPLETE_PENDING_FINAL_CONSOLE'
} catch {
    $checksComplete = $false
    $receipt.status = Get-StagingFailureStatus $writeIntent $gate
    $receipt.exception_type = $_.Exception.GetType().FullName
    # Only script-defined uppercase gate reasons are permitted in public output.
    $reason = [string]$_.Exception.Message
    if ($reason -cmatch '^[A-Z][A-Z0-9_]{1,80}$') { $receipt.reason = $reason }
    $receipt.target_created_this_attempt = $created
    $receipt.no_retry_or_cleanup = $true
} finally {
    $receipt.utc = [DateTime]::UtcNow.ToString('o')
    if ($secureStage) {
        $receiptPath = Join-Path $stage 'POWERSHELL7_STAGING_RECEIPT.safe.json'
        $receipt.receipt_path = $receiptPath
        try {
            Assert-ExactSecurity $stage $true
            $receiptHash = Write-StagingRecord $receiptPath $receipt
            $receipt.receipt_sha256 = $receiptHash
            $receipt.receipt_persistence_confirmed = $true
            if ($checksComplete -and $receipt.status -ceq 'STAGING_CHECKS_COMPLETE_PENDING_FINAL_CONSOLE') {
                $receipt.status = 'POWERSHELL7_STAGING_VERIFIED'
            }
        } catch {
            $receipt.status = 'UNKNOWN_RECEIPT_PERSISTENCE'
            $receipt.receipt_persistence_confirmed = $false
        }
    }
    for ($i=$locks.Count-1; $i -ge 0; $i--) {
        try { $locks[$i].Dispose() }
        catch { $receipt.status = Get-StagingFailureStatus $writeIntent 'HANDLE_RELEASE' }
    }
    $receipt | ConvertTo-Json -Depth 6
}
