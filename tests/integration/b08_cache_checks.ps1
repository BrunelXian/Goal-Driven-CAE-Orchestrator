param([Parameter(Mandatory)][string]$Plugin,[Parameter(Mandatory)][string]$Work)
$ErrorActionPreference='Stop'
$null=New-Item -ItemType Directory -Path $Work
$env:PLUGIN_DATA=$Work
$driver=Join-Path $Plugin 'scripts/update.ps1'
$file=Join-Path $Work 'gdcae-update/check-v2.json'
$rows=[ordered]@{}
function Check($name,$status,$cache) {
    $result=& powershell.exe -NoProfile -File $driver -Action check | ConvertFrom-Json
    if ($LASTEXITCODE -ne 0 -or $result.status -cne $status -or $result.cache -cne $cache -or $result.cache_store -cne 'PLUGIN_DATA'){
        throw "$name returned $($result | ConvertTo-Json -Compress)"
    }
    $rows[$name]=$result
}
Check first CHANNEL_BEHIND STORED
Check hit CHANNEL_BEHIND HIT
[IO.File]::WriteAllText($file,'{')
Check corrupt CHANNEL_BEHIND REPAIRED
$v=Get-Content -Raw $file | ConvertFrom-Json
$v.checked-=7200
$v.expires-=7200
[IO.File]::WriteAllText($file,($v|ConvertTo-Json))
Check expired CHANNEL_BEHIND STORED
$v=Get-Content -Raw $file | ConvertFrom-Json
$v.version='0.2.0-preview.8'
[IO.File]::WriteAllText($file,($v|ConvertTo-Json))
Check foreign_version CHANNEL_BEHIND STORED
$env:PLUGIN_DATA=$file
Check unwritable CHANNEL_BEHIND LOCAL_STATE_UNWRITABLE
$rows | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $Work 'result.json') -Encoding UTF8
