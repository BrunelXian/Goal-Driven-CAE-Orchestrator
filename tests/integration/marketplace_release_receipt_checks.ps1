param([Parameter(Mandatory)][string]$Updater,[Parameter(Mandatory)][string]$TargetTree)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$ast=[Management.Automation.Language.Parser]::ParseFile($Updater,[ref]$null,[ref]$null)
foreach ($f in $ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst]},$false)){
    . ([scriptblock]::Create($f.Extent.Text))
}
$repo='BrunelXian/Goal-Driven-CAE-Orchestrator'
$branch='gdcae-preview'
$product='gdcae-research'
$commit=(& git -C $TargetTree rev-parse HEAD)
$blob=(& git -C $TargetTree rev-parse HEAD:channel.json)
$raw=[IO.File]::ReadAllBytes((Join-Path $TargetTree 'channel.json'))
$channel=[Text.Encoding]::UTF8.GetString($raw)|ConvertFrom-Json
$tag="gdcae-research-$($channel.version)"
$base="https://api.github.com/repos/$repo"
function JsonCall($suffix,$body){
    @{tool='github.fetch';status='completed';arguments=@{url="$base/$suffix"};
        result=@{structuredContent=@{content=($body|ConvertTo-Json -Depth 8)}}}
}
function Asset($name,$digest){
    @{id=1;name=$name;state='uploaded';size=10;digest="sha256:$digest";
        browser_download_url="https://github.com/$repo/releases/download/$tag/$name"}
}
$rel=@{html_url="https://github.com/$repo/releases/tag/$tag";tag_name=$tag;draft=$false;prerelease=$true;
    assets=@((Asset 'package-manifest.json' $channel.manifest_sha256),(Asset "CAE-Agent-Research-Preview-$($channel.version)_PUBLIC_DIRECTORY.zip" $channel.zip_sha256))}
$head=JsonCall "git/ref/heads/$branch" @{ref="refs/heads/$branch";object=@{type='commit';sha=$commit}}
$ref=JsonCall "git/ref/tags/$tag" @{ref="refs/tags/$tag";object=@{type='commit';sha=$commit}}
$file=@{tool='github.fetch_file';status='completed';arguments=@{repository_full_name=$repo;path='channel.json';ref=$commit;encoding='base64'};
    result=@{structuredContent=@{encoding='base64';content=[Convert]::ToBase64String($raw);sha=$blob}}}
function Assert-Rejection($reason,[scriptblock]$run){
    try {& $run | Out-Null}catch{if($_.Exception.Message -ceq $reason){return};throw}
    throw "Expected rejection: $reason"
}
$release=JsonCall "releases/tags/$tag" $rel
$connectorCalls=@($head,$ref,$file,$release)
$offer=Get-ConnectorOffer
if ($offer.target_commit -cne $commit -or $offer.channel_blob -cne $blob){throw 'offer mismatch'}
Assert-StagedRef $TargetTree $offer.target_commit $offer.channel_blob
Assert-Rejection 'STAGED_CHANNEL_MISMATCH' {Assert-StagedRef $TargetTree $commit ('0'*40)}
$connectorCalls+=$release
Assert-Rejection 'CONNECTOR_PROOF_MISSING' {Get-ConnectorOffer}
$connectorCalls=@($head,$ref,$file,$release)
$file.arguments.ref=$branch
Assert-Rejection 'CONNECTOR_CHANNEL_MISSING' {Get-ConnectorOffer}
$file.arguments.ref=$commit
$rel.assets[1].digest='sha256:'+('0'*64)
$connectorCalls=@($head,$ref,$file,(JsonCall "releases/tags/$tag" $rel))
Assert-Rejection 'RELEASE_DIGEST_MISMATCH' {Get-ConnectorOffer}
$rel.draft=$true
$connectorCalls=@($head,$ref,$file,(JsonCall "releases/tags/$tag" $rel))
Assert-Rejection 'RELEASE_IDENTITY' {Get-ConnectorOffer}
'PASS: fixed-commit channel, Git blob, duplicate endpoint, moving ref, release digest, draft release'
