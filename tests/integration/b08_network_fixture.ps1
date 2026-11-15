param([string]$Driver,[string]$Endpoint)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
if ($env:CODEX_SANDBOX_NETWORK_DISABLED -in '1','true'){throw 'Network test requires an authorized loopback context'}
$repo='fixture'
$cases=[ordered]@{}
$ast=[Management.Automation.Language.Parser]::ParseFile($Driver,[ref]$null,[ref]$null)
$function=$ast.Find({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Get-OfficialJson'},$false)
# Inject the test endpoint into a private copy; production has no configurable URL.
$src=$function.Extent.Text.Replace('"https://api.github.com/repos/$repo/$suffix"','"$Endpoint/$suffix"')
. ([scriptblock]::Create($src))
function Assert-Fault([string]$inputName,[string]$expected,[int]$http=0) {
    $script:httpStatus=0
    $reason='NO_FAULT'
    try {$null=Get-OfficialJson $inputName} catch {$reason=$_.Exception.Message}
    if ($reason -cne $expected -or $http -ne $script:httpStatus){throw "case $inputName expected $expected/$http observed $reason/$script:httpStatus"}
    $cases[$inputName]=@{reason=$reason;http_status=$script:httpStatus}
}
Assert-Fault '404' HTTP_ERROR 404
Assert-Fault '302' HTTP_ERROR 302
Assert-Fault '407' PROXY_AUTH_REQUIRED 407
Assert-Fault '403' GITHUB_RATE_LIMIT 403
Assert-Fault '429' GITHUB_RATE_LIMIT 429
Assert-Fault '503' GITHUB_API_UNAVAILABLE 503
Assert-Fault 'bad-json' METADATA_FORMAT_ERROR
Assert-Fault 'bad-utf8' METADATA_FORMAT_ERROR
Assert-Fault 'oversize' METADATA_SIZE
if ((Get-OfficialJson 'ok').schema -ne 1){throw 'valid JSON case'}
$env:CODEX_SANDBOX_NETWORK_DISABLED='1'
Assert-Fault 'host-restriction' HOST_NETWORK_RESTRICTED
# Continue transport fault injection in the fixture only.
$env:CODEX_SANDBOX_NETWORK_DISABLED=$null
$faults=@{NameResolutionFailure='DNS_FAILURE';ProxyNameResolutionFailure='PROXY_DNS_FAILURE';
    SecureChannelFailure='TLS_FAILURE';TrustFailure='TLS_TRUST_FAILURE';Timeout='NETWORK_TIMEOUT'}
$src=$src.Replace('$response=$request.GetResponse()', 'throw [Net.WebException]::new("fixture",[Net.WebExceptionStatus]$suffix)')
. ([scriptblock]::Create($src))
foreach($k in $faults.Keys){Assert-Fault $k $faults[$k]}
$cases | ConvertTo-Json -Depth 4
