# Exercise the packaged RPC implementation against an empty, disposable Git marketplace.
param([Parameter(Mandatory)][string]$Plugin,[Parameter(Mandatory)][string]$Work)
$ErrorActionPreference='Stop'
$env:CODEX_HOME=(New-Item -ItemType Directory -Path $Work).FullName
$market='gdcae-research-preview'
$origin='https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator.git'
$old='2990ffe68a2bc391d7750d0a93eb359caaf13506'
$next='1a01e89fd1a568e9aaaf7da80da7254bb027421c'
$missing='f'*40
$ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $Plugin 'scripts/update.ps1'),[ref]$null,[ref]$null)
foreach($f in $ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst]},$false)){
    . ([scriptblock]::Create($f.Extent.Text))
}
$registered=Invoke-CodexJson @('plugin','marketplace','add',$origin,'--ref',$old,'--sparse','.agents/plugins','--sparse','plugins/gdcae-research','--json')
$first=Invoke-MarketplacePin $env:CODEX_HOME
if ($first.ref -cne $old){throw 'registration mismatch'}
$err=$null
try{$null=Invoke-MarketplacePin $env:CODEX_HOME $old $next 'outdated-version'}catch{$err=$_.Exception.Message}
if ($err -cne 'PIN_CONFLICT' -or (Invoke-MarketplacePin $env:CODEX_HOME).ref -cne $old){throw 'stale configuration changed'}
$written=Invoke-MarketplacePin $env:CODEX_HOME $old $missing $first.version
try{$ErrorActionPreference='Continue';$null=& codex.exe plugin marketplace upgrade $market --json 2>&1;$failure=$LASTEXITCODE}
finally{$ErrorActionPreference='Stop'}
$head=git -C $registered.installedRoot rev-parse HEAD
if (!$failure -or $head -cne $old){throw 'missing target did not retain prior snapshot'}
$back=Invoke-MarketplacePin $env:CODEX_HOME $missing $old $written.version
$null=Invoke-CodexJson @('plugin','marketplace','upgrade',$market,'--json')
$stable=Invoke-MarketplacePin $env:CODEX_HOME
$null=Invoke-MarketplacePin $env:CODEX_HOME $old $next $stable.version
$refresh=Invoke-CodexJson @('plugin','marketplace','upgrade',$market,'--json')
$verified=Invoke-MarketplacePin $env:CODEX_HOME
$head=git -C $registered.installedRoot rev-parse HEAD
if ($refresh.errors.Count -or $verified.ref -cne $next -or $head -cne $next){throw 'persistent ref mismatch'}
if (@((Invoke-CodexJson @('plugin','list','--json')).installed|Where-Object name -CEQ 'gdcae-research').Count){throw 'unexpected plugin'}
@{stale_rejected=$true;missing_exit=$failure;retained=$old;recovered_ref=$back.ref;new_ref=$verified.ref;new_head=$head;installed_gdcae=0} | ConvertTo-Json
