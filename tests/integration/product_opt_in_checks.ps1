param([Parameter(Mandatory)][string]$Plugin,[Parameter(Mandatory)][string]$Work,
      [Parameter(Mandatory)][string]$PreviousTree,[Parameter(Mandatory)][string]$PreviousCommit,
      [Parameter(Mandatory)][string]$TargetCommit,
      [Parameter(Mandatory)][string]$TargetTree,[string]$Updater)
$ErrorActionPreference='Stop'
$Plugin=(Get-Item $Plugin).FullName
$state=(New-Item -ItemType Directory -Path $Work).FullName
if (!$Updater){$Updater=Join-Path $Plugin 'scripts/update.ps1'}
$ast=[Management.Automation.Language.Parser]::ParseFile($Updater,[ref]$null,[ref]$null)
foreach($f in $ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst]},$false)){
    . ([scriptblock]::Create($f.Extent.Text))
}
$market='gdcae-research-preview';$product='gdcae-research';$id="$product@$market"
$origin='https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator.git'
$branch='gdcae-preview'
$FromCommit=$PreviousCommit
$TargetVersion=(Get-Content (Join-Path $Plugin 'plugin.json') -Raw|ConvertFrom-Json).version
$previousFolder=Join-Path $PreviousTree "plugins/$product"
$previousVersion=(Get-Content (Join-Path $previousFolder 'plugin.json') -Raw|ConvertFrom-Json).version
$oldPin=(Get-FileHash (Join-Path $previousFolder 'package-manifest.json')).Hash.ToLowerInvariant()
$ManifestPin=(Get-FileHash (Join-Path $Plugin 'package-manifest.json')).Hash.ToLowerInvariant()
$ZipPin='7'*64
$offer=@{version=$TargetVersion;manifest_sha256=$ManifestPin;zip_sha256=$ZipPin;target_commit=$TargetCommit;
    channel_blob=(& git -C $TargetTree rev-parse HEAD:channel.json)}
$ConfirmUpdate=$true
$originalReview=(Get-Item Function:Review-Package).ScriptBlock
$originalSave=(Get-Item Function:Save-RecoveryPackage).ScriptBlock
# Only the transport/Host boundaries below are fixtures. Real package bytes,
# manifest verification, transaction sequencing and recovery use the shipped code.
function Get-ReleaseManifestPin {return $oldPin}
function Get-Installed {return @{version=$previousVersion}}
function Invoke-MarketplacePin($homePath,$expected,$replacement,$revision){
    if ($replacement){
        if ($script:ref -cne $expected -or $script:revision -ne $revision){throw 'PIN_CONFLICT'}
        $script:ref=$replacement
        $script:revision++
        $script:writes+=$replacement
    }
    return @{ref=$script:ref;version=$script:revision}
}
function Review-Package($folder,$pin,$version){
    $source=if ($version -ceq $previousVersion){$previousFolder}else{$Plugin}
    & $originalReview $source $pin $version
}
function Save-RecoveryPackage($folder,$pin,$version,$commit,$directory){
    & $originalSave $previousFolder $pin $version $commit $directory
    & $originalReview (Join-Path $directory ("known-good-"+$commit)) $pin $version
}
function Invoke-CodexJson($arguments){
    $op=$arguments -join ' '
    if ($op -like 'plugin marketplace list*'){return @{marketplaces=@(@{name=$market;root=$PreviousTree})}}
    if ($op -like 'plugin marketplace add*'){return @{marketplaceName=$market;installedRoot=$(if($script:fault -eq 'wrong-head'){$PreviousTree}else{$TargetTree})}}
    if ($op -like 'plugin add*'){return @{version=$TargetVersion;installedPath=$Plugin}}
    if ($op -like 'plugin marketplace upgrade*'){
        if ($script:ref -ceq $TargetCommit){
            if ($script:fault -eq 'concurrent'){$script:revision++}
            if ($script:fault){throw 'HOST_COMMAND_FAILED'}
        }
        return @{errors=@();selectedMarketplaces=@($market)}
    }
    throw 'UNEXPECTED_HOST_COMMAND'
}
function Verify-Installation($homePath,$version,$commit,$pin){
    if ($script:ref -cne $commit){throw 'PIN_MISMATCH'}
    Review-Package '' $pin $version
}
$results=@()
foreach ($fault in @('wrong-head','','refresh','concurrent')){
    $script:ref=$FromCommit;$script:revision=1;$script:writes=@();$script:fault=$fault
    try{$status=(Install-Offer $offer).status}catch{$status=$_.Exception.Message}
    $pending=Test-Path (Join-Path $state 'pending.json')
    switch ($fault) {
        'wrong-head' {if ($status -ne 'STAGED_HEAD_MISMATCH' -or $writes.Count -or $pending){throw "stage: $status"}}
        '' {if ($status -ne 'INSTALLED_RESTART_REQUIRED' -or $ref -ne $TargetCommit -or $pending){throw "success: $status"}}
        'refresh' {if ($status -ne 'FAILED_OLD_VERSION_RESTORED' -or $ref -ne $FromCommit -or $pending){throw "restore: $status"}}
        'concurrent' {if ($status -ne 'PIN_CONFLICT' -or !$pending -or $writes.Count -ne 1){throw "conflict: $status"}}
    }
    $results+=@{fault=$fault;status=$status;writes=$writes;pending=$pending}
}
$results | ConvertTo-Json -Depth 4
