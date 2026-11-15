[CmdletBinding()]
param(
    [ValidateSet('hook','check','skill-check','install')][string]$Action='check',
    [string]$TargetVersion, [string]$ManifestPin, [switch]$ConfirmUpdate,
    [string]$ChannelBase64, [string]$ChannelBlobSha
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
    if ($env:CODEX_SANDBOX_NETWORK_DISABLED -in '1','true'){throw 'HOST_NETWORK_RESTRICTED'}
    $request=[Net.HttpWebRequest]::Create("https://api.github.com/repos/$repo/$suffix")
    $request.UserAgent='GDCAE-Research-Update/1'
    $request.AllowAutoRedirect=$false
    $request.Timeout=5500
    $request.ReadWriteTimeout=5500
    try {$response=$request.GetResponse()} catch [Net.WebException] {
        $ex=$_.Exception
        $http=if($ex.Response){[int]$ex.Response.StatusCode}else{0}
        $limited=$ex.Response -and ($ex.Response.Headers['X-RateLimit-Remaining'] -eq '0' -or $ex.Response.Headers['Retry-After'])
        if ($ex.Response){$ex.Response.Dispose()}
        if ($http){$script:httpStatus=$http}
        if ($http -eq 407){throw 'PROXY_AUTH_REQUIRED'}
        if ($http -eq 429 -or ($http -eq 403 -and $limited)){throw 'GITHUB_RATE_LIMIT'}
        if ($http -ge 500){throw 'GITHUB_API_UNAVAILABLE'}
        if ($http){throw 'HTTP_ERROR'}
        switch ([string]$ex.Status) {
            'NameResolutionFailure' {throw 'DNS_FAILURE'}
            'ProxyNameResolutionFailure' {throw 'PROXY_DNS_FAILURE'}
            'SecureChannelFailure' {throw 'TLS_FAILURE'}
            'TrustFailure' {throw 'TLS_TRUST_FAILURE'}
            'Timeout' {throw 'NETWORK_TIMEOUT'}
        }
        if ($request.Proxy -and !$request.Proxy.IsBypassed($request.RequestUri) -and $ex.Status -eq 'ConnectFailure'){throw 'PROXY_CONNECT_FAILURE'}
        throw 'NETWORK_CONNECTION_FAILURE'
    }
    try {
        if ([int]$response.StatusCode -ne 200) {$script:httpStatus=[int]$response.StatusCode;throw 'HTTP_ERROR'}
        $stream=$response.GetResponseStream()
        $bytes=New-Object byte[] 65537
        $count=0
        while ($count -lt $bytes.Length) {
            $n=$stream.Read($bytes,$count,$bytes.Length-$count)
            if ($n -eq 0){break}
            $count+=$n
        }
        if ($count -ge $bytes.Length){throw 'METADATA_SIZE'}
        try {return ([Text.UTF8Encoding]::new($false,$true).GetString($bytes,0,$count) | ConvertFrom-Json)}
        catch {throw 'METADATA_FORMAT_ERROR'}
    } finally {$response.Dispose()}
}
function ConvertTo-Offer($entry) {
    if ($entry.type -cne 'file' -or $entry.path -cne 'channel.json' -or $entry.encoding -cne 'base64' -or $entry.size -gt 2048){throw 'CHANNEL_IDENTITY'}
    $data=[Convert]::FromBase64String($entry.content)
    $header=[Text.Encoding]::ASCII.GetBytes("blob "+$data.Length+[char]0)
    $alg=[Security.Cryptography.SHA1]::Create()
    try {$blob=([BitConverter]::ToString($alg.ComputeHash([byte[]]($header+$data)))).Replace('-','').ToLowerInvariant()} finally {$alg.Dispose()}
    if ($entry.size -ne $data.Length -or $entry.sha -cne $blob){throw 'METADATA_INTEGRITY_ERROR'}
    $value=[Text.UTF8Encoding]::new($false,$true).GetString($data) | ConvertFrom-Json
    $null=PreviewNumber $value.version
    if ($value.schema -ne 1 -or $value.product -cne $product -or $value.manifest_sha256 -cnotmatch '^[0-9a-f]{64}$' -or
        $value.zip_sha256 -cnotmatch '^[0-9a-f]{64}$' -or $value.impact -cne 'restart-rebind-no-migration' -or
        $value.change -cnotin 'project-main','auto-update','preview-fixes'){throw 'INVALID_CHANNEL'}
    return $value
}
function Get-Offer {
    $entry=Get-OfficialJson "contents/channel.json?ref=$branch"
    try {return ConvertTo-Offer $entry}
    catch {if ($_.Exception.Message -eq 'METADATA_INTEGRITY_ERROR'){throw};throw 'METADATA_FORMAT_ERROR'}
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
    $oldPreference=$ErrorActionPreference
    try {$ErrorActionPreference='Continue'; $out=@(& $exe @arguments 2>&1); $rc=$LASTEXITCODE}
    finally {$ErrorActionPreference=$oldPreference}
    if ($rc -ne 0){
        $script:hostExit=$rc
        if (($out -join ' ') -match 'permission denied|access (is )?denied|os error 5\b|拒绝访问|blocked by policy'){throw 'BLOCKED_HOST_UPDATE_PERMISSION'}
        throw 'HOST_COMMAND_FAILED'
    }
    $out=@($out | Where-Object {$_ -isnot [Management.Automation.ErrorRecord]})
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
        if ($_.Exception.Message -eq 'BLOCKED_HOST_UPDATE_PERMISSION'){throw}
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

function Get-StateDirectory {
    $base=if($env:PLUGIN_DATA){$env:PLUGIN_DATA}else{$env:LOCALAPPDATA}
    if (!$base -or $base -notmatch '^[A-Za-z]:[\\/]' -or $base -match '(^|[\\/])\.\.([\\/]|$)'){throw 'LOCAL_STATE_UNAVAILABLE'}
    $dir=if ($env:PLUGIN_DATA){Join-Path $base 'gdcae-update'}else{Join-Path $base 'GDCAE\plugin-updates'}
    $dir=[IO.Path]::GetFullPath($dir)
    for ($p=$dir;$p;$p=[IO.Path]::GetDirectoryName($p)){
        if ($p -eq $root -or ((Test-Path -LiteralPath $p) -and ((Get-Item -LiteralPath $p -Force).Attributes -band [IO.FileAttributes]::ReparsePoint))){throw 'LOCAL_STATE_UNSAFE'}
    }
    [void][IO.Directory]::CreateDirectory($dir)
    return $dir
}
function Read-CheckCache($file) {
    if (![IO.File]::Exists($file)){return $null}
    $info=Get-Item -LiteralPath $file -Force
    if ($info.Length -gt 8192 -or ($info.Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'CACHE_INVALID'}
    $v=Get-Content -Raw -Encoding UTF8 -LiteralPath $file | ConvertFrom-Json
    if ($v.schema -ne 2 -or $v.product -cne $product -or $v.channel -cne $branch -or $v.version -cne $local){return $null}
    $now=[DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    if ($v.checked -gt $now -or $v.expires -le $now){return $null}
    if ($v.kind -ceq 'restricted'){
        if ($env:CODEX_SANDBOX_NETWORK_DISABLED -notin '1','true' -or $v.expires -ne $v.checked+180){return $null}
        return [ordered]@{status='CHECK_UNAVAILABLE';reason='HOST_NETWORK_RESTRICTED';current=$local;
            checked_utc_epoch=$v.checked;expires_utc_epoch=$v.expires}
    }
    if ($v.kind -cne 'offer' -or $v.expires -ne $v.checked+3600){return $null}
    if ($v.offer.manifest_sha256 -cnotmatch '^[0-9a-f]{64}$' -or $v.offer.change -cnotin 'auto-update','project-main','preview-fixes'){throw 'CACHE_INVALID'}
    $result=Compare-Offer $v.offer $local
    $result.checked_utc_epoch=$v.checked
    $result.expires_utc_epoch=$v.expires
    return $result
}
function Write-CheckCache($file,$offer,$checked) {
    $v=@{schema=2;product=$product;channel=$branch;version=$local;checked=$checked}
    if ($null -eq $offer){$v.kind='restricted';$v.expires=$checked+180}
    else {$v.kind='offer';$v.expires=$checked+3600;$v.offer=@{version=$offer.version;manifest_sha256=$offer.manifest_sha256;change=$offer.change}}
    $tmp=Join-Path ([IO.Path]::GetDirectoryName($file)) ([guid]::NewGuid().ToString('N')+'.tmp')
    try {
        [IO.File]::WriteAllText($tmp,($v | ConvertTo-Json -Compress -Depth 3))
        if ([IO.File]::Exists($file)){
            $backup=$tmp+'.bak'
            [IO.File]::Replace($tmp,$file,$backup)
            [IO.File]::Delete($backup)
        }else{[IO.File]::Move($tmp,$file)}
    }finally{if ([IO.File]::Exists($tmp)){[IO.File]::Delete($tmp)}}
}

$mode=@{hook='SESSIONSTART_AUTO_CHECK';'skill-check'='FIRST_SKILL_USE_CHECK';check='MANUAL_CHECK';install='CONFIRMED_INSTALL'}[$Action]
# Connector provenance comes from the Host tool event. Its bytes are for display only:
# never persist these inputs, perform an install, or replace the release verification path.
if ($PSBoundParameters.ContainsKey('ChannelBase64') -or $PSBoundParameters.ContainsKey('ChannelBlobSha')) {
    $rc=0
    try {
        if ($Action -ne 'skill-check' -or $ConfirmUpdate -or $TargetVersion -or $ManifestPin){$rc=2;throw 'DISCOVERY_ONLY'}
        if ($ChannelBase64.Length -gt 2732 -or $ChannelBase64 -cnotmatch '^[A-Za-z0-9+/]+={0,2}$' -or
            $ChannelBlobSha -cnotmatch '^[0-9a-f]{40}$'){throw 'METADATA_FORMAT_ERROR'}
        $bytes=[Convert]::FromBase64String($ChannelBase64)
        $offer=ConvertTo-Offer ([pscustomobject]@{type='file';path='channel.json';encoding='base64';size=$bytes.Length;
            content=$ChannelBase64;sha=$ChannelBlobSha})
        $result=Compare-Offer $offer $local
        $result.zip_sha256=$offer.zip_sha256
        $result.channel_blob_sha=$ChannelBlobSha
    } catch {
        $reason=if ($_.Exception.Message -in 'DISCOVERY_ONLY','METADATA_INTEGRITY_ERROR'){$_.Exception.Message}else{'METADATA_FORMAT_ERROR'}
        $result=@{status='CHECK_UNAVAILABLE';current=$local;reason=$reason}
    }
    $result.mode=$mode
    $result.source='CONNECTOR_INPUT'
    $result.cache='NOT_STORED'
    $result.exit_code=$rc
    $result | ConvertTo-Json -Compress
    exit $rc
}
$liveWrite=$false
$lock=$null
$result=$null
$httpStatus=$null
$hostExit=$null
$cacheState='MISS'
$store=if($env:PLUGIN_DATA){'PLUGIN_DATA'}else{'LOCALAPPDATA'}
try {
    try {
        $state=Get-StateDirectory
        $guard=Join-Path $state 'channel.lock'
        $file=Join-Path $state 'check-v2.json'
        foreach($path in @($guard,$file)){
            if ((Test-Path -LiteralPath $path) -and ((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'LOCAL_STATE_UNSAFE'}
        }
        $lock=[IO.File]::Open($guard,'OpenOrCreate','ReadWrite','None')
    } catch {
        $cacheState='LOCAL_STATE_UNWRITABLE'
        for($cause=$_.Exception;$cause;$cause=$cause.InnerException){
            if (($cause.HResult -band 65535) -in 32,33){$cacheState='BUSY'}
        }
        if($Action -eq 'install'){throw $cacheState}
        if($cacheState -eq 'BUSY'){$result=@{status='BUSY';current=$local}}
    }
    if ($lock -and $Action -ne 'install'){
        try {$result=Read-CheckCache $file;if ($result){$cacheState='HIT'}}
        catch {$cacheState='CORRUPT_OR_UNREADABLE'}
    }
    if (!$result){
        $offer=Get-Offer
        if ($Action -eq 'install'){$result=Install-Offer $offer}
        else {
            $result=Compare-Offer $offer $local
            $checked=[DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
            $result.checked_utc_epoch=$checked
            $result.expires_utc_epoch=$checked+3600
            if ($lock){
                try {Write-CheckCache $file $offer $checked
                    $cacheState=if ($cacheState -eq 'CORRUPT_OR_UNREADABLE'){'REPAIRED'}else{'STORED'}
                }catch{$cacheState='LOCAL_STATE_UNWRITABLE'}
            }
        }
    }
} catch {
    $code=$_.Exception.Message
    if ($code -cnotmatch '^[A-Z_]{3,60}$'){$code='UNCLASSIFIED_FAILURE'}
    $status=if ($code -eq 'BLOCKED_HOST_UPDATE_PERMISSION'){$code}elseif($liveWrite){'UNKNOWN_AFTER_HOST_WRITE'}elseif($Action -eq 'install'){'BLOCKED'}else{'CHECK_UNAVAILABLE'}
    $result=@{status=$status;reason=$code;current=$local}
    if ($code -ceq 'HOST_NETWORK_RESTRICTED' -and $lock -and $Action -ne 'install'){
        $checked=[DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
        try {
            Write-CheckCache $file $null $checked
            $result.checked_utc_epoch=$checked;$result.expires_utc_epoch=$checked+180;$cacheState='STORED'
        }catch{$cacheState='LOCAL_STATE_UNWRITABLE'}
    }
    if ($httpStatus){$result.http_status=$httpStatus}
    if ($null -ne $hostExit){$result.host_exit_code=$hostExit}
} finally {if ($lock){$lock.Dispose()}}
$result.mode=$mode
$result.cache=$cacheState
$result.cache_store=$store
$rc=0
if ($Action -eq 'install' -and $result.status -notin 'INSTALLED_RESTART_REQUIRED','ALREADY_INSTALLED'){$rc=2}
$result.exit_code=$rc
if ($Action -eq 'hook') {
    @{hookSpecificOutput=@{hookEventName='SessionStart';additionalContext=('GD-CAE update receipt '+($result | ConvertTo-Json -Compress))}} | ConvertTo-Json -Depth 4 -Compress
} else {$result | ConvertTo-Json -Compress}
exit $rc
