# 静态暂存门禁修订：操作卡

仅离线交付，尚未批准执行新版。旧脚本摘要作废；历史 HOST_IN_JOB 阻断保持原样。

新版 SHA-256：`2398dfdab49f48ed23d9798e2ad55cb674cafb37f4d62b79458561e54a4c6374`

Job true/false 仅记录；查询失败停止。管理员、系统 Windows PowerShell、完整语言模式、签名、所有权、受保护 ACL、路径、注册冲突、MSI 摘要及证书链仍须通过。互操作采用进程内 Reflection.Emit，不使用 Add-Type/csc，不创建安装器或其他工作进程。操作者须确认控制台来自 Codex 之外；此声明不是 OS 独立性证明。

**中断规则**：创建调用前失败为 BLOCKED；开始调用后任何异常为 UNKNOWN。安全目录建立后写入不可覆盖的意图文件；最终磁盘回执仅称 checks-complete，读回摘要核对成功及句柄收尾后才在控制台输出 VERIFIED。杀进程、断电或没有最终控制台结果即 UNKNOWN，不能凭回执文件存在推定成功；禁止重跑、清理或自动恢复。

**以后获准时的唯一人工步骤**：在原来手动开启的独立、提升权限的系统 Windows PowerShell 5.1 第一层控制台，粘贴下面整段一次；不要再开嵌套 Shell。出现确认时输入 STAGE_769_ONCE，然后仅返回末尾脱敏 JSON。本轮不要执行。

本段加载器从一次打开取得字节快照，核验本卡固定摘要，严格 UTF-8 解码，执行同一快照而非重开 Agent 可写脚本路径。摘要需从本次审阅的聊天/操作卡固定，禁止运行时从同目录 manifest 获取。它不是 Authenticode 签名，也无法抵御已被攻陷的管理员会话；应使用未加载个人 profile 的控制台。不修改执行策略，受限策略/语言模式或远程来源标记均停止。

```powershell
& {
    $ErrorActionPreference = 'Stop'
    function Assert-PinnedLoaderPolicy([string]$Language, [string]$Policy) {
        if ($Language -ne 'FullLanguage' -or $Policy -notin @('RemoteSigned','Unrestricted')) {
            throw 'STOP_EXECUTION_POLICY_OR_LANGUAGE_MODE'
        }
    }
    function Get-PinnedStageBlock([string]$Path, [string]$ExpectedHash) {
        Assert-PinnedLoaderPolicy ([string]$ExecutionContext.SessionState.LanguageMode) `
            ([string](Microsoft.PowerShell.Security\Get-ExecutionPolicy))
        $stream = [IO.File]::Open($Path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
        try {
            if ($stream.Length -lt 1 -or $stream.Length -gt 131072) { throw 'STOP_SCRIPT_SIZE' }
            $streams = @(Microsoft.PowerShell.Management\Get-Item -LiteralPath $Path -Stream '*' -ErrorAction Stop)
            if (@($streams | Where-Object { $_.Stream -eq 'Zone.Identifier' }).Count) {
                throw 'STOP_REMOTE_SOURCE_MARKER'
            }
            $bytes = [byte[]]::new([int]$stream.Length)
            $offset = 0
            while ($offset -lt $bytes.Length) {
                $count = $stream.Read($bytes,$offset,$bytes.Length-$offset)
                if ($count -eq 0) { throw 'STOP_INCOMPLETE_SNAPSHOT' }
                $offset += $count
            }
        } finally { $stream.Dispose() }
        $hasher = [Security.Cryptography.SHA256]::Create()
        try { $actual = [BitConverter]::ToString($hasher.ComputeHash($bytes)).Replace('-','').ToLowerInvariant() }
        finally { $hasher.Dispose() }
        if ($ExpectedHash -cnotmatch '^[a-f0-9]{64}$' -or $actual -cne $ExpectedHash) { throw 'STOP_SCRIPT_HASH' }
        $text = [Text.UTF8Encoding]::new($false,$true).GetString($bytes)
        return [ScriptBlock]::Create($text)
    }
    $pin = '2398dfdab49f48ed23d9798e2ad55cb674cafb37f4d62b79458561e54a4c6374'
    $block = Get-PinnedStageBlock `
        'D:\Projects\Goal-Driven-CAE-Orchestrator\docs\milestones\Stage-PowerShell769-Approved.ps1' $pin
    & $block -PinnedScriptSha256 $pin
}
```

脚本固定仅解决已核验字节与执行字节之间的路径替换窗口；不保证 Agent 无法修改本卡、管理员无法改文件或未来安装安全。下一次批准须明确绑定新版摘要。若管理员不能确认本卡来源或当前控制台可信，停止。暂存成功也不授权 msiexec、账户、Operator 或 Solver。

离线证据：系统 Windows PowerShell 5.1.26100.9818，98 项检查通过；包括原生产 catch/finally 的合成故障注入、记录写入/Flush/读回失败、句柄释放异常和快照替换。没有执行生产顶层、真实原生创建、管理员 ACL 部署、杀进程或断电实验。本轮新增检查曾暴露旧 AceFlags 枚举在 PS5.1 中的位运算转换问题，已显式转换整数修复。历史阻断不因此改写。

独立 Reviewer：OFFLINE_REVIEW_PASS。独立复跑基础 87 项，并只读复核最终 98 项证据及新增故障注入；确认最终脚本 20663 字节、上述 SHA 和卡片两处固定值一致。执行准入仅为提交新版精确暂存授权申请；不等于 POWERSHELL7_STAGING_VERIFIED，不包含真实暂存、安装或 Operator 部署。
