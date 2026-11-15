param([Parameter(Mandatory)][string]$Plugin,[Parameter(Mandatory)][string]$Work)
$ErrorActionPreference='Stop'
$Plugin=(Get-Item -LiteralPath $Plugin).FullName
$Work=(New-Item -ItemType Directory -Path $Work -ErrorAction Stop).FullName
$driver=Join-Path $Plugin 'scripts/update.ps1'
$pin=(Get-FileHash -LiteralPath (Join-Path $Plugin 'package-manifest.json')).Hash.ToLower()
# Exercise the exact production functions, replacing network input only in these unit cases.
$ast=[Management.Automation.Language.Parser]::ParseFile($driver,[ref]$null,[ref]$null)
foreach($node in $ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst]},$false)){
    . ([scriptblock]::Create($node.Extent.Text))
}
$repo='BrunelXian/Goal-Driven-CAE-Orchestrator'
$product='gdcae-research'
$market='gdcae-research-preview'
$branch='gdcae-preview'
$id="$product@$market"
$current=(Get-Content -LiteralPath (Join-Path $Plugin 'plugin.json') -Raw | ConvertFrom-Json).version
$env:LOCALAPPDATA=$Work
$offer=[pscustomobject]@{version=$current;change='auto-update';manifest_sha256=$pin;zip_sha256=('1'*64)}
$results=@()
function Check($name,$ok){if(!$ok){throw "failed: $name"};$script:results+=$name}
function Refused($name,[scriptblock]$body,$code){
    $message=$null
    try {& $body | Out-Null} catch {$message=$_.Exception.Message}
    Check $name ($message -eq $code)
}
Check 'equal version' ((Compare-Offer $offer $current).status -eq 'CURRENT')
Check 'higher version' ((Compare-Offer $offer '0.2.0-preview.7').status -eq 'AVAILABLE')
Check 'older channel' ((Compare-Offer $offer ('0.2.0-preview.'+((PreviewNumber $current)+1))).status -eq 'CHANNEL_BEHIND')
$payload=[Text.Encoding]::UTF8.GetBytes('{"schema":1}')
$entry=[pscustomobject]@{type='file';path='channel.json';encoding='base64';size=$payload.Length;
    content=[Convert]::ToBase64String($payload);sha='0'*40}
Refused 'invalid Git blob digest' {ConvertTo-Offer $entry} 'METADATA_INTEGRITY_ERROR'
function Get-OfficialJson {return $entry}
$entry.content='invalid*'
Refused 'invalid GitHub content encoding' {Get-Offer} 'METADATA_FORMAT_ERROR'
$offerBody=@{schema=1;product=$product;version='0.2.0-preview.8';impact='restart-rebind-no-migration';change='auto-update';manifest_sha256=$pin;zip_sha256='1'*64}
$bytes=[Text.Encoding]::UTF8.GetBytes(($offerBody | ConvertTo-Json -Compress))
$content=[Convert]::ToBase64String($bytes)
$header=[Text.Encoding]::ASCII.GetBytes('blob '+$bytes.Length+[char]0)
$hasher=[Security.Cryptography.SHA1]::Create()
try {$blob=([BitConverter]::ToString($hasher.ComputeHash([byte[]]($header+$bytes)))).Replace('-','').ToLowerInvariant()} finally {$hasher.Dispose()}
$res=& powershell.exe -NoProfile -File $driver -Action skill-check -ChannelBase64 $content -ChannelBlobSha $blob | ConvertFrom-Json
Check 'connector uses existing version and blob checks' ($res.status -eq 'CHANNEL_BEHIND' -and $res.channel_blob_sha -ceq $blob -and $res.manifest_sha256 -ceq $pin -and $res.cache -ceq 'NOT_STORED')
$res=& powershell.exe -NoProfile -File $driver -Action skill-check -ChannelBase64 $content -ChannelBlobSha ('0'*40) | ConvertFrom-Json
Check 'tampered connector bytes rejected' ($res.reason -ceq 'METADATA_INTEGRITY_ERROR' -and $res.status -ceq 'CHECK_UNAVAILABLE')
$res=& powershell.exe -NoProfile -File $driver -Action skill-check -ChannelBase64 'bad*' -ChannelBlobSha $blob | ConvertFrom-Json
Check 'malformed connector data rejected' ($res.reason -ceq 'METADATA_FORMAT_ERROR')
$res=& powershell.exe -NoProfile -File $driver -Action install -ChannelBase64 $content -ChannelBlobSha $blob -ConfirmUpdate | ConvertFrom-Json
Check 'connector bytes cannot authorize an install' ($LASTEXITCODE -eq 2 -and $res.reason -ceq 'DISCOVERY_ONLY')
Refused 'unsupported version' {PreviewNumber '0.2.0-preview.8;command'} 'UNSUPPORTED_VERSION_SERIES'
$TargetVersion=$current;$ManifestPin=$pin;$ConfirmUpdate=$false
Refused 'confirmation absent' {Install-Offer $offer} 'CONFIRM_EXACT_OFFER'
$ConfirmUpdate=$true;$ManifestPin='0'*64
Refused 'changed offer' {Install-Offer $offer} 'CONFIRM_EXACT_OFFER'
Review-Package $Plugin $pin $current
Refused 'manifest mismatch' {Review-Package $Plugin ('0'*64) $current} 'PACKAGE_MANIFEST_MISMATCH'
$broken=Join-Path $Work 'broken'
Copy-Item -LiteralPath $Plugin -Destination $broken -Recurse
[IO.File]::AppendAllText((Join-Path $broken 'scripts/main.py'),'x')
Refused 'altered package' {Review-Package $broken $pin $current} 'PACKAGE_BYTES'
Refused 'incompatible metadata' {Review-Package $Plugin $pin '0.2.0-preview.99'} 'PACKAGE_IDENTITY'
$cached=Join-Path $Work 'GDCAE\plugin-updates'
[void][IO.Directory]::CreateDirectory($cached)
$now=[DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$entry=@{schema=2;product=$product;version=$current;channel=$branch;kind='offer';checked=$now;expires=$now+3600;
    offer=@{version='0.2.0-preview.99';manifest_sha256=$pin;change='preview-fixes';changes='REMOTE_COMMAND_MUST_NOT_APPEAR'}}
[IO.File]::WriteAllText((Join-Path $cached 'check-v2.json'),($entry | ConvertTo-Json -Depth 4))
$hook=& powershell.exe -NoProfile -File $driver -Action hook
Check 'hook emits only locally rendered metadata' (($hook -join '') -match 'additionalContext' -and ($hook -join '') -notmatch 'REMOTE_COMMAND')
$lock=[IO.File]::Open((Join-Path $cached 'channel.lock'),'OpenOrCreate','ReadWrite','None')
try {$busy=& powershell.exe -NoProfile -File $driver -Action check | ConvertFrom-Json; Check 'concurrent check' ($busy.status -eq 'BUSY')}finally{$lock.Dispose()}
$results | ConvertTo-Json | Set-Content (Join-Path $Work 'results.json') -Encoding UTF8
$results
