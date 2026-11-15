param([Parameter(Mandatory)][string]$Plugin,[Parameter(Mandatory)][string]$Receipt,[Parameter(Mandatory)][string]$FreshWork)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$folder=(New-Item -ItemType Directory -Path $FreshWork -ErrorAction Stop).FullName
$driver=Join-Path $Plugin 'scripts/update.ps1'
$ast=[Management.Automation.Language.Parser]::ParseFile($driver,[ref]$null,[ref]$null)
foreach($node in $ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst]},$false)){
    . ([scriptblock]::Create($node.Extent.Text))
}
$repo='BrunelXian/Goal-Driven-CAE-Orchestrator'
$product='gdcae-research'
$proof=Get-Content -Raw -Encoding UTF8 -LiteralPath $Receipt | ConvertFrom-Json
$commit='a'*40
$refUrl="https://api.github.com/repos/$repo/git/ref/heads/main"
function FileCall($receipt){
    $bytes=[Text.Encoding]::UTF8.GetBytes(($receipt|ConvertTo-Json -Compress))
    $sha=[Security.Cryptography.SHA1]::Create()
    try {$blob=[BitConverter]::ToString($sha.ComputeHash([byte[]]([Text.Encoding]::ASCII.GetBytes('blob '+$bytes.Length+[char]0)+$bytes))).Replace('-','').ToLowerInvariant()}finally{$sha.Dispose()}
    return [pscustomobject]@{tool='github.fetch_file';status='completed';arguments=@{ref=$commit;path="product/research-preview/publisher-receipts/$($receipt.version).json";repository_full_name=$repo;encoding='base64'};
        result=@{structuredContent=@{encoding='base64';sha=$blob;content=[Convert]::ToBase64String($bytes)}}}
}
function Denied($reason,[scriptblock]$test){
    $errorCode='';try{& $test|Out-Null}catch{$errorCode=$_.Exception.Message}
    if ($errorCode -cne $reason){throw "Expected $reason, got $errorCode"}
}
$ref=@{tool='github.fetch';status='completed';arguments=@{url=$refUrl};result=@{structuredContent=@{content=(@{ref='refs/heads/main';object=@{type='commit';sha=$commit}}|ConvertTo-Json -Compress)}}}
foreach ($version in '0.2.0-preview.17','0.2.0-preview.91'){
    $proof.version=$version
    $call=FileCall $proof
    $connectorCalls=@($ref,$call)
    $got=Read-PublisherReceipt $connectorCalls $version
    if ($got.receipt.version -cne $version -or $got.receipt.manifest_sha256 -cne $proof.manifest_sha256){throw 'Positive fixture failed'}
}
$call.arguments.ref='main'
Denied 'PUBLISHER_RECEIPT_MISSING' {Read-PublisherReceipt $connectorCalls $proof.version}
$call.arguments.ref=$commit;$call.status='failed'
Denied 'PUBLISHER_RECEIPT_MISSING' {Read-PublisherReceipt $connectorCalls $proof.version}
$call.status='completed';$call.result.structuredContent.sha='f'*40
Denied 'PUBLISHER_BLOB_MISMATCH' {Read-PublisherReceipt $connectorCalls $proof.version}
$proof.plugin_id='plugins_'+('0'*32);$call=FileCall $proof
Denied 'PUBLISHER_IDENTITY_MISMATCH' {Read-PublisherReceipt @($ref,$call) $proof.version}
$proof=Get-Content -Raw -Encoding UTF8 -LiteralPath $Receipt|ConvertFrom-Json
$call=FileCall $proof;$call.arguments.path='product/research-preview/publisher-receipts/0.2.0-preview.92.json'
Denied 'PUBLISHER_IDENTITY_MISMATCH' {Read-PublisherReceipt @($ref,$call) '0.2.0-preview.92'}
$connectorCalls=@()
Denied 'CONNECTOR_PROOF_MISSING' {Read-PublisherReceipt @() $proof.version}
$target=Join-Path $folder 'package'
Copy-Item -Recurse -LiteralPath $Plugin -Destination $target
$pin=(Get-FileHash -LiteralPath (Join-Path $target 'package-manifest.json')).Hash
$version=(Get-Content -Raw -LiteralPath (Join-Path $target 'package-manifest.json')|ConvertFrom-Json).version
Test-HandoffFiles $target $version $pin
Denied 'PACKAGE_MANIFEST_MISMATCH' {Test-HandoffFiles $target $version ('0'*64)}
foreach ($name in 'scripts/main-handoff.ps1','scripts/runtime-checks.ps1','skills/setup/SKILL.md'){
    $file=Join-Path $target $name;$bytes=[IO.File]::ReadAllBytes($file)
    [IO.File]::AppendAllText($file,'changed')
    Denied 'PACKAGE_BYTES' {Test-HandoffFiles $target $version $pin}
    [IO.File]::WriteAllBytes($file,$bytes)
}
$summary=@{source=@{type='remote'};name=$product;id="$product@created-by-me-remote";remotePluginId=$proof.plugin_id;installed=$true;enabled=$true;localVersion=$proof.version}
$detail=@{summary=$summary;marketplaceName='created-by-me-remote';skills=@(@{name='setup';enabled=$true})}
$body=Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $target 'skills/setup/SKILL.md')
Assert-PrivateInstall $detail $body $proof $target 'created-by-me-remote'
Denied 'HOST_INSTALLED_SKILL_UNVERIFIED' {Assert-PrivateInstall $detail 'different content' $proof $target 'created-by-me-remote'}
$summary.localVersion='0.2.0-preview.1'
Denied 'HOST_INSTALL_IDENTITY_MISMATCH' {Assert-PrivateInstall $detail $body $proof $target 'created-by-me-remote'}
$summary.localVersion=$proof.version;$summary.remotePluginId='different'
Denied 'HOST_INSTALL_IDENTITY_MISMATCH' {Assert-PrivateInstall $detail $body $proof $target 'created-by-me-remote'}
Write-Output 'PASS: two version records, pinned provenance, source/role/skill identity and handoff payload rejection fixtures'
