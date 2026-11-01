# Shared, inert definitions. Importing this file never changes accounts or ACLs.
Set-StrictMode -Version Latest

function Hash-Bytes([byte[]]$Bytes) {
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($Bytes)).ToLowerInvariant()
}
function Assert-NoReparse([string]$Path) {
    $node = [IO.Path]::GetFullPath($Path)
    while ($node) {
        if (Test-Path -LiteralPath $node) {
            if ((Get-Item -LiteralPath $node -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'REPARSE_REJECTED' }
        }
        $node = [IO.Path]::GetDirectoryName($node)
    }
}
function Get-HostPin {
    $key = [Microsoft.Win32.RegistryKey]::OpenBaseKey([Microsoft.Win32.RegistryHive]::LocalMachine,[Microsoft.Win32.RegistryView]::Registry64)
    try {
        $sub = $key.OpenSubKey('SOFTWARE\Microsoft\Cryptography',$false)
        try { return Hash-Bytes ([Text.Encoding]::UTF8.GetBytes([string]$sub.GetValue('MachineGuid'))) }
        finally { $sub.Dispose() }
    } finally { $key.Dispose() }
}
function Assert-ExactKeys($Value, [string[]]$Keys) {
    if ((($Value.Keys | Sort-Object) -join ',') -cne (($Keys | Sort-Object) -join ',')) { throw 'UNEXPECTED_FIELDS' }
}
function Read-OperatorPlan([string]$Path,[string]$Approved,[bool]$Apply) {
    if (-not $IsWindows -or -not [Environment]::Is64BitProcess) { throw 'WINDOWS_X64_REQUIRED' }
    Assert-NoReparse $Path
    if ((Get-Item -LiteralPath $Path).Length -gt 8388608) { throw 'BOUNDED_PLAN_REQUIRED' }
    $raw = [IO.File]::ReadAllBytes([IO.Path]::GetFullPath($Path))
    $script:PlanHash = Hash-Bytes $raw
    if ($Apply -and ($Approved -cnotmatch '^[a-f0-9]{64}$' -or $Approved -cne $script:PlanHash)) { throw 'EXACT_PLAN_APPROVAL_REQUIRED' }
    $plan = [Text.Encoding]::UTF8.GetString($raw) | ConvertFrom-Json -AsHashtable
    Assert-ExactKeys $plan @('schema','scope','host_sha256','original_agent_sid','accounts','code_root','state_root','staging_root','directories','source_files','scripts','activation_blockers','create_service','create_project','create_capability','start_owner','issue_grant','execute_solver','research_identity_requirement','rollback')
    if ($plan.schema -cne 'gdcae-operator-foundation-v1' -or $plan.scope -cne 'FOUNDATION_ONLY_NO_ACTIVATION' -or
        $plan.code_root -cne 'C:/Program Files/GDCAE Operator' -or $plan.state_root -cne 'C:/ProgramData/GDCAE Operator' -or
        $plan.staging_root -cne 'C:/ProgramData/GDCAE Operator Preparation' -or
        ($plan.accounts -join ',') -cne 'GDCAEResearch,GDCAEIssuer' -or
        ($plan.directories -join ',') -cne 'config,projects,audit,review,deployment' -or
        ($plan.activation_blockers -join ',') -cne 'FIXED_INTERPRETER_OUTSIDE_CODE_ROOT,RUNTIME_NOT_LOAD_QUALIFIED,PROTECTED_OPERATOR_CONSOLE_NOT_IMPLEMENTED,CROSS_SID_EVIDENCE_NOT_QUALIFIED,CUSTODY_ACE_INHERIT_ONLY_UNRECONCILED' -or
        $plan.research_identity_requirement -cne 'ACTUAL_CODEX_TOOL_TOKEN_MUST_EQUAL_NEW_RESEARCH_SID' -or
        $plan.rollback -cne 'DISABLE_ONLY_EXACT_CREATED_ACCOUNTS_PRESERVE_ALL_FILES' -or
        $plan.original_agent_sid -cnotmatch '^S-1-5-21-(?:[0-9]+-){3}[0-9]+$') { throw 'UNREVIEWED_SCOPE' }
    foreach ($name in @('create_service','create_project','create_capability','start_owner','issue_grant','execute_solver')) {
        if ($plan[$name] -isnot [bool] -or $plan[$name] -ne $false) { throw 'AUTHORITY_EXPANSION_REJECTED' }
    }
    if ($plan.host_sha256 -cne (Get-HostPin)) { throw 'WRONG_HOST' }
    Assert-ExactKeys $plan.scripts @('Deploy-Operator.ps1','Undo-Operator.ps1','Operator.Common.ps1','identity_probe.py','audit.py')
    foreach ($name in $plan.scripts.Keys) {
        $scriptFile = Join-Path $PSScriptRoot $name
        Assert-NoReparse $scriptFile
        if ((Get-FileHash -LiteralPath $scriptFile -Algorithm SHA256).Hash.ToLowerInvariant() -cne $plan.scripts[$name]) { throw 'SCRIPT_CHANGED' }
    }
    return $plan
}
function Assert-ParentSecurity([string]$Root) {
    # Same narrow parent replacement threat as AF custody: no existing ACL changes.
    $parent = [IO.Path]::GetDirectoryName([IO.Path]::GetFullPath($Root))
    $installer = ([Security.Principal.NTAccount]'NT SERVICE\TrustedInstaller').Translate([Security.Principal.SecurityIdentifier]).Value
    $trusted = @('S-1-5-18','S-1-5-32-544',$installer)
    while ($parent) {
        Assert-NoReparse $parent
        $acl = Get-Acl -LiteralPath $parent
        if ($acl.Owner -eq $null) { throw 'PARENT_OWNER_UNKNOWN' }
        $owner = ([Security.Principal.NTAccount]$acl.Owner).Translate([Security.Principal.SecurityIdentifier]).Value
        if ($owner -notin $trusted) { throw 'UNTRUSTED_PARENT_OWNER' }
        foreach ($rule in $acl.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier])) {
            # INHERIT_ONLY does not grant access to this ancestor; new roots are
            # created with protected DACLs and do not inherit these child rules.
            if ($rule.PropagationFlags -band [Security.AccessControl.PropagationFlags]::InheritOnly) { continue }
            if ($rule.AccessControlType -eq 'Allow' -and ([long]$rule.FileSystemRights -band 0x500D0040) -and $rule.IdentityReference.Value -notin $trusted) { throw 'UNTRUSTED_PARENT_REPLACEMENT_RIGHT' }
        }
        $parent = [IO.Path]::GetDirectoryName($parent)
    }
}
function Assert-NewDeployment($Plan) {
    foreach ($name in $Plan.accounts) {
        # Exact local names only; an unexpected lookup failure is not absence.
        try { $existing = Get-LocalUser -Name $name -ErrorAction Stop }
        catch [Microsoft.PowerShell.Commands.UserNotFoundException] { $existing = $null }
        if ($null -ne $existing) { throw 'ACCOUNT_NAME_CONFLICT' }
    }
    foreach ($root in @($Plan.code_root,$Plan.state_root)) {
        Assert-NoReparse $root
        if (Test-Path -LiteralPath $root) { throw 'EXISTING_ROOT_NO_ADOPTION' }
        Assert-ParentSecurity $root
    }
}
function Assert-Sources($Plan) {
    if ($Plan.source_files.Count -lt 1 -or $Plan.source_files.Count -gt 20000) { throw 'INVENTORY_BOUND' }
    $seen = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    [long]$total = 0
    foreach ($item in $Plan.source_files) {
        Assert-ExactKeys $item @('source','destination','size','sha256')
        if ($item.destination -cnotmatch '^[A-Za-z0-9_./-]+$' -or $item.destination.StartsWith('/') -or
            $item.destination -match '(^|/)(\.|\.\.|)(/|$)' -or
            [IO.Path]::GetExtension($item.destination).ToLowerInvariant() -notin @('.py','.pyd','.dll','.exe') -or
            -not $seen.Add($item.destination) -or $item.sha256 -cnotmatch '^[a-f0-9]{64}$') { throw 'UNSAFE_FILE_RECORD' }
        foreach ($part in $item.destination.Split('/')) {
            if ($part.EndsWith('.') -or $part -match '^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\.|$)') { throw 'WINDOWS_RESERVED_NAME' }
        }
        if ($item.size -isnot [long] -and $item.size -isnot [int]) { throw 'INTEGER_SIZE_REQUIRED' }
        if ($item.size -lt 0 -or $item.size -gt 67108864) { throw 'FILE_BOUND' }
        $total += $item.size
        if ($total -gt 1073741824) { throw 'TOTAL_BOUND' }
        Assert-NoReparse $item.source
        $file = Get-Item -LiteralPath $item.source
        if ($file.PSIsContainer -or $file.Length -ne $item.size -or (Get-FileHash -LiteralPath $item.source -Algorithm SHA256).Hash.ToLowerInvariant() -cne $item.sha256) { throw 'SOURCE_CHANGED' }
    }
}
function Initialize-ReadOnlyNative {
    if (-not ('GDCAE.FoundationNative' -as [type])) {
        Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
namespace GDCAE {
  public static class FoundationNative {
    [StructLayout(LayoutKind.Sequential)] public struct SA { public int nLength; public IntPtr descriptor; public int inherit; }
    [DllImport("kernel32.dll")] public static extern IntPtr GetCurrentProcess();
    [DllImport("kernel32.dll", SetLastError=true)] [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool IsProcessInJob(IntPtr process, IntPtr job, out bool result);
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)] [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool CreateDirectoryW(string path, ref SA security);
  }
}
'@
    }
}
function Assert-IndependentAdmin([string]$Actual,[string]$Expected) {
    if ($Actual -cne $Expected) { throw 'EXPLICIT_HUMAN_APPROVAL_REQUIRED' }
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    try {
        $principal = [Security.Principal.WindowsPrincipal]::new($identity)
        if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator) -or
            $identity.ImpersonationLevel -ne [Security.Principal.TokenImpersonationLevel]::None) { throw 'ELEVATED_UNIMPERSONATED_ADMIN_REQUIRED' }
    } finally { $identity.Dispose() }
    Initialize-ReadOnlyNative
    $inJob = $false
    if (-not [GDCAE.FoundationNative]::IsProcessInJob([GDCAE.FoundationNative]::GetCurrentProcess(),[IntPtr]::Zero,[ref]$inJob) -or $inJob) { throw 'INDEPENDENT_CONSOLE_NO_JOB_REQUIRED' }
}
function New-ExactSecurity([hashtable]$Extra) {
    $acl = [Security.AccessControl.DirectorySecurity]::new()
    $acl.SetAccessRuleProtection($true,$false)
    $acl.SetOwner([Security.Principal.SecurityIdentifier]::new('S-1-5-32-544'))
    $rights = @{'S-1-5-18'='FullControl'; 'S-1-5-32-544'='FullControl'}
    foreach ($key in $Extra.Keys) { $rights[$key] = $Extra[$key] }
    foreach ($sid in $rights.Keys) {
        $rule = [Security.AccessControl.FileSystemAccessRule]::new([Security.Principal.SecurityIdentifier]::new($sid),
            [Security.AccessControl.FileSystemRights]$rights[$sid],
            [Security.AccessControl.InheritanceFlags]'ContainerInherit,ObjectInherit',
            [Security.AccessControl.PropagationFlags]::None,[Security.AccessControl.AccessControlType]::Allow)
        $acl.AddAccessRule($rule)
    }
    return $acl
}
function New-ProtectedDirectory([string]$Path,[hashtable]$Extra) {
    Initialize-ReadOnlyNative
    Assert-NoReparse $Path
    if (Test-Path -LiteralPath $Path) { throw 'EXISTING_DIRECTORY_NO_ADOPTION' }
    $bytes = (New-ExactSecurity $Extra).GetSecurityDescriptorBinaryForm()
    $memory = [Runtime.InteropServices.Marshal]::AllocHGlobal($bytes.Length)
    try {
        [Runtime.InteropServices.Marshal]::Copy($bytes,0,$memory,$bytes.Length)
        $sa = [GDCAE.FoundationNative+SA]::new()
        $sa.nLength = [Runtime.InteropServices.Marshal]::SizeOf($sa); $sa.descriptor=$memory; $sa.inherit=0
        if (-not [GDCAE.FoundationNative]::CreateDirectoryW([IO.Path]::GetFullPath($Path),[ref]$sa)) { throw 'ATOMIC_DIRECTORY_CREATE_FAILED' }
    } finally { [Runtime.InteropServices.Marshal]::FreeHGlobal($memory) }
}
function Set-NewRootSecurity([string]$Path,[hashtable]$Extra) {
    # Caller only passes the state root created in this invocation, never ancestors.
    Assert-NoReparse $Path
    Set-Acl -LiteralPath $Path -AclObject (New-ExactSecurity $Extra) -ErrorAction Stop
}
function Copy-PinnedFile([string]$Code,$Item,[hashtable]$Rights) {
    $target = [IO.Path]::GetFullPath((Join-Path $Code $Item.destination))
    $prefix = [IO.Path]::GetFullPath($Code).TrimEnd('\') + '\'
    if (-not $target.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase)) { throw 'PATH_ESCAPE' }
    Assert-NoReparse $Item.source
    $input = [IO.File]::Open($Item.source,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
    try {
        if ($input.Length -ne $Item.size) { throw 'SOURCE_SIZE_CHANGED' }
        $content = [byte[]]::new([int]$input.Length); $input.ReadExactly($content)
        if ((Hash-Bytes $content) -cne $Item.sha256) { throw 'LOCKED_SOURCE_HASH_CHANGED' }
        $relativeParents = [IO.Path]::GetDirectoryName($Item.destination).Replace('\','/')
        $current = $Code
        if ($relativeParents) {
            foreach ($part in $relativeParents.Split('/')) {
                $current = Join-Path $current $part
                Assert-NoReparse $current
                if (-not (Test-Path -LiteralPath $current)) { New-ProtectedDirectory $current $Rights }
            }
        }
        Assert-NoReparse $target
        $output = [IO.FileStream]::new($target,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
        try { $output.Write($content); $output.Flush($true) } finally { $output.Dispose() }
    } finally { $input.Dispose() }
}
function Write-Receipt([string]$Path,$Receipt) {
    Assert-NoReparse $Path
    $temporary = $Path + '.new'
    $bytes = [Text.Encoding]::UTF8.GetBytes(($Receipt | ConvertTo-Json -Depth 10 -Compress))
    $stream = [IO.FileStream]::new($temporary,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
    try { $stream.Write($bytes); $stream.Flush($true) } finally { $stream.Dispose() }
    [IO.File]::Move($temporary,$Path,$true)
}
