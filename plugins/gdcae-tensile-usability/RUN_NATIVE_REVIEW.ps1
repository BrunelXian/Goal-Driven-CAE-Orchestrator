param([Parameter(Mandatory=$true)][string]$ArgumentsFile,
      [Parameter(Mandatory=$true)][string]$FreezeSha256)
& {
    $ErrorActionPreference = 'Stop'
    Import-Module 'C:\Windows\System32\WindowsPowerShell\v1.0\Modules\Microsoft.PowerShell.Utility\Microsoft.PowerShell.Utility.psd1' -ErrorAction Stop
    $root = $PSScriptRoot
    $freezePath = Join-Path $root 'FREEZE.json'
    if ((Get-FileHash -LiteralPath $freezePath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $FreezeSha256) { throw 'FREEZE_IDENTITY_MISMATCH' }
    $freeze = Get-Content -LiteralPath $freezePath -Raw | ConvertFrom-Json
    foreach ($property in $freeze.files.PSObject.Properties) {
        $file = Join-Path $root $property.Name
        if ((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant() -ne $property.Value) { throw "FROZEN_FILE_CHANGED: $($property.Name)" }
    }
    $request = Get-Content -LiteralPath $ArgumentsFile -Raw | ConvertFrom-Json
    $expected = @('schema','workspace','contract_pin','operation_id','evidence','scope','scope_pin')
    if ((($request.PSObject.Properties.Name | Sort-Object) -join ',') -ne (($expected | Sort-Object) -join ',')) { throw 'EXACT_REVIEW_ARGUMENTS_REQUIRED' }
    if ($request.schema -ne 'native-tensile-review-arguments-v1') { throw 'REVIEW_ARGUMENT_SCHEMA' }
    $python = 'D:\XianLab\envs\LangChainEnv\Scripts\python.exe'
    $entry = Join-Path $root 'gd\operator_entry.py'
    $argv = @('-I','-B','-S',$entry,'run','--python-exe',$python,'--package-pin',$freeze.package_pin,
      '--workspace',$request.workspace,'--contract-pin',$request.contract_pin,'--operation-id',$request.operation_id,
      '--evidence',$request.evidence,'--scope',$request.scope,'--scope-pin',$request.scope_pin)
    & $python @argv
    if ($LASTEXITCODE -ne 0) { throw "REVIEW_STOPPED_EXIT_$LASTEXITCODE" }
}
