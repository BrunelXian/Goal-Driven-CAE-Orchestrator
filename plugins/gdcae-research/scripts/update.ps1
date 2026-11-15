[CmdletBinding()]
param(
    [ValidateSet('hook','check','skill-check','offer','install','identity','pin-current','verify','handoff-identity')][string]$Action='check',
    [string]$TargetVersion, [string]$ManifestPin, [switch]$ConfirmUpdate,
    [string]$ChannelBase64, [string]$ChannelBlobSha,
    [string]$InstalledRoot, [string]$FromCommit, [string]$TargetCommit, [string]$ZipPin
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
        zip_sha256=$offer.zip_sha256;changes=$summary[$offer.change];impact='打开新会话；Core 使用时按新版本重新绑定，保留 Runtime 及科研项目';
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
    if ((Get-Item -LiteralPath $folder -Force).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'UNSAFE_TREE'}
    $manifest=Join-Path $folder 'package-manifest.json'
    if ((Get-FileHash -LiteralPath $manifest).Hash -ne $pin){throw 'PACKAGE_MANIFEST_MISMATCH'}
    $m=Get-Content -LiteralPath $manifest -Encoding UTF8 -Raw | ConvertFrom-Json
    $p=Get-Content -LiteralPath (Join-Path $folder 'plugin.json') -Encoding UTF8 -Raw | ConvertFrom-Json
    if ($m.version -cne $version -or $p.name -cne $product -or $p.version -cne $version){throw 'PACKAGE_IDENTITY'}
    $expected=@($m.files.PSObject.Properties)
    $tree=@(Get-ChildItem -LiteralPath $folder -Recurse -Force)
    if (@($tree | Where-Object {$_.Attributes -band [IO.FileAttributes]::ReparsePoint}).Count){throw 'UNSAFE_TREE'}
    $actualNames=@($tree | Where-Object {!$_.PSIsContainer} | ForEach-Object {$_.FullName.Substring($folder.TrimEnd('\','/').Length+1).Replace('\','/')})
    $expectedNames=@('package-manifest.json')+@($expected | ForEach-Object Name)
    if ($actualNames.Count -ne $expectedNames.Count -or (Compare-Object -CaseSensitive $expectedNames $actualNames)){throw 'PACKAGE_FILESET'}
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
function Read-Commit($refName) {
    $ref=Read-ConnectorJson "git/ref/$refName"
    if ($ref.ref -cne "refs/$refName" -or $ref.object.type -cne 'commit' -or $ref.object.sha -cnotmatch '^[0-9a-f]{40}$'){throw 'REF_IDENTITY'}
    return $ref.object.sha
}

# This configuration-only Host has no plugins to start. In particular reading a
# legacy branch registration during migration must not schedule its refresh.
function Invoke-PinRpc($process,[int]$number,[string]$method,$parameters) {
    Send-RpcLine $process (@{id=$number;method=$method;params=$parameters}|ConvertTo-Json -Compress -Depth 10)
    $end=[DateTime]::UtcNow.AddSeconds(35)
    while ([DateTime]::UtcNow -lt $end) {
        $line=$process.StandardOutput.ReadLineAsync()
        if (!$line.Wait([Math]::Max(1,[int]($end-[DateTime]::UtcNow).TotalMilliseconds)) -or !$line.Result){throw 'HOST_RPC_UNAVAILABLE'}
        $message=$line.Result | ConvertFrom-Json
        if ($message.PSObject.Properties['id'] -and $message.id -eq $number){
            if ($message.PSObject.Properties['error']){throw 'HOST_CONFIG_REJECTED'}
            return $message.result
        }
    }
    throw 'HOST_RPC_TIMEOUT'
}
function Send-RpcLine($process,[string]$json) {
    $data=[Text.Encoding]::UTF8.GetBytes($json+[char]10)
    $pipe=$process.StandardInput.BaseStream
    $pipe.Write($data,0,$data.Length)
    $pipe.Flush()
}
function Get-PinLayer($process,$homePath,[int]$number) {
    $r=Invoke-PinRpc $process $number 'config/read' @{includeLayers=$true;cwd=(Get-Location).Path}
    $layers=@($r.layers|Where-Object {$_.name.type -ceq 'user' -and $_.name.file -eq (Join-Path $homePath 'config.toml')})
    if($layers.Count -ne 1){throw 'HOST_CONFIG_SCOPE'}
    $entry=$layers[0].config.marketplaces.$market
    $effective=$r.config.marketplaces.$market
    if ($entry.source -cne $origin -or $effective.source -cne $origin -or $entry.ref -cne $effective.ref){throw 'HOST_CONFIG_SCOPE'}
    return @{ref=$entry.ref;version=$layers[0].version}
}
function Invoke-MarketplacePin($homePath,[string]$expected,[string]$replacement,[string]$revision){
    $si=[Diagnostics.ProcessStartInfo]::new()
    $si.FileName=(Get-Command codex.exe -CommandType Application|Select-Object -First 1).Source
    $si.Arguments='app-server --stdio --disable plugins'
    $si.UseShellExecute=$false
    $si.CreateNoWindow=$true
    $si.RedirectStandardInput=$true
    $si.RedirectStandardOutput=$true
    $si.RedirectStandardError=$true
    $si.StandardOutputEncoding=[Text.UTF8Encoding]::new($false)
    $p=[Diagnostics.Process]::Start($si)
    try{
        $p.BeginErrorReadLine()
        $null=Invoke-PinRpc $p 1 'initialize' @{clientInfo=@{name='gdcae-update';version='1'};capabilities=@{}}
        Send-RpcLine $p '{"method":"initialized","params":{}}'
        $current=Get-PinLayer $p $homePath 2
        if (!$replacement){return $current}
        if ($replacement -cnotmatch '^[0-9a-f]{40}$' -or $current.ref -cne $expected -or $current.version -cne $revision){throw 'PIN_CONFLICT'}
        $result=Invoke-PinRpc $p 3 'config/value/write' @{keyPath="marketplaces.$market.ref";value=$replacement;mergeStrategy='replace';expectedVersion=$revision}
        $after=Get-PinLayer $p $homePath 4
        if ($result.status -cne 'ok' -or $result.overriddenMetadata -or $after.ref -cne $replacement){throw 'PIN_WRITE_UNCONFIRMED'}
        return $after
    }finally{if (!$p.HasExited){$p.Kill()};$p.Dispose()}
}
function Get-HostHome {
    if ($env:CODEX_HOME){return [IO.Path]::GetFullPath($env:CODEX_HOME)}
    return Join-Path ([Environment]::GetFolderPath('UserProfile')) '.codex'
}
function Verify-Installation($homePath,$version,$commit,$manifest) {
    if ((Invoke-MarketplacePin $homePath).ref -cne $commit){throw 'PIN_MISMATCH'}
    $ms=@((Invoke-CodexJson @('plugin','marketplace','list','--json')).marketplaces|Where-Object name -CEQ $market)
    if ($ms.Count -ne 1 -or $ms[0].marketplaceSource.source -cne $origin){throw 'MARKETPLACE_IDENTITY'}
    $actual=& git.exe -C $ms[0].root rev-parse HEAD
    if ($LASTEXITCODE -ne 0 -or $actual -cne $commit){throw 'MARKETPLACE_HEAD_MISMATCH'}
    if ((Get-Installed).version -cne $version){throw 'HOST_VERSION_MISMATCH'}
    Review-Package (Join-Path $ms[0].root "plugins\$product") $manifest $version
    Review-Package (Join-Path $homePath "plugins\cache\$market\$product\$version") $manifest $version
}
function Get-ConnectorCalls([switch]$ForHandoff) {
    # Read structured events from the invoking Host thread, never from caller JSON.
    $tid=$env:CODEX_THREAD_ID
    if ($tid -notmatch '^[0-9a-fA-F-]{36}$'){throw 'HOST_THREAD_REQUIRED'}
    $si=[Diagnostics.ProcessStartInfo]::new()
    $si.FileName=(Get-Command codex.exe -CommandType Application|Select-Object -First 1).Source
    $si.Arguments='app-server --stdio --disable plugins'
    $si.UseShellExecute=$false
    $si.CreateNoWindow=$true
    $si.RedirectStandardInput=$true
    $si.RedirectStandardOutput=$true
    $si.RedirectStandardError=$true
    $si.StandardOutputEncoding=[Text.UTF8Encoding]::new($false)
    $p=[Diagnostics.Process]::Start($si)
    try {
        $p.BeginErrorReadLine()
        $null=Invoke-PinRpc $p 1 initialize @{clientInfo=@{name='gdcae-update';version='1'};capabilities=@{experimentalApi=$true}}
        Send-RpcLine $p '{"method":"initialized","params":{}}'
        $r=Invoke-PinRpc $p 2 'thread/read' @{threadId=$tid;includeTurns=$true}
        if ($r.thread.id -cne $tid){throw 'HOST_THREAD_MISMATCH'}
        $turns=@($r.thread.turns)
        [array]::Reverse($turns)
        foreach ($turn in $turns){
            $calls=@($turn.items | Where-Object {$_.type -ceq 'mcpToolCall' -and $_.server -ceq 'codex_apps' -and $_.tool -cin 'github.fetch','github.fetch_file'})
            if (!$calls.Count){continue}
            $age=[DateTimeOffset]::UtcNow.ToUnixTimeSeconds()-[long]$turn.startedAt
            if ($ForHandoff -and $age -ge 0 -and $age -le 1800 -and $turn.status -cnotin 'completed','inProgress'){
                throw 'CONNECTOR_TURN_UNCONFIRMED'
            }
            if ($turn.status -cnotin 'completed','inProgress' -or $age -lt 0 -or $age -gt 1800){throw 'CONNECTOR_PROOF_EXPIRED'}
            return $calls
        }
        throw 'CONNECTOR_PROOF_MISSING'
    } finally {if (!$p.HasExited){$p.Kill()};$p.Dispose()}
}
function Read-ConnectorJson([string]$suffix) {
    $url="https://api.github.com/repos/$repo/$suffix"
    $hits=@($connectorCalls | Where-Object {$_.tool -ceq 'github.fetch' -and $_.status -ceq 'completed' -and $_.arguments.url -ceq $url})
    if ($hits.Count -ne 1){throw 'CONNECTOR_PROOF_MISSING'}
    return ($hits[0].result.structuredContent.content | ConvertFrom-Json)
}
function Get-ReleaseDigest($release,$tag,$name) {
    $asset=@($release.assets | Where-Object name -CEQ $name)
    if ($asset.Count -ne 1 -or $asset[0].state -cne 'uploaded' -or $asset[0].size -le 0 -or $asset[0].id -le 0 -or
        $asset[0].browser_download_url -cne "https://github.com/$repo/releases/download/$tag/$name" -or
        $asset[0].digest -cnotmatch '^sha256:([0-9a-f]{64})$'){throw 'RELEASE_DIGEST_MISMATCH'}
    return $Matches[1]
}
function Get-ReleasePins($version,$commit){
    $null=PreviewNumber $version
    $tag="gdcae-research-$version"
    if ((Read-Commit "tags/$tag") -cne $commit){throw 'BASELINE_TAG_MISMATCH'}
    $release=Read-ConnectorJson "releases/tags/$tag"
    if ($release.tag_name -cne $tag -or $release.draft -ne $false -or $release.prerelease -ne $true -or
        $release.html_url -cne "https://github.com/$repo/releases/tag/$tag"){throw 'RELEASE_IDENTITY'}
    return @{manifest=(Get-ReleaseDigest $release $tag 'package-manifest.json');
        zip=(Get-ReleaseDigest $release $tag "CAE-Agent-Research-Preview-${version}_PUBLIC_DIRECTORY.zip")}
}
function Get-ReleaseManifestPin($version,$commit){return (Get-ReleasePins $version $commit).manifest}
function Get-ConnectorOffer {
    $commit=Read-Commit "heads/$branch"
    $files=@($connectorCalls | Where-Object {$_.tool -ceq 'github.fetch_file' -and $_.status -ceq 'completed' -and
        $_.arguments.repository_full_name -ceq $repo -and $_.arguments.ref -ceq $commit -and
        $_.arguments.path -ceq 'channel.json' -and $_.arguments.encoding -ceq 'base64'})
    if ($files.Count -ne 1){throw 'CONNECTOR_CHANNEL_MISSING'}
    $entry=$files[0].result.structuredContent
    if ($entry.encoding -cne 'base64' -or $entry.content.Length -gt 3000){throw 'CHANNEL_IDENTITY'}
    $offer=ConvertTo-Offer ([pscustomobject]@{type='file';path='channel.json';encoding=$entry.encoding;
        content=$entry.content;sha=$entry.sha;size=[Convert]::FromBase64String($entry.content).Length})
    $pins=Get-ReleasePins $offer.version $commit
    if ($pins.manifest -cne $offer.manifest_sha256 -or $pins.zip -cne $offer.zip_sha256){throw 'RELEASE_DIGEST_MISMATCH'}
    $offer | Add-Member -NotePropertyMembers @{target_commit=$commit;channel_blob=$entry.sha}
    return $offer
}
function Assert-StagedRef($folder,$commit,$blob){
    $head=& git.exe -C $folder rev-parse --verify HEAD
    if ($LASTEXITCODE -ne 0 -or $head -cne $commit){throw 'STAGED_HEAD_MISMATCH'}
    $object=& git.exe -C $folder rev-parse --verify HEAD:channel.json
    if ($LASTEXITCODE -ne 0 -or $object -cne $blob){throw 'STAGED_CHANNEL_MISMATCH'}
}
function Pin-Current {
    if (!$ConfirmUpdate -or $TargetCommit -cnotmatch '^[0-9a-f]{40}$' -or $ManifestPin -cnotmatch '^[0-9a-f]{64}$'){throw 'CONFIRM_EXACT_OFFER'}
    $null=PreviewNumber $TargetVersion
    $homePath=Get-HostHome
    $before=Invoke-MarketplacePin $homePath
    if ($before.ref -cnotin $branch,$TargetCommit){throw 'PIN_CONFLICT'}
    if ((Get-ReleaseManifestPin $TargetVersion $TargetCommit) -cne $ManifestPin){throw 'BASELINE_TAG_MISMATCH'}
    $snap=Join-Path $homePath ".tmp\marketplaces\$market"
    $actual=& git.exe -C $snap rev-parse HEAD
    if ($LASTEXITCODE -or $actual -cne $TargetCommit){throw 'MARKETPLACE_HEAD_MISMATCH'}
    Review-Package (Join-Path $snap "plugins\$product") $ManifestPin $TargetVersion
    Review-Package (Join-Path $homePath "plugins\cache\$market\$product\$TargetVersion") $ManifestPin $TargetVersion
    if ($before.ref -cne $TargetCommit){
        $script:liveWrite=$true
        $null=Invoke-MarketplacePin $homePath $branch $TargetCommit $before.version
    }
    Verify-Installation $homePath $TargetVersion $TargetCommit $ManifestPin
    return @{status='PINNED_CURRENT';version=$TargetVersion;commit=$TargetCommit;manifest_sha256=$ManifestPin;enabled=$true}
}
function Save-RecoveryPackage($folder,$pin,$version,$commit,$directory){
    if ($commit -cnotmatch '^[0-9a-f]{40}$'){throw 'NO_RECOVERY_SNAPSHOT'}
    $dest=Join-Path $directory ("known-good-"+$commit)
    if (!(Test-Path -LiteralPath $dest)){
        $tmp=Join-Path $directory ("staging-"+[guid]::NewGuid().ToString('N'))
        # Copy only the already verified payload. Host state and user data are outside this tree.
        Copy-Item -LiteralPath $folder -Destination $tmp -Recurse -ErrorAction Stop
        Review-Package $tmp $pin $version
        [IO.Directory]::Move($tmp,$dest)
    }
    Review-Package $dest $pin $version
}
function Install-Offer($offer) {
    if (!$ConfirmUpdate -or $TargetVersion -cne $offer.version -or $ManifestPin -cne $offer.manifest_sha256 -or
        $ZipPin -cne $offer.zip_sha256 -or $TargetCommit -cnotmatch '^[0-9a-f]{40}$' -or $FromCommit -cnotmatch '^[0-9a-f]{40}$'){throw 'CONFIRM_EXACT_OFFER'}
    if ($offer.target_commit -cne $TargetCommit){throw 'CHANNEL_MOVED'}
    $hostHome=Get-HostHome
    $saved=Invoke-MarketplacePin $hostHome
    if ($saved.ref -cnotmatch '^[0-9a-f]{40}$'){throw 'MIGRATION_REQUIRED'}
    if ($saved.ref -cnotin $FromCommit,$TargetCommit){throw 'PIN_CONFLICT'}
    $old=Get-Installed
    $delta=(PreviewNumber $TargetVersion)-(PreviewNumber $old.version)
    if ($delta -lt 0){throw 'DOWNGRADE_DENIED'}
    $installBase=Join-Path $hostHome "plugins\cache\$market\$product"
    if ($delta -eq 0){
        if ((Get-ReleaseManifestPin $TargetVersion $TargetCommit) -cne $ManifestPin){throw 'RELEASE_DIGEST_MISMATCH'}
        Verify-Installation $hostHome $TargetVersion $TargetCommit $ManifestPin
        return @{status='ALREADY_INSTALLED';version=$TargetVersion;commit=$TargetCommit;enabled=$true;manifest_sha256=$ManifestPin}
    }
    $snapshot=@((Invoke-CodexJson @('plugin','marketplace','list','--json')).marketplaces | Where-Object {$_.name -ceq $market})
    if ($snapshot.Count -ne 1){throw 'NO_RECOVERY_SNAPSHOT'}
    $priorCommit=& git.exe -C $snapshot[0].root rev-parse HEAD
    if ($LASTEXITCODE -ne 0 -or $priorCommit -cne $FromCommit -or $saved.ref -cne $FromCommit){throw 'NO_RECOVERY_SNAPSHOT'}
    $previous=Join-Path $installBase $old.version
    $previousPin=Get-ReleaseManifestPin $old.version $priorCommit
    Review-Package $previous $previousPin $old.version
    Review-Package (Join-Path $snapshot[0].root "plugins\$product") $previousPin $old.version
    $commit=$offer.target_commit
    # Inspect immutable, isolated source before invoking a refresh on the user's profile.
    $temp=Join-Path ([IO.Path]::GetTempPath()) ('gdcae-market-'+[guid]::NewGuid().ToString('N'))
    $original=$env:CODEX_HOME
    try {
        [void][IO.Directory]::CreateDirectory($temp)
        $env:CODEX_HOME=$temp
        $stage=Invoke-CodexJson @('plugin','marketplace','add',$origin,'--ref',$commit,'--sparse','.agents/plugins','--sparse','plugins/gdcae-research','--json')
        if ($stage.marketplaceName -cne $market){throw 'STAGED_MARKETPLACE_IDENTITY'}
        Assert-StagedRef $stage.installedRoot $commit $offer.channel_blob
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
    # Exclusive, durable record before the first live write. Retain it on unknown outcomes.
    Save-RecoveryPackage $previous $previousPin $old.version $priorCommit $state
    $journal=Join-Path $state 'pending.json'
    try {$stream=[IO.File]::Open($journal,'CreateNew','Write','None')}catch{throw 'PENDING_RECONCILIATION'}
    try {
        $bytes=[Text.Encoding]::UTF8.GetBytes((@{instance=$hostHome;previous_version=$old.version;previous_commit=$priorCommit;previous_manifest=$previousPin;
            target=$TargetVersion;target_commit=$commit;target_manifest=$ManifestPin;zip_sha256=$ZipPin}|ConvertTo-Json))
        $stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)
    }finally{$stream.Dispose()}
    $script:liveWrite=$true
    $written=$null
    try {
        $written=Invoke-MarketplacePin $hostHome $priorCommit $commit $saved.version
        $refresh=Invoke-CodexJson @('plugin','marketplace','upgrade',$market,'--json')
        if ($refresh.errors.Count -or $market -cnotin $refresh.selectedMarketplaces){throw 'MARKETPLACE_REFRESH_UNKNOWN'}
        Verify-Installation $hostHome $TargetVersion $commit $ManifestPin
    } catch {
        $reason=$_.Exception.Message
        if (!$written -or $reason -eq 'BLOCKED_HOST_UPDATE_PERMISSION'){throw}
        # Restore only our own exact config revision. Concurrent writes require reconciliation.
        $null=Invoke-MarketplacePin $hostHome $commit $priorCommit $written.version
        $null=Invoke-CodexJson @('plugin','marketplace','upgrade',$market,'--json')
        Verify-Installation $hostHome $old.version $priorCommit $previousPin
        [IO.File]::Delete($journal)
        return @{status='FAILED_OLD_VERSION_RESTORED';version=$old.version;commit=$priorCommit;reason=$reason}
    }
    [IO.File]::Delete($journal)
    return @{status='INSTALLED_RESTART_REQUIRED';version=$TargetVersion;commit=$commit;enabled=$true;manifest_sha256=$ManifestPin;
        zip_sha256=$ZipPin;release_zip_bytes_verified=$false;staged_head=$commit;staged_channel_blob=$offer.channel_blob}
}

function Read-PublisherReceipt($calls, [string]$version) {
    $null=PreviewNumber $version
    $commit=Read-Commit 'heads/main'
    $path="product/research-preview/publisher-receipts/$version.json"
    $hits=@($calls | Where-Object {$_.tool -ceq 'github.fetch_file' -and $_.status -ceq 'completed' -and
        $_.arguments.repository_full_name -ceq $repo -and $_.arguments.ref -ceq $commit -and
        $_.arguments.path -ceq $path -and $_.arguments.encoding -ceq 'base64'})
    if ($hits.Count -ne 1){throw 'PUBLISHER_RECEIPT_MISSING'}
    $entry=$hits[0].result.structuredContent
    if ($entry.encoding -cne 'base64' -or $entry.content.Length -gt 4096){throw 'PUBLISHER_RECEIPT_FORMAT'}
    $bytes=[Convert]::FromBase64String($entry.content)
    $prefix=[Text.Encoding]::ASCII.GetBytes("blob "+$bytes.Length+[char]0)
    $sha=[Security.Cryptography.SHA1]::Create()
    try {$blob=([BitConverter]::ToString($sha.ComputeHash([byte[]]($prefix+$bytes)))).Replace('-','').ToLowerInvariant()}finally{$sha.Dispose()}
    if ($entry.sha -cne $blob){throw 'PUBLISHER_BLOB_MISMATCH'}
    $raw=[Text.UTF8Encoding]::new($false,$true).GetString($bytes)
    $r=$raw|ConvertFrom-Json
    $keys=@('schema','repository','channel','product','plugin_id','release_id','version','source_commit','zip_sha256','manifest_sha256')
    if ((Compare-Object -CaseSensitive $keys @($r.PSObject.Properties.Name)) -or $r.schema -ne 1 -or
        $r.product -cne $product -or $r.channel -cne 'plugin-creator-private' -or $r.repository -cne $repo -or
        $r.version -cne $version -or $r.plugin_id -cne 'plugins_6af978c244ec8191ba521a0eb8bb949d' -or
        $r.release_id -cnotmatch '^pluginrel_[0-9a-f]{32}$' -or $r.source_commit -cnotmatch '^[0-9a-f]{40}$' -or
        $r.manifest_sha256 -cnotmatch '^[0-9a-f]{64}$' -or $r.zip_sha256 -cnotmatch '^[0-9a-f]{64}$'){throw 'PUBLISHER_IDENTITY_MISMATCH'}
    # Publisher files contain only flat ASCII identifiers; reject duplicate keys and JSON escapes.
    if ($raw.Contains('\') -or [regex]::Matches($raw,'"[a-z_0-9]+"\s*:').Count -ne $keys.Count){throw 'PUBLISHER_RECEIPT_FORMAT'}
    return @{receipt=$r;commit=$commit;blob=$blob}
}
function Read-PrivateInstall($receipt,$folder,$marketName) {
    $si=[Diagnostics.ProcessStartInfo]::new()
    $si.FileName=(Get-Command codex.exe -CommandType Application|Select-Object -First 1).Source
    $si.Arguments='app-server --stdio';$si.UseShellExecute=$false;$si.CreateNoWindow=$true
    $si.RedirectStandardInput=$true;$si.RedirectStandardOutput=$true;$si.RedirectStandardError=$true
    $si.StandardOutputEncoding=[Text.UTF8Encoding]::new($false)
    $p=[Diagnostics.Process]::Start($si)
    try {
        $p.BeginErrorReadLine()
        $null=Invoke-PinRpc $p 1 initialize @{clientInfo=@{name='gdcae-handoff';version='1'};capabilities=@{}}
        Send-RpcLine $p '{"method":"initialized","params":{}}'
        $detail=(Invoke-PinRpc $p 2 'plugin/read' @{remoteMarketplaceName=$marketName;pluginName=$receipt.plugin_id}).plugin
        $body=(Invoke-PinRpc $p 3 'plugin/skill/read' @{remoteMarketplaceName=$marketName;remotePluginId=$receipt.plugin_id;skillName='setup'}).contents
        Assert-PrivateInstall $detail $body $receipt $folder $marketName
    } finally {if (!$p.HasExited){$p.Kill()};$p.Dispose()}
}
function Assert-PrivateInstall($detail,$body,$receipt,$folder,$marketName) {
    $s=$detail.summary
    if ($detail.marketplaceName -cne $marketName -or $s.source.type -cne 'remote' -or
        $s.remotePluginId -cne $receipt.plugin_id -or $s.id -cne "$product@$marketName" -or
        $s.name -cne $product -or !$s.installed -or !$s.enabled -or $s.localVersion -cne $receipt.version){throw 'HOST_INSTALL_IDENTITY_MISMATCH'}
    $path=Join-Path $folder 'skills/setup/SKILL.md'
    $skills=@($detail.skills | Where-Object {$_.name -ceq 'setup' -and $_.enabled})
    if ($skills.Count -ne 1 -or !$body -or $body.Length -gt 1048576){throw 'HOST_INSTALLED_SKILL_UNVERIFIED'}
    $sha=[Security.Cryptography.SHA256]::Create()
    try {$hash=[BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($body))).Replace('-','')}finally{$sha.Dispose()}
    if ((Get-FileHash -LiteralPath $path).Hash -ne $hash){throw 'HOST_INSTALLED_SKILL_UNVERIFIED'}
}
function Test-HandoffFiles($folder,$version,$pin) {
    # Do not load any package code here. Pin the manifest before using its file map.
    $manifest=Join-Path $folder 'package-manifest.json'
    if ((Get-FileHash -LiteralPath $manifest).Hash -ne $pin){throw 'PACKAGE_MANIFEST_MISMATCH'}
    $m=Get-Content -Raw -Encoding UTF8 -LiteralPath $manifest | ConvertFrom-Json
    if ($m.version -cne $version){throw 'PACKAGE_IDENTITY'}
    foreach ($name in 'package-manifest.json','scripts/main-handoff.ps1','scripts/runtime-checks.ps1','skills/setup/SKILL.md'){
        $item=Get-Item -Force -LiteralPath (Join-Path $folder $name)
        while ($item){
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'UNSAFE_TREE'}
            if ($item -is [IO.FileInfo]){$item=$item.Directory}else{$item=$item.Parent}
        }
        if ($name -ne 'package-manifest.json' -and ((Get-FileHash -LiteralPath (Join-Path $folder $name)).Hash -ne $m.files.$name)){throw 'PACKAGE_BYTES'}
    }
}
function Get-HandoffIdentity($folder) {
    $folder=(Get-Item -LiteralPath $folder).FullName
    $meta=Get-Content -LiteralPath (Join-Path $folder 'plugin.json') -Encoding UTF8 -Raw | ConvertFrom-Json
    $version=$meta.version
    $null=PreviewNumber $version
    if ($meta.name -cne $product){throw 'PACKAGE_IDENTITY'}
    $cache=Join-Path (Get-HostHome) 'plugins/cache'
    $marketName=(Get-Item -LiteralPath $folder).Parent.Parent.Name
    if ($folder -ne [IO.Path]::GetFullPath((Join-Path $cache "$marketName/$product/$version"))){throw 'HOST_INSTALL_LOCATION_MISMATCH'}
    $connectorCalls=@(Get-ConnectorCalls -ForHandoff)
    if ($marketName -ceq $market){
        $ref=(Invoke-MarketplacePin (Get-HostHome)).ref
        if ($ref -cnotmatch '^[0-9a-f]{40}$'){throw 'PIN_MISMATCH'}
        $manifest=Get-ReleaseManifestPin $version $ref
        Verify-Installation (Get-HostHome) $version $ref $manifest
        return @{status='VERIFIED_RELEASE_IDENTITY';channel='git-marketplace';version=$version;commit=$ref;manifest_sha256=$manifest}
    }
    if ($marketName -cnotin 'created-by-me-remote','shared-with-me','shared-with-me-remote'){throw 'UNSUPPORTED_INSTALL_SOURCE'}
    $proof=Read-PublisherReceipt $connectorCalls $version
    Read-PrivateInstall $proof.receipt $folder $marketName
    Test-HandoffFiles $folder $version $proof.receipt.manifest_sha256
    return @{status='VERIFIED_RELEASE_IDENTITY';channel=$proof.receipt.channel;version=$version;release_id=$proof.receipt.release_id;
        plugin_id=$proof.receipt.plugin_id;receipt_commit=$proof.commit;receipt_blob=$proof.blob;manifest_sha256=$proof.receipt.manifest_sha256}
}

function Get-StateDirectory {
    $base=if($env:PLUGIN_DATA -and !$operation){$env:PLUGIN_DATA}else{$env:LOCALAPPDATA}
    if (!$base -or $base -notmatch '^[A-Za-z]:[\\/]' -or $base -match '(^|[\\/])\.\.([\\/]|$)'){throw 'LOCAL_STATE_UNAVAILABLE'}
    $dir=if ($env:PLUGIN_DATA -and !$operation){Join-Path $base 'gdcae-update'}else{Join-Path $base 'GDCAE\plugin-updates'}
    if ($operation){
        $hasher=[Security.Cryptography.SHA256]::Create()
        try{$scope=[BitConverter]::ToString($hasher.ComputeHash([Text.Encoding]::UTF8.GetBytes((Get-HostHome).ToLowerInvariant()))).Replace('-','')}finally{$hasher.Dispose()}
        $dir=Join-Path $dir $scope
    }
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
    if (!$v.offer.PSObject.Properties['zip_sha256'] -or $v.offer.zip_sha256 -cnotmatch '^[0-9a-f]{64}$' -or
        $v.offer.manifest_sha256 -cnotmatch '^[0-9a-f]{64}$' -or $v.offer.change -cnotin 'auto-update','project-main','preview-fixes'){throw 'CACHE_INVALID'}
    $result=Compare-Offer $v.offer $local
    $result.checked_utc_epoch=$v.checked
    $result.expires_utc_epoch=$v.expires
    return $result
}
function Write-CheckCache($file,$offer,$checked) {
    $v=@{schema=2;product=$product;channel=$branch;version=$local;checked=$checked}
    if ($null -eq $offer){$v.kind='restricted';$v.expires=$checked+180}
    else {$v.kind='offer';$v.expires=$checked+3600;$v.offer=@{version=$offer.version;manifest_sha256=$offer.manifest_sha256;zip_sha256=$offer.zip_sha256;change=$offer.change}}
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

if ($Action -eq 'handoff-identity'){
    try {
        if ($PSBoundParameters.Keys | Where-Object {$_ -notin 'Action','InstalledRoot'}){throw 'INVALID_IDENTITY_ARGUMENTS'}
        $folder=if ($InstalledRoot){$InstalledRoot}else{$root}
        Get-HandoffIdentity $folder | ConvertTo-Json -Compress
        exit 0
    }catch{
        $reason=$_.Exception.Message
        if ($reason -cnotmatch '^[A-Z_]{3,64}$'){$reason='HOST_OR_PROOF_UNAVAILABLE'}
        @{status='RELEASE_IDENTITY_UNAVAILABLE';reason=$reason}|ConvertTo-Json -Compress
        exit 2
    }
}
$mode=@{hook='SESSIONSTART_AUTO_CHECK';'skill-check'='FIRST_SKILL_USE_CHECK';check='MANUAL_CHECK';install='CONFIRMED_INSTALL';
    'pin-current'='CONFIRMED_MIGRATION';verify='INSTALLED_READBACK';identity='INSTALLED_IDENTITY';offer='VERIFIED_OFFER'}[$Action]
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
$reportedCurrent=if ($Action -eq 'install'){$null}else{$local}
$lock=$null
$result=$null
$httpStatus=$null
$hostExit=$null
$cacheState='MISS'
$operation=$Action -in 'install','pin-current','verify','identity','offer'
$store=if($env:PLUGIN_DATA -and !$operation){'PLUGIN_DATA'}else{'LOCALAPPDATA'}
try {
    if ($Action -in 'install','pin-current' -and !$ConfirmUpdate){throw 'CONFIRM_EXACT_OFFER'}
    if ($Action -eq 'install'){
        $null=PreviewNumber $TargetVersion
        if ($FromCommit -cnotmatch '^[0-9a-f]{40}$' -or $TargetCommit -cnotmatch '^[0-9a-f]{40}$' -or
            $ManifestPin -cnotmatch '^[0-9a-f]{64}$' -or $ZipPin -cnotmatch '^[0-9a-f]{64}$'){throw 'CONFIRM_EXACT_OFFER'}
        $configured=(Invoke-MarketplacePin (Get-HostHome)).ref
        if ($configured -cnotmatch '^[0-9a-f]{40}$'){throw 'MIGRATION_REQUIRED'}
        if ($configured -cnotin $FromCommit,$TargetCommit){throw 'PIN_CONFLICT'}
        $reportedCurrent=(Get-Installed).version
    }
    if ($Action -ne 'offer'){try {
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
        if($operation){throw $cacheState}
        if($cacheState -eq 'BUSY'){$result=@{status='BUSY';current=$local}}
    }}
    if ($lock -and !$operation){
        try {$result=Read-CheckCache $file;if ($result){$cacheState='HIT'}}
        catch {$cacheState='CORRUPT_OR_UNREADABLE'}
    }
    if ($Action -in 'install','offer','pin-current'){$connectorCalls=@(Get-ConnectorCalls)}
    if ($Action -eq 'offer'){
        $offer=Get-ConnectorOffer
        $installed=Get-Installed
        $from=(Invoke-MarketplacePin (Get-HostHome)).ref
        $baselinePin=Get-ReleaseManifestPin $installed.version $from
        Verify-Installation (Get-HostHome) $installed.version $from $baselinePin
        $result=Compare-Offer $offer $installed.version
        $result.from_commit=$from
        $result.target_commit=$offer.target_commit
        $result.release_zip_bytes_verified=$false
    }
    if ($Action -eq 'pin-current'){$result=Pin-Current}
    if ($Action -eq 'identity'){
        $homePath=Get-HostHome
        $ref=(Invoke-MarketplacePin $homePath).ref
        if ($ref -cnotmatch '^[0-9a-f]{40}$'){throw 'MIGRATION_REQUIRED'}
        $actual=Get-Installed
        $folder=Join-Path $homePath "plugins\cache\$market\$product\$($actual.version)"
        $digest=(Get-FileHash -LiteralPath (Join-Path $folder 'package-manifest.json')).Hash.ToLowerInvariant()
        Verify-Installation $homePath $actual.version $ref $digest
        $result=@{status='FIXED_BASELINE';version=$actual.version;commit=$ref;manifest_sha256=$digest;enabled=$true}
    }
    if ($Action -eq 'verify'){
        $null=PreviewNumber $TargetVersion
        if ($TargetCommit -cnotmatch '^[0-9a-f]{40}$' -or $ManifestPin -cnotmatch '^[0-9a-f]{64}$'){throw 'INSTALL_IDENTITY_REQUIRED'}
        Verify-Installation (Get-HostHome) $TargetVersion $TargetCommit $ManifestPin
        $result=@{status='VERIFIED_INSTALLATION';version=$TargetVersion;enabled=$true;commit=$TargetCommit;manifest_sha256=$ManifestPin}
        $pending=Join-Path $state 'pending.json'
        if ($ConfirmUpdate -and [IO.File]::Exists($pending)){
            $j=Get-Content -LiteralPath $pending -Raw -Encoding UTF8 | ConvertFrom-Json
            if ($j.instance -ne (Get-HostHome) -or !(($j.target_commit -ceq $TargetCommit -and $j.target_manifest -ceq $ManifestPin) -or
                ($j.previous_commit -ceq $TargetCommit -and $j.previous_manifest -ceq $ManifestPin))){throw 'PENDING_RECONCILIATION'}
            [IO.File]::Delete($pending)
            $result.reconciled=$true
        }
    }
    if (!$result){
        $offer=if ($Action -eq 'install'){Get-ConnectorOffer}else{Get-Offer}
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
    $status=if ($code -eq 'BLOCKED_HOST_UPDATE_PERMISSION'){$code}elseif($liveWrite){'UNKNOWN_AFTER_HOST_WRITE'}elseif($operation){'BLOCKED'}else{'CHECK_UNAVAILABLE'}
    $result=@{status=$status;reason=$code;current=$reportedCurrent;entry_version=$local}
    if ($code -ceq 'HOST_NETWORK_RESTRICTED' -and $lock -and !$operation){
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
if ($operation -and $result.status -notin 'INSTALLED_RESTART_REQUIRED','ALREADY_INSTALLED','PINNED_CURRENT','VERIFIED_INSTALLATION','FIXED_BASELINE','AVAILABLE','CURRENT','CHANNEL_BEHIND'){$rc=2}
$result.exit_code=$rc
if ($Action -eq 'hook') {
    @{hookSpecificOutput=@{hookEventName='SessionStart';additionalContext=('GD-CAE update receipt '+($result | ConvertTo-Json -Compress))}} | ConvertTo-Json -Depth 4 -Compress
} else {$result | ConvertTo-Json -Compress}
exit $rc
