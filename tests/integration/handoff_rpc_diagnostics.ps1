param([Parameter(Mandatory)][string]$Plugin)
$ErrorActionPreference='Stop'
$entry=Join-Path $Plugin 'scripts/update.ps1'
$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($entry,[ref]$null,[ref]$errors)
if ($errors.Count){throw 'Product script did not parse'}
foreach ($fn in $ast.FindAll({param($n)$n -is [Management.Automation.Language.FunctionDefinitionAst]},$false)){
    if ($fn.Name -in 'Invoke-PinRpc','Send-RpcLine'){. ([scriptblock]::Create($fn.Extent.Text))}
}
function Check-Rpc([string]$method,[string]$response,[string]$expected){
    # The peer reads the request before replying or closing, so EOF cannot race a broken input pipe.
    $script='[void][Console]::ReadLine()' + [Environment]::NewLine + $response
    $info=[Diagnostics.ProcessStartInfo]::new()
    $info.FileName=(Get-Process -Id $PID).Path
    $info.Arguments='-NoProfile -NonInteractive -OutputFormat Text -EncodedCommand '+[Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($script))
    $info.UseShellExecute=$false
    $info.CreateNoWindow=$true
    $info.RedirectStandardInput=$true
    $info.RedirectStandardOutput=$true
    $info.RedirectStandardError=$true
    $p=[Diagnostics.Process]::Start($info)
    $p.BeginErrorReadLine()
    $trace=[ordered]@{stage='transport_test'}
    $actual='OK'
    try {
        try {$result=Invoke-PinRpc $p 7 $method @{} $trace}
        catch {$actual=$_.Exception.Message}
        if ($actual -cne $expected -or $trace.method -cne $method){throw "Expected $method $expected, got $actual"}
        if ($actual -eq 'OK' -and $result.marker -cne 'accepted'){throw 'Wrong RPC result'}
        if ($expected -eq 'HOST_RPC_EOF' -and $trace.child_exit -ne 29){throw 'Missing observed child exit code'}
        if ($actual -eq 'HOST_RPC_REJECTED' -and $trace.rpc_code -ne -32601){throw 'Missing numeric rejection'}
        if (($trace|ConvertTo-Json) -match 'PRIVATE_MESSAGE'){throw 'Unredacted transport diagnostic'}
        Write-Output "$method $actual"
    } finally {if (!$p.HasExited){$p.Kill()};$p.Dispose()}
}
Check-Rpc 'initialize' 'exit 29' 'HOST_RPC_EOF'
Check-Rpc 'initialize' "Write-Output 'not json'" 'HOST_RPC_INVALID_JSON'
Check-Rpc 'initialize' "Write-Output 'null'" 'HOST_RPC_INVALID_RESPONSE'
Check-Rpc 'initialize' "Write-Output '{""id"":9,""method"":""interaction/request"",""params"":{}}'" 'HOST_RPC_INTERACTION_REQUIRED'
foreach ($method in 'initialize','thread/read','thread/turns/list','thread/items/list','plugin/read','plugin/skill/read'){
    Check-Rpc $method "Write-Output '{""id"":7,""error"":{""code"":-32601,""message"":""PRIVATE_MESSAGE""}}'" 'HOST_RPC_REJECTED'
}
Check-Rpc 'thread/read' "Write-Output '{""method"":""notice""}';Write-Output '{""id"":7,""result"":{""marker"":""accepted""}}'" 'OK'
Check-Rpc 'initialize' 'Start-Sleep -Seconds 40' 'HOST_RPC_TIMEOUT'

# Test the replay policy with synthetic response objects and the caller's actual thread identity.
# No thread is created and no environment identity is assigned by this test.
if ($env:CODEX_THREAD_ID -notmatch '^[0-9a-fA-F-]{36}$'){throw 'Run the replay tests from a Codex thread'}
$body=$ast.Find({param($n)$n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Get-RecentHandoffCalls'},$false)
. ([scriptblock]::Create($body.Extent.Text))
function Invoke-PinRpc($p,$number,$method,$parameters,$trace){
    switch ($method){
        'thread/read' {return @{thread=@{id=$(if ($case -eq 'wrong-thread'){'wrong'}else{$env:CODEX_THREAD_ID})}}}
        'thread/turns/list' {return @{data=@(@{id='turn';startedAt=([DateTimeOffset]::UtcNow.ToUnixTimeSeconds()-$(if ($case -eq 'old'){2000}else{0}));status=$(if($case -eq 'active'){'inProgress'}else{'completed'})});nextCursor=$(if ($case -eq 'turn-window'){'next'})}}
        'thread/items/list' {
            $item=@{type='mcpToolCall';server='codex_apps';tool='github.fetch';status=$(if ($case -eq 'failed'){'failed'}else{'completed'})}
            $data=@()
            if ($case -in 'ok','failed','wrong-turn'){$data+=@{turnId=$(if ($case -eq 'wrong-turn'){'wrong'}else{'turn'});item=$item}}
            return @{data=$data;nextCursor=$(if ($case -eq 'page-window'){'next'})}
        }
        default {throw 'Unexpected call'}
    }
}
$expected=@{ok='OK';active='CONNECTOR_PROOF_NOT_VISIBLE_IN_ACTIVE_TURN';old='CONNECTOR_PROOF_EXPIRED';failed='CONNECTOR_QUERY_NOT_COMPLETED';empty='CONNECTOR_PROOF_MISSING';'wrong-thread'='HOST_THREAD_MISMATCH';'wrong-turn'='HOST_TURN_MISMATCH';'turn-window'='HOST_RECEIPT_WINDOW_EXCEEDED';'page-window'='HOST_RECEIPT_WINDOW_EXCEEDED'}
foreach ($case in $expected.Keys){
    $result='OK'
    try {$calls=@(Get-RecentHandoffCalls $null ([ordered]@{stage='start'}));if ($calls.Count -ne 1){throw 'Missing call'}}
    catch {$result=$_.Exception.Message}
    if ($result -cne $expected[$case]){throw "Replay $case expected $($expected[$case]), got $result"}
    Write-Output "replay $case $result"
}
