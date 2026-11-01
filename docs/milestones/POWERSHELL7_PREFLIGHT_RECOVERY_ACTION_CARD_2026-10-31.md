# PowerShell 7.6.9：限定恢复操作卡

状态：包内容与安装选项静态核验完成；`BLOCKED_ADMIN_STAGING_SECURITY_UNQUALIFIED`、`BLOCKED_ADMIN_CONSOLE_RUNTIME_UNQUALIFIED` 保持。没有安装、创建目录、复制到管理员区或修改 ACL。历史回执保持原样。

## 已完成的只读核验

现有 MSI 重新计算 SHA-256，仍为 `50d33c7494aaf82b987cfd4de3f232d04f91fdd4c0deeca8a669cced3e7cf8f9`；大小仍为 117493760。复用先前 Valid/Microsoft 签名链证据；安装前管理员必须再次验证。

MSI 以 OpenDatabase(..., 0) 只读打开；修正 COM 属性读取方式后取得有效字段，没有执行 MSI 动作。ProductVersion=7.6.9.0，Manufacturer=Microsoft Corporation。官方属性见 [Microsoft Learn](https://learn.microsoft.com/en-us/powershell/scripting/install/install-powershell-on-windows?view=powershell-7.6)。

准备好的安装属性（仅参数，不是本轮执行指令）：

```text
INSTALLFOLDER="C:\Program Files\PowerShell"
ADD_PATH=0
ADD_EXPLORER_CONTEXT_MENU_OPENPOWERSHELL=0
ADD_FILE_CONTEXT_MENU_RUNPOWERSHELL=0
ENABLE_PSREMOTING=0
REGISTER_MANIFEST=0
USE_MU=0
ENABLE_MU=0
DISABLE_TELEMETRY=0
LAUNCHAPPONEXIT=0
REBOOT=ReallySuppress
```

Directory 表确认 VersionFolder=INSTALLFOLDER\7。Component 条件将 PATH、两个右键菜单、MU 登记和遥测退出变量限制为对应属性=1；ExecuteSequence 将 Remoting、manifest 和 MU 执行限制为对应属性=1。禁用 MU 不撤销既有更新策略。退出启动条件为 LAUNCHAPPONEXIT=1。

**额外固定行为需要明确接受**：Environment 表的 Telemetry 组件无条件关联 ProductFeature，按 `+-*POWERSHELL_DISTRIBUTION_CHANNEL` 写入机器级 `MSI:[WINDOWS_PRODUCT_NAME]` 分发标记；AppPath 组件也会登记系统 App Paths\pwsh.exe。未找到独立组件禁用的公开属性。不修改 MSI、不做 transform 绕过。安装前须检查该环境变量是否已有值；存在则停止复核，不覆盖未知配置。这个系统标记与产品登记不应被隐瞒为“零环境变更”；不改 PATH、Codex 配置文件或 Python 环境文件。

## 当前唯一人工步骤：独立管理员只读核查

从 Windows 开始菜单独立打开系统 Windows PowerShell，以管理员身份运行；不要通过 Codex 启动，也不要使用缓存 pwsh。这里仅用 Windows PowerShell 做读取，不执行要求 7.4+ 的 Operator 脚本。执行以下只读片段，结果仅在本机查看：

```powershell
$ErrorActionPreference = 'Stop'
$id = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($id)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'STOP: independent elevated administrator required'
}
$paths = @('C:\', 'C:\ProgramData', 'C:\ProgramData\GDCAE PowerShell Install 7.6.9')
foreach ($p in $paths) {
    if (-not (Test-Path -LiteralPath $p)) { Write-Output "ABSENT: $p"; continue }
    $item = Get-Item -LiteralPath $p -Force
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
        throw 'STOP: reparse path'
    }
    $acl = Get-Acl -LiteralPath $p
    [pscustomobject]@{Path=$p;Owner=$acl.Owner;ProtectedDacl=$acl.AreAccessRulesProtected;SDDL=$acl.Sddl}
}
[pscustomobject]@{
    TargetExists = Test-Path -LiteralPath 'C:\Program Files\PowerShell\7'
    DistributionMarkerPresent = $null -ne [Environment]::GetEnvironmentVariable('POWERSHELL_DISTRIBUTION_CHANNEL','Machine')
}
```

若发现既有专用暂存位置：独立管理员在“属性→安全→高级→有效访问”确认实际执行账户以及当前 Codex Windows 主体、Users/Authenticated Users 等相关组权限；结合实际令牌、继承范围和祖先 DeleteChild/删除权限审查。仅显示 ACL 或目录名称不等于有效权限 PASS；不能通过创建文件作写入试验。若不能证明普通/非提升 Agent 令牌不可写入、替换或删除包，则保持 BLOCKED。不得借助管理员关联组把普通令牌误判为提升令牌，也不得据此修改既有 ACL。

无需提供用户名、SID 或完整 ACL 到聊天；只回复“专用目录不存在 / 已存在且管理员确认合格 / 无法确认”，以及标记或目标冲突是否存在。当前 Codex 只读检查显示专用目录不存在，未自行认定任何现有目录合格。

## 一次精确创建授权申请（尚未获准）

请批准由独立管理员只创建 `C:\ProgramData\GDCAE PowerShell Install 7.6.9` 一个新目录，并在创建时原子设置安全描述符：

```text
O:BAG:BAD:P(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)
```

所有者为 Administrators；关闭 DACL 继承；仅 SYSTEM 和 Administrators 完全控制，继承到新子项。不修改父目录或任何既有对象；目录已存在或祖先不合格即停止。创建后由管理员核验实际权限，再复制唯一批准 MSI、重新检查摘要/签名/证书链。子项不得保留普通用户所有权或不受限 ACL。本授权请求仅包含该新目录、精确 MSI 副本及后续安装回执/日志所需新文件，不含 Operator 暂存区、账户、服务或安装执行。

## 以后的一次人工安装确认流程（本轮禁止执行）

受保护暂存门禁、固定分发标记变更许可、冲突复核通过且获得安装执行批准后：管理员在独立控制台核验系统 msiexec 签名、包摘要/签名链，确认一次才调用该 MSI；采用上述属性、基础进度 UI（/qb，不显示可重新勾选功能的完整向导）、/norestart，保存受保护日志，捕获退出码。无静默替换、升级、卸载或重试；默认不启动新 pwsh。管理员确认前不运行 msiexec。

安装后：退出码 0 仅代表安装器完成，还须核对真实版本/路径/签名、目录及祖先权限、普通令牌不可替换、产品登记、PATH/禁止功能未改变；3010 保留重启待定，不自动重启。随后由用户独立启动新安装的 pwsh -NoProfile，核验实际提升身份、无 impersonation 和无 Job 约束。无法证明任何一项即 BLOCKED，不自动修复。仅全部通过才能报告 POWERSHELL7_INDEPENDENT_INSTALL_VERIFIED；不自动进入 Operator 部署。
