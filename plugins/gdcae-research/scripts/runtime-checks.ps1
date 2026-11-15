function Assert-LocalTreePath([string]$Path) {
    if ($Path -notmatch '^[A-Za-z]:\\' -or [IO.Path]::GetFullPath($Path) -ne $Path) { throw 'LOCAL_PATH_REQUIRED' }
    for ($p=$Path; $p; $p=[IO.Path]::GetDirectoryName($p)) {
        if (Test-Path -LiteralPath $p) {
            $attr=(Get-Item -LiteralPath $p -Force).Attributes
            if ($attr -band [IO.FileAttributes]::ReparsePoint) { throw 'REPARSE_POINT_DENIED' }
        }
    }
}
function Get-RuntimeParent {
    Assert-LocalTreePath $env:LOCALAPPDATA
    return (Join-Path $env:LOCALAPPDATA 'GDCAE\runtimes')
}
function Assert-RuntimeTree([string]$Root, $Spec) {
    Assert-LocalTreePath $Root
    $list=@(Get-ChildItem -LiteralPath $Root -Force -ErrorAction Stop)
    if ($list.Count -ne @($Spec.files.PSObject.Properties).Count) { throw 'RUNTIME_FILESET_MISMATCH' }
    foreach ($f in $list) {
        $expected=$Spec.files.PSObject.Properties[$f.Name]
        if (!$expected -or $f.Name -cne $expected.Name -or $f.PSIsContainer -or
            ($f.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'RUNTIME_FILESET_MISMATCH' }
        if ($f.Length -ne $expected.Value.size -or
            (Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash -ne $expected.Value.sha256) {
            throw ('RUNTIME_MEMBER_MISMATCH:'+ $f.Name)
        }
    }
}
function Assert-RuntimeSpace([long]$Available,$Spec) {
    if ($Available -lt ($Spec.archive_bytes+$Spec.expanded_bytes+8MB)) { throw 'INSUFFICIENT_DISK_SPACE' }
}
function Receive-RuntimeArchive($Spec,[string]$Destination) {
    $request=[Net.HttpWebRequest]::Create([uri]$Spec.url)
    $request.AllowAutoRedirect=$false
    $request.Timeout=180000
    $request.ReadWriteTimeout=60000
    $response=$request.GetResponse()
    try {
        if ($response.ResponseUri.AbsoluteUri -cne $Spec.url) { throw 'UNEXPECTED_HTTP_RESPONSE' }
        if ([int]$response.StatusCode -in 301,302,303,307,308) {
            $next=[uri]$response.Headers['Location']
            if ($request.RequestUri.Host -cne 'github.com' -or !$next.IsAbsoluteUri -or
                $next.Scheme -cne 'https' -or $next.Host -cne 'release-assets.githubusercontent.com' -or
                !$next.IsDefaultPort -or $next.UserInfo -or $next.Fragment -or
                !$next.AbsolutePath.StartsWith('/github-production-release-asset/1312887420/')) { throw 'UNEXPECTED_HTTP_RESPONSE' }
            $response.Dispose()
            $delivery=[Net.HttpWebRequest]::Create($next)
            $delivery.AllowAutoRedirect=$false
            $delivery.Timeout=$request.Timeout
            $delivery.ReadWriteTimeout=$request.ReadWriteTimeout
            $response=$delivery.GetResponse()
        }
        if ([int]$response.StatusCode -ne 200) { throw 'UNEXPECTED_HTTP_RESPONSE' }
        if ($response.ContentLength -gt 0 -and $response.ContentLength -ne $Spec.archive_bytes) { throw 'DOWNLOAD_SIZE_MISMATCH' }
        $output=[IO.File]::Open($Destination,'CreateNew','Write','None')
        try {
            $buffer=New-Object byte[] 65536
            $inputStream=$response.GetResponseStream()
            while (($n=$inputStream.Read($buffer,0,$buffer.Length)) -gt 0) {
                if ($output.Length+$n -gt $Spec.archive_bytes) { throw 'DOWNLOAD_SIZE_MISMATCH' }
                $output.Write($buffer,0,$n)
            }
            if ($output.Length -ne $Spec.archive_bytes) { throw 'DOWNLOAD_SIZE_MISMATCH' }
        } finally { $output.Dispose() }
    } finally { $response.Dispose() }
}
function Expand-RuntimeArchive([string]$Archive,[string]$Root,$Spec) {
    if ((Get-FileHash -LiteralPath $Archive -Algorithm SHA256).Hash -ne $Spec.archive_sha256) { throw 'ARCHIVE_SHA256_MISMATCH' }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip=[IO.Compression.ZipFile]::OpenRead($Archive)
    try {
        $seen=@{}
        foreach ($item in $zip.Entries) {
            $name=$item.FullName
            if ($name -notmatch '^[a-zA-Z0-9_.-]+$' -or $name -in '.','..' -or $seen.ContainsKey($name)) { throw 'UNSAFE_ARCHIVE_PATH' }
            $entry=$Spec.files.PSObject.Properties[$name]
            if (!$entry -or $entry.Name -cne $name -or $item.Length -ne $entry.Value.size) { throw 'ARCHIVE_MEMBER_MISMATCH' }
            $seen[$name]=$true
        }
        if ($seen.Count -ne @($Spec.files.PSObject.Properties).Count) { throw 'ARCHIVE_FILESET_MISMATCH' }
        foreach ($item in $zip.Entries) {
            [IO.Compression.ZipFileExtensions]::ExtractToFile($item,(Join-Path $Root $item.FullName),$false)
        }
    } finally { $zip.Dispose() }
    Assert-RuntimeTree $Root $Spec
}
