# Packaging only: execution requires separate confirmation of this file's SHA-256.
# Run the reviewed in-memory snapshot in an independent elevated Windows PowerShell.
# No self-elevation, retry, uninstall, cleanup, or Operator deployment.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Assert-769Signature([string] $Path) {
    $signature = Microsoft.PowerShell.Security\Get-AuthenticodeSignature -LiteralPath $Path
    if ($signature.Status -ne 'Valid' -or $null -eq $signature.SignerCertificate -or
        $signature.SignerCertificate.Subject -notmatch '(^|,\s*)O=Microsoft Corporation(,|$)') {
        throw 'SIGNATURE_INVALID'
    }
    return $signature
}

function Assert-769Conflicts {
    foreach ($key in @(
        'C:\Program Files\PowerShell\7',
        'HKLM:\SOFTWARE\Microsoft\PowerShellCore\InstalledVersions',
        'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Installer\InProgress',
        'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\pwsh.exe',
        'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths\pwsh.exe',
        'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\pwsh.exe',
        'HKCU:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths\pwsh.exe'
    )) {
        if (Test-Path -LiteralPath $key) { throw 'INSTALL_CONFLICT' }
    }
    foreach ($root in @(
        'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall',
        'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall',
        'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall'
    )) {
        if (Test-Path -LiteralPath $root) {
            foreach ($entry in Get-ChildItem -LiteralPath $root) {
                $item = Get-ItemProperty -LiteralPath $entry.PSPath
                if ($null -ne $item.PSObject.Properties['DisplayName'] -and
                    $item.DisplayName -match '^PowerShell(?:\s+7|\s+Core)') {
                    throw 'INSTALL_CONFLICT'
                }
            }
        }
    }
    if (@(Get-AppxPackage -Name '*PowerShell*').Count -gt 0) { throw 'INSTALL_CONFLICT' }
    $envKey = Get-Item -LiteralPath 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Environment'
    try {
        if ($envKey.GetValueNames() -contains 'POWERSHELL_DISTRIBUTION_CHANNEL') {
            throw 'DISTRIBUTION_CHANNEL_CONFLICT'
        }
    } finally { $envKey.Close() }
}

function Assert-769Paths([string] $Source) {
    $item = Get-Item -LiteralPath $Source -Force
    if ($item.PSIsContainer) { throw 'SOURCE_NOT_FILE' }
    while ($null -ne $item) {
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw 'REPARSE_PATH'
        }
        if ($item -is [IO.FileInfo]) { $item = $item.Directory }
        else { $item = $item.Parent }
    }
    $programFiles = Get-Item -LiteralPath 'C:\Program Files' -Force
    if (-not $programFiles.PSIsContainer -or
        ($programFiles.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw 'REPARSE_PATH'
    }
    if (Test-Path -LiteralPath 'C:\Program Files\PowerShell') {
        $parent = Get-Item -LiteralPath 'C:\Program Files\PowerShell' -Force
        if (-not $parent.PSIsContainer -or
            ($parent.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw 'REPARSE_PATH'
        }
    }
}

function Assert-769Bytes([IO.Stream] $Stream, [string] $Source, [string] $Expected) {
    if ($Stream.Length -ne 117493760) { throw 'MSI_SIZE_MISMATCH' }
    $Stream.Position = 0
    $sha = [Security.Cryptography.SHA256]::Create()
    try { $heldHash = ([BitConverter]::ToString($sha.ComputeHash($Stream))).Replace('-', '').ToLowerInvariant() }
    finally { $sha.Dispose() }
    $pathHash = (Microsoft.PowerShell.Utility\Get-FileHash -LiteralPath $Source -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($heldHash -cne $Expected -or $pathHash -cne $Expected) { throw 'MSI_HASH_MISMATCH' }
}

function Assert-769Host {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    try {
        $principal = [Security.Principal.WindowsPrincipal]::new($identity)
        if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
            throw 'ADMIN_REQUIRED'
        }
    } finally { $identity.Dispose() }
    $current = [Diagnostics.Process]::GetCurrentProcess()
    try { $image = $current.MainModule.FileName }
    finally { $current.Dispose() }
    if ($PSVersionTable.PSEdition -ne 'Desktop' -or -not [Environment]::Is64BitProcess -or
        $image -ine 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe') {
        throw 'INDEPENDENT_WINDOWS_POWERSHELL_REQUIRED'
    }
    # Job membership alone is not a gate for this separately approved direct MSI route.
}

function Assert-769SourceSignature([string] $Source) {
    $signature = Assert-769Signature $Source
    if ($null -eq $signature.TimeStamperCertificate) { throw 'TIMESTAMP_MISSING' }
    $chain = [Security.Cryptography.X509Certificates.X509Chain]::new()
    try {
        $chain.ChainPolicy.RevocationMode = [Security.Cryptography.X509Certificates.X509RevocationMode]::Online
        $chain.ChainPolicy.RevocationFlag = [Security.Cryptography.X509Certificates.X509RevocationFlag]::EntireChain
        $chain.ChainPolicy.UrlRetrievalTimeout = [TimeSpan]::FromSeconds(20)
        if (-not $chain.Build($signature.SignerCertificate)) { throw 'SIGNER_CHAIN_INVALID' }
    } finally { $chain.Dispose() }
}

function Invoke-769ApprovedInstall {
    $source = 'C:\Users\wuxia\AppData\Local\GDCAE-PowerShell-769-Qualification-20261031-A01\PowerShell-7.6.9-win-x64.msi'
    $expected = '50d33c7494aaf82b987cfd4de3f232d04f91fdd4c0deeca8a669cced3e7cf8f9'
    $installer = 'C:\Windows\System32\msiexec.exe'
    $stream = $null
    $intent = $false
    $receipt = [ordered]@{
        schema_version = 1
        status = 'BLOCKED_PREFLIGHT'
        exit_code = $null
        started_utc = $null
        finished_utc = $null
        source_sha256 = $expected
        source_recheck_passed = $false
        strong_same_user_isolation_claimed = $false
    }
    try {
        Assert-769Host
        Assert-769Conflicts
        Assert-769Paths $source
        $stream = [IO.File]::Open($source, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read)
        Assert-769Bytes $stream $source $expected
        Assert-769SourceSignature $source
        $null = Assert-769Signature $installer
        if ((Read-Host 'Confirm this one approved installation: type INSTALL_769_ONCE') -cne 'INSTALL_769_ONCE') {
            throw 'HUMAN_CONFIRMATION_REQUIRED'
        }
        Assert-769Conflicts
        Assert-769Paths $source
        Assert-769Bytes $stream $source $expected
        $arguments = '/i "' + $source + '" /qb /norestart INSTALLFOLDER="C:\Program Files\PowerShell" ADD_PATH=0 ADD_EXPLORER_CONTEXT_MENU_OPENPOWERSHELL=0 ADD_FILE_CONTEXT_MENU_RUNPOWERSHELL=0 ENABLE_PSREMOTING=0 REGISTER_MANIFEST=0 USE_MU=0 ENABLE_MU=0 DISABLE_TELEMETRY=0 LAUNCHAPPONEXIT=0 REBOOT=ReallySuppress'
        $receipt.started_utc = [DateTime]::UtcNow.ToString('o')
        $intent = $true
        $process = Start-Process -FilePath $installer -ArgumentList $arguments -Wait -PassThru
        try { $receipt.exit_code = $process.ExitCode }
        finally { if ($null -ne $process) { $process.Dispose() } }
        if ($null -eq $receipt.exit_code) { throw 'INSTALL_EXIT_UNKNOWN' }
        Assert-769Paths $source
        Assert-769Bytes $stream $source $expected
        $null = Assert-769Signature $source
        $receipt.source_recheck_passed = $true
        if ($receipt.exit_code -eq 0) { $receipt.status = 'INSTALLER_EXIT_0_PENDING_READONLY_VERIFICATION' }
        elseif ($receipt.exit_code -eq 3010) { $receipt.status = 'PENDING_REBOOT_STOP' }
        else { $receipt.status = 'INSTALLER_NONZERO_STOP' }
    } catch {
        if ($intent) { $receipt.status = 'UNKNOWN_INSTALL_STOP' }
        else { $receipt.status = 'BLOCKED_PREFLIGHT' }
        $message = $_.Exception.Message
        $allowed = @('SIGNATURE_INVALID', 'INSTALL_CONFLICT', 'DISTRIBUTION_CHANNEL_CONFLICT',
            'SOURCE_NOT_FILE', 'REPARSE_PATH', 'MSI_SIZE_MISMATCH', 'MSI_HASH_MISMATCH',
            'ADMIN_REQUIRED', 'INDEPENDENT_WINDOWS_POWERSHELL_REQUIRED', 'TIMESTAMP_MISSING',
            'SIGNER_CHAIN_INVALID', 'HUMAN_CONFIRMATION_REQUIRED', 'INSTALL_EXIT_UNKNOWN')
        $receipt.reason = if ($message -cin $allowed) { $message } else { 'CHECK_OR_INSTALL_EXCEPTION' }
        $receipt.error_type = $_.Exception.GetType().Name
    } finally {
        if ($null -ne $stream) {
            try { $stream.Dispose() }
            catch { $receipt.status = 'UNKNOWN_SOURCE_HANDLE_CLOSE'; $receipt.reason = 'SOURCE_HANDLE_CLOSE_FAILED' }
        }
        $receipt.finished_utc = [DateTime]::UtcNow.ToString('o')
    }
    # A terminated console or failed output can leave no receipt: UNKNOWN, never retry.
    # Exit 0 is NOT independent installation verification; retain the JSON for review.
    $receipt | ConvertTo-Json -Compress
}

Invoke-769ApprovedInstall
