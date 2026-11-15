param([Parameter(Mandatory)][string]$plugin, [Parameter(Mandatory)][string]$work, [Parameter(Mandatory)][int]$FixturePort)
$ErrorActionPreference='Stop'
. (Join-Path $plugin 'scripts/runtime-checks.ps1')
$spec=Get-Content (Join-Path $plugin 'runtime/cpython-windows.json') -Raw | ConvertFrom-Json
function Denied($name,$expected,[scriptblock]$operation){
    $message=$null
    try { & $operation } catch {$message=$_.Exception.Message}
    if (!$message -or $message -notmatch $expected) {throw "FAILED $name $message"}
    [pscustomobject]@{case=$name; error=$message}
}
$rows=@()
$rows+=Denied space 'INSUFFICIENT_DISK_SPACE' {Assert-RuntimeSpace 100 $spec}
$rows+=Denied digest 'ARCHIVE_SHA256_MISMATCH' {Expand-RuntimeArchive $PSCommandPath "$work/unused" $spec}
Add-Type -AssemblyName System.IO.Compression.FileSystem
foreach($case in 'path','duplicate','size','extra') {
    $file=Join-Path $work "$case.zip"
    $z=[IO.Compression.ZipFile]::Open($file,'Create')
    try {
        $name=@{path='../outside';duplicate='LICENSE.txt';size='python312.zip';extra='new.txt'}[$case]
        [void]$z.CreateEntry($name)
        if($case -eq 'duplicate'){[void]$z.CreateEntry($name)}
    }finally{$z.Dispose()}
    $fixture=Get-Content (Join-Path $plugin 'runtime/cpython-windows.json') -Raw | ConvertFrom-Json
    $fixture.archive_sha256=(Get-FileHash $file).Hash
    if($case -eq 'duplicate'){$fixture.files.'LICENSE.txt'.size=0}
    $rows+=Denied $case 'UNSAFE_ARCHIVE_PATH|ARCHIVE_MEMBER_MISMATCH' {Expand-RuntimeArchive $file "$work/unused" $fixture}
}
$localSpec=Get-Content (Join-Path $plugin 'runtime/cpython-windows.json') -Raw | ConvertFrom-Json
foreach($case in 'missing','redirect','offline','short') {
    $localSpec.url=if($case -eq 'offline'){'http://127.0.0.1:1/unreachable'}else{"http://127.0.0.1:$FixturePort/$case"}
    $rows+=Denied $case '404|refused|拒绝|UNEXPECTED_HTTP_RESPONSE|DOWNLOAD_SIZE_MISMATCH' {Receive-RuntimeArchive $localSpec "$work/$case.bin"}
}
$rows | ConvertTo-Json
