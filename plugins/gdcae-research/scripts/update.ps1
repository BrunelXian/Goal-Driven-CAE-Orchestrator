[CmdletBinding()]
param(
    [ValidateSet('hook','check','install')][string]$Action='check',
    [string]$TargetVersion, [string]$ManifestPin, [switch]$ConfirmUpdate
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$repo='BrunelXian/Goal-Driven-CAE-Orchestrator'
$origin="https://github.com/$repo.git"
$branch='gdcae-preview'
$market='gdcae-research-preview'
$product='gdcae-research'
$id="$product@$market"
$root=(Get-Item -LiteralPath $PSScriptRoot).Parent.FullName
$local=(Get-Content -LiteralPath (Join-Path $root 'plugin.json') -Raw -Encoding UTF8 | ConvertFrom-Json).version

function PreviewNumber([string]$v) {
    if ($v -cnotmatch '^0\.2\.0-preview\.([1-9][0-9]{0,5})$') { throw 'UNSUPPORTED_VERSION_SERIES' }
    return [int]$Matches[1]
}
function Get-OfficialJson([string]$suffix) {
    $request=[Net.HttpWebRequest]::Create("https://api.github.com/repos/$repo/$suffix")
    $request.UserAgent='GDCAE-Research-Update/1'
    $request.AllowAutoRedirect=$false
    $request.Timeout=3500
    $request.ReadWriteTimeout=3500
    $response=$request.GetResponse()
    try {
        if ([int]$response.StatusCode -ne 200) {throw 'HTTP_STATUS'}
        $stream=$response.GetResponseStream()
        $bytes=New-Object byte[] 65537
        $count=0
        while ($count -lt $bytes.Length) {
            $n=$stream.Read($bytes,$count,$bytes.Length-$count)
            if ($n -eq 0){break}
            $count+=$n
        }
        if ($count -ge $bytes.Length){throw 'METADATA_SIZE'}
        return ([Text.Encoding]::UTF8.GetString($bytes,0,$count) | ConvertFrom-Json)
    } finally {$response.Dispose()}
}
function Get-Offer {
    $entry=Get-OfficialJson "contents/channel.json?ref=$branch"
    if ($entry.type -cne 'file' -or $entry.path -cne 'channel.json' -or $entry.encoding -cne 'base64' -or $entry.size -gt 2048){throw 'CHANNEL_IDENTITY'}
    $value=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($entry.content)) | ConvertFrom-Json
    $null=PreviewNumber $value.version
    if ($value.schema -ne 1 -or $value.product -cne $product -or $value.manifest_sha256 -cnotmatch '^[0-9a-f]{64}$' -or
        $value.zip_sha256 -cnotmatch '^[0-9a-f]{64}$' -or $value.impact -cne 'restart-rebind-no-migration' -or
        $value.change -cnotin 'project-main','auto-update','preview-fixes'){throw 'INVALID_CHANNEL'}
    return $value
}
function Compare-Offer($offer,[string]$current) {
    $n=PreviewNumber $current
    $next=PreviewNumber $offer.version
    $status=if ($next -gt $n){'AVAILABLE'}elseif ($next -eq $n){'CURRENT'}else{'CHANNEL_BEHIND'}
    $summary=@{'project-main'='研究 Main 与基准资格';'auto-update'='会话检查版本并在确认后通过 Marketplace 更新';'preview-fixes'='已验证的 Preview 修订'}
    return [ordered]@{status=$status;current=$current;available=$offer.version;manifest_sha256=$offer.manifest_sha256;
        changes=$summary[$offer.change];impact='打开新会话；Core 使用时按新版本重新绑定，保留 Runtime 及科研项目';
        details="https://github.com/$repo/releases/tag/gdcae-research-$($offer.version)"}
}
function Invoke-CodexJson([string[]]$arguments) {
    $exe=(Get-Command codex.exe -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
    $out=& $exe @arguments
    if ($LASTEXITCODE -ne 0){throw 'HOST_COMMAND_FAILED'}
    return (($out -join [Environment]::NewLine) | ConvertFrom-Json)
}
function Review-Package([string]$folder,[string]$pin,[string]$version) {
    $manifest=Join-Path $folder 'package-manifest.json'
    if ((Get-FileHash -LiteralPath $manifest).Hash -ne $pin){throw 'PACKAGE_MANIFEST_MISMATCH'}
    $m=Get-Content -LiteralPath $manifest -Encoding UTF8 -Raw | ConvertFrom-Json
    $p=Get-Content -LiteralPath (Join-Path $folder 'plugin.json') -Encoding UTF8 -Raw | ConvertFrom-Json
    if ($m.version -cne $version -or $p.name -cne $product -or $p.version -cne $version){throw 'PACKAGE_IDENTITY'}
    $expected=@($m.files.PSObject.Properties)
    $tree=@(Get-ChildItem -LiteralPath $folder -Recurse -Force)
    if (@($tree | Where-Object {$_.Attributes -band [IO.FileAttributes]::ReparsePoint}).Count){throw 'UNSAFE_TREE'}
    if (@($tree | Where-Object {!$_.PSIsContainer}).Count -ne $expected.Count+1){throw 'PACKAGE_FILESET'}
    foreach ($f in $expected) {
        if ($f.Name -cnotmatch '^[a-zA-Z0-9_.-]+(/[a-zA-Z0-9_.-]+)*$' -or $f.Name.Split('/') -contains '..' -or $f.Name.Split('/') -contains '.' -or
            $f.Value -cnotmatch '^[0-9a-f]{64}$' -or (Get-FileHash -LiteralPath (Join-Path $folder $f.Name)).Hash -ne $f.Value){throw 'PACKAGE_BYTES'}
    }
}
function Get-Installed {
    $rows=@((Invoke-CodexJson @('plugin','list','--json')).installed | Where-Object {$_.name -ceq $product -and $_.enabled})
    if ($rows.Count -ne 1 -or $rows[0].pluginId -cne $id -or $rows[0].marketplaceSource.sourceType -cne 'git' -or $rows[0].marketplaceSource.source -cne $origin){
        throw 'MIGRATION_REQUIRED'
    }
    return $rows[0]
}
function Read-Commit($tag) {
    $ref=Get-OfficialJson "git/ref/tags/$tag"
    if ($ref.object.type -cne 'commit' -or $ref.object.sha -cnotmatch '^[0-9a-f]{40}$'){throw 'TAG_NOT_PINNED'}
    return $ref.object.sha
}
function Install-Offer($offer) {
    if (!$ConfirmUpdate -or $TargetVersion -cne $offer.version -or $ManifestPin -cne $offer.manifest_sha256){throw 'CONFIRM_EXACT_OFFER'}
    $old=Get-Installed
    $delta=(PreviewNumber $TargetVersion)-(PreviewNumber $old.version)
    if ($delta -lt 0){throw 'DOWNGRADE_DENIED'}
    $hostHome=if($env:CODEX_HOME){$env:CODEX_HOME}else{Join-Path ([Environment]::GetFolderPath('UserProfile')) '.codex'}
    $installBase=Join-Path $hostHome "plugins\cache\$market\$product"
    if ($delta -eq 0){
        Review-Package (Join-Path $installBase $TargetVersion) $ManifestPin $TargetVersion
        return @{status='ALREADY_INSTALLED';version=$TargetVersion}
    }
    $snapshot=@((Invoke-CodexJson @('plugin','marketplace','list','--json')).marketplaces | Where-Object {$_.name -ceq $market})
    if ($snapshot.Count -ne 1){throw 'NO_RECOVERY_SNAPSHOT'}
    $priorCommit=& git.exe -C $snapshot[0].root rev-parse HEAD
    if ($LASTEXITCODE -ne 0 -or $priorCommit -cnotmatch '^[0-9a-f]{40}$'){throw 'NO_RECOVERY_SNAPSHOT'}
    $previous=Join-Path $installBase $old.version
    $previousPin=(Get-FileHash -LiteralPath (Join-Path $previous 'package-manifest.json')).Hash
    Review-Package $previous $previousPin $old.version
    Review-Package (Join-Path $snapshot[0].root "plugins\$product") $previousPin $old.version
    $tag="gdcae-research-$TargetVersion"
    $release=Get-OfficialJson "releases/tags/$tag"
    if ($release.tag_name -cne $tag -or $release.draft -or !$release.prerelease){throw 'RELEASE_IDENTITY'}
    foreach ($proof in @(@('package-manifest.json',$ManifestPin),@("CAE-Agent-Research-Preview-$($TargetVersion)_PUBLIC_DIRECTORY.zip",$offer.zip_sha256))) {
        $matchesAsset=@($release.assets | Where-Object {$_.name -ceq $proof[0] -and $_.state -ceq 'uploaded' -and $_.digest -ceq ('sha256:'+$proof[1])})
        if ($matchesAsset.Count -ne 1){throw 'RELEASE_DIGEST_MISMATCH'}
    }
    $commit=Read-Commit $tag
    $head=Get-OfficialJson "git/ref/heads/$branch"
    if ($head.object.sha -cne $commit){throw 'CHANNEL_MOVED'}
    # Inspect immutable, isolated source before invoking a refresh on the user's profile.
    $temp=Join-Path ([IO.Path]::GetTempPath()) ('gdcae-market-'+[guid]::NewGuid().ToString('N'))
    $original=$env:CODEX_HOME
    try {
        [void][IO.Directory]::CreateDirectory($temp)
        $env:CODEX_HOME=$temp
        $stage=Invoke-CodexJson @('plugin','marketplace','add',$origin,'--ref',$commit,'--sparse','.agents/plugins','--sparse','plugins/gdcae-research','--json')
        if ($stage.marketplaceName -cne $market){throw 'STAGED_MARKETPLACE_IDENTITY'}
        Review-Package (Join-Path $stage.installedRoot "plugins\$product") $ManifestPin $TargetVersion
        $catalog=Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $stage.installedRoot '.agents/plugins/marketplace.json') | ConvertFrom-Json
        if ($catalog.name -cne $market -or @($catalog.plugins).Count -ne 1 -or $catalog.plugins[0].name -cne $product -or
            $catalog.plugins[0].source.source -cne 'local' -or $catalog.plugins[0].source.path -cne "./plugins/$product"){throw 'CATALOG_IDENTITY'}
        $probe=Invoke-CodexJson @('plugin','add',$id,'--json')
        if ($probe.version -cne $TargetVersion){throw 'STAGING_HOST_INCOMPATIBLE'}
        Review-Package $probe.installedPath $ManifestPin $TargetVersion
    } finally {
        $env:CODEX_HOME=$original
        $resolved=[IO.Path]::GetFullPath($temp)
        if ([IO.Path]::GetDirectoryName($resolved) -eq [IO.Path]::GetTempPath().TrimEnd('\') -and
            [IO.Path]::GetFileName($resolved) -match '^gdcae-market-[0-9a-f]{32}$' -and (Test-Path -LiteralPath $resolved)){
            Remove-Item -LiteralPath $resolved -Force -Recurse -ErrorAction SilentlyContinue
        }
    }
    # CLI -c pins this operation to the reviewed commit without changing the saved branch.
    $override="marketplaces.$market.ref='$commit'"
    $script:liveWrite=$true
    try {
    $null=Invoke-CodexJson @('plugin','marketplace','upgrade',$market,'-c',$override,'--json')
    $markets=@((Invoke-CodexJson @('plugin','marketplace','list','--json')).marketplaces | Where-Object {$_.name -ceq $market})
    if ($markets.Count -ne 1){throw 'MARKETPLACE_REFRESH_UNKNOWN'}
    Review-Package (Join-Path $markets[0].root "plugins\$product") $ManifestPin $TargetVersion
    $actual=Invoke-CodexJson @('plugin','add',$id,'-c',$override,'--json')
    if ($actual.pluginId -cne $id -or $actual.version -cne $TargetVersion){throw 'HOST_RECEIPT_MISMATCH'}
    Review-Package $actual.installedPath $ManifestPin $TargetVersion
    $observed=Get-Installed
    if ($observed.version -cne $TargetVersion){throw 'HOST_VERSION_MISMATCH'}
    return @{status='INSTALLED_RESTART_REQUIRED';version=$observed.version;enabled=$true;manifest_sha256=$ManifestPin}
    } catch {
        # Restore only the previously installed, byte-verified version using Codex.
        # If the failed command never replaced the working version, leave it alone.
        try {
            Review-Package $previous $previousPin $old.version
            if ((Get-Installed).version -ceq $old.version){return @{status='FAILED_OLD_VERSION_AVAILABLE';version=$old.version}}
        } catch {}
        $recovery="marketplaces.$market.ref='$priorCommit'"
        $null=Invoke-CodexJson @('plugin','marketplace','upgrade',$market,'-c',$recovery,'--json')
        $restored=Invoke-CodexJson @('plugin','add',$id,'-c',$recovery,'--json')
        Review-Package $restored.installedPath $previousPin $old.version
        if ((Get-Installed).version -cne $old.version){throw 'RECOVERY_UNVERIFIED'}
        return @{status='FAILED_OLD_VERSION_RESTORED';version=$old.version}
    }
}

$liveWrite=$false
$lock=$null
try {
    $state=Join-Path $env:LOCALAPPDATA 'GDCAE\plugin-updates'
    [void][IO.Directory]::CreateDirectory($state)
    $lock=[IO.File]::Open((Join-Path $state 'channel.lock'),'OpenOrCreate','ReadWrite','None')
    $cache=Join-Path $state 'check.json'
    if ($Action -ne 'install' -and (Test-Path -LiteralPath $cache) -and
        ((Get-Item -LiteralPath $cache).LastWriteTimeUtc -ge [DateTime]::UtcNow.AddHours(-1) -and (Get-Item -LiteralPath $cache).LastWriteTimeUtc -le [DateTime]::UtcNow)){
        $saved=Get-Content -LiteralPath $cache -Raw -Encoding UTF8 | ConvertFrom-Json
        $result=$null
        if ($saved.current -ceq $local -and $saved.status -ceq 'OFFLINE_OR_UNAVAILABLE'){
            $result=@{status='OFFLINE_OR_UNAVAILABLE';current=$local}
        }elseif ($saved.current -ceq $local -and $saved.available -cmatch '^0\.2\.0-preview\.[1-9][0-9]{0,5}$' -and
            $saved.manifest_sha256 -cmatch '^[0-9a-f]{64}$' -and $saved.change -cin 'project-main','auto-update','preview-fixes'){
            $result=Compare-Offer ([pscustomobject]@{version=$saved.available;manifest_sha256=$saved.manifest_sha256;change=$saved.change}) $local
        }
    }else{$result=$null}
    if (!$result -or $Action -eq 'install'){
        try {$offer=Get-Offer;$result=Compare-Offer $offer $local}
        catch {if($Action -eq 'install'){throw};$result=@{status='OFFLINE_OR_UNAVAILABLE';current=$local}}
        if ($Action -eq 'install'){$result=Install-Offer $offer}
        else {
            $cached=@{};foreach($k in $result.Keys){$cached[$k]=$result[$k]}
            if ($result.status -ne 'OFFLINE_OR_UNAVAILABLE'){$cached.change=$offer.change}
            [IO.File]::WriteAllText($cache,($cached | ConvertTo-Json -Compress))
        }
    }
} catch [IO.IOException] {
    $result=@{status=if($liveWrite){'UNKNOWN_AFTER_HOST_WRITE'}else{'BUSY'}}
} catch {
    $code=$_.Exception.Message
    if ($code -cnotmatch '^[A-Z_]{3,60}$'){$code='UPDATE_UNAVAILABLE'}
    $result=@{status=if($liveWrite){'UNKNOWN_AFTER_HOST_WRITE'}else{'BLOCKED'};reason=$code}
} finally {if ($lock){$lock.Dispose()}}
if ($Action -eq 'hook') {
    if ($result.status -eq 'AVAILABLE'){
        @{hookSpecificOutput=@{hookEventName='SessionStart';additionalContext=('GD-CAE official channel data: '+($result | ConvertTo-Json -Compress))}} | ConvertTo-Json -Depth 4 -Compress
    }else{'{}'}
} else {$result | ConvertTo-Json -Compress}
if ($Action -eq 'install' -and $result.status -notin 'INSTALLED_RESTART_REQUIRED','ALREADY_INSTALLED'){exit 2}
