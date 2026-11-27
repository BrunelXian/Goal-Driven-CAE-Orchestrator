# Recheck one frozen T3D2 case with PowerShell 5.1+.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$culture = [System.Globalization.CultureInfo]::InvariantCulture

$hashes = @{
    'axial_bar.inp' = '189e9b438c117e86eba0997ca12ef5d786ee013631e05c2e2cede39d2a70fe68'
    'tip-table.txt' = '1a155ab9e9506965e0074b3069a923c56fcb825b0051b93ac8519447fbd6e2f5'
    'u2.json'       = '577edcb8048709663f107981d9b406f539bd102a520076d5a5e6195ad1eddd38'
}
foreach ($file in $hashes.Keys) {
    $hash = (Get-FileHash -LiteralPath (Join-Path $PSScriptRoot $file) -Algorithm SHA256).Hash
    if ($hash -ne $hashes[$file]) { throw "SHA-256 mismatch for $file" }
}

# These exact cards and row layouts are fixed by the input digest.
$deck = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'axial_bar.inp')
function Get-CardRow([string] $keyword, [int] $offset = 1) {
    $index = [array]::IndexOf($deck, $keyword)
    if ($index -lt 0) { throw "Missing input card $keyword" }
    return ,@(($deck[$index + $offset] -split ',').Trim())
}

$baseNode = Get-CardRow '*NODE'
$tipNode = Get-CardRow '*NODE' 2
$length = [decimal]$tipNode[2] - [decimal]$baseNode[2]
$modulus = [decimal](Get-CardRow '*ELASTIC')[0]
$area = [decimal](Get-CardRow '*SOLID SECTION, ELSET=BAR, MATERIAL=ELASTICBAR')[0]
$load = [decimal](Get-CardRow '*CLOAD')[2]
$predicted = $load * $length / ($modulus * $area)

$table = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'tip-table.txt')
$columns = $table[-1] -split '\s+'
$dat = [decimal]::Parse($columns[2], [System.Globalization.NumberStyles]::Float, $culture)
$record = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'u2.json') | ConvertFrom-Json
$measurement = $record.measurement
if ($columns[0] -ne $tipNode[0] -or $measurement.node -ne 2 -or $measurement.increment -ne 1 -or $measurement.step_time -ne '1') {
    throw 'Unexpected node, increment or step time'
}
$diagnostic = [decimal]::Parse($measurement.value_mm, $culture)

'LOAD | increment 1 | step time 1 | TIP | node 2 | global U2'
"Analytical U2 (mm)      $($predicted.ToString('0.000', $culture))"
"DAT U2 (mm)             $($dat.ToString('0.000000000', $culture))"
"Diagnostic - DAT (mm)   $(($diagnostic - $dat).ToString('0.000000000E+0', $culture))"
if ($predicted -ne $dat) { throw 'The axial solution and printed DAT value differ' }
'Analytical / DAT comparison     PASS'
'Historical evidence verdict     PARTIAL'
