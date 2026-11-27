# Microsoft-signed MSI Direct Installation — 一页操作卡

**状态：PLAN_ONLY，等待新的精确安装授权。** 自定义暂存流程停止，原脚本不再调用或修改。本次人工报告的 `BLOCKED_ANCESTORS_AND_ABSENT_TARGET / UNTRUSTED_ANCESTOR_MUTATION_RIGHTS` 保留；没有据此认定 MSI 已安装或来源隔离已通过。

**唯一安装源（复用，不重新下载或换版本）**

`C:\Users\wuxia\AppData\Local\GDCAE-PowerShell-769-Qualification-20261031-A01\PowerShell-7.6.9-win-x64.msi`

大小 **117493760 字节**；SHA-256 **`50d33c7494aaf82b987cfd4de3f232d04f91fdd4c0deeca8a669cced3e7cf8f9`**。本轮只读复验摘要一致，Authenticode Valid、Microsoft Corporation 发布者、时间戳证书存在；不能替代实际安装前的重新核验。[官方发行来源](https://github.com/PowerShell/PowerShell/releases/tag/v7.6.9)

**1．安装前现场门禁及来源风险**

在 Codex 之外，由操作者使用系统 Windows PowerShell 5.1 第一层控制台；按需由官方 UAC 提升一次，不用缓存 pwsh、不再嵌套 Shell、不以 Job=True 单独判定安装不安全。确认系统 `msiexec.exe` 路径及 Microsoft 有效签名。重查既有 PowerShell 产品、目标目录、发行标记及 App Paths；任何需要覆盖的现有状态均停止，不升级、卸载或修复。

重新读取同一 MSI：完整大小/摘要、Authenticode Valid、Microsoft 发布者、可信证书链和时间戳均须通过。打开源 MSI 的只读句柄（FileShare.Read），在持有期间完成核验并保持至安装器退出；不允许其间写入/删除该文件，不能先释放句柄再凭旧摘要安装。

**真实风险边界：**本轮源文件及祖先未发现 reparse point，但源位于当前用户可写目录，文件 ACL 还含一个未解析名称的 capability SID FullControl ACE；尚未证明该能力的实际持有者。这里只做了 ACL 观察，不是完整 token AccessCheck。它不是管理员隔离安装源。只读文件锁不能单独防止可写祖先被重命名/替换；UAC 的 Microsoft 发布者提示也不能代替精确 SHA，结束后摘要相同不能倒推中途绝无替换。

后续授权必须明确接受此普通本地人工安装的剩余来源风险；现场确认有关写入主体/进程处于操作者可信控制下、没有并行 Agent/下载器修改、路径未变化。若能力持有者或路径可信性仍无法确认，停止，不静默豁免、不修 ACL、不另建暂存控制器。若要求严格抵御同用户恶意进程，此直接路径不能提供该保证，须另行裁定。

**2．一次人工确认后的官方 MSI 调用（本轮不得执行）**

上述门禁通过后，操作者只确认一次，通过 `C:\Windows\System32\msiexec.exe` 安装该完整源路径。使用 `/i`、`/qb`、`/norestart`，记录开始时间、退出码并等待完成；采用 Windows Installer 自带事件记录，不让提升进程向 Agent 可写路径输出自定义日志。固定属性如下，不进入可重新勾选选项的完整向导：

```text
INSTALLFOLDER="C:\Program Files\PowerShell"
ADD_PATH=0  ADD_EXPLORER_CONTEXT_MENU_OPENPOWERSHELL=0
ADD_FILE_CONTEXT_MENU_RUNPOWERSHELL=0  ENABLE_PSREMOTING=0
REGISTER_MANIFEST=0  USE_MU=0  ENABLE_MU=0
DISABLE_TELEMETRY=0  LAUNCHAPPONEXIT=0  REBOOT=ReallySuppress
```

安装包追加 `7`，最终为 `C:\Program Files\PowerShell\7`。不设置/修改执行策略，不自动启动新 PowerShell。MU=0 不撤销既有更新/GPO；DISABLE_TELEMETRY=0 不新增退出遥测环境变量。[微软 MSI 属性](https://learn.microsoft.com/en-us/powershell/scripting/install/install-powershell-on-windows?view=powershell-7.6) · [Windows Installer/UAC](https://learn.microsoft.com/en-us/windows/win32/msi/using-windows-installer-with-uac) · [官方安装参数](https://learn.microsoft.com/en-us/windows/win32/msi/command-line-options)

**3．应明确批准的系统变更**

程序文件、正常 Windows Installer 缓存/产品卸载登记及默认快捷方式；HKLM `Software\Microsoft\PowerShellCore\InstalledVersions` 的版本/产品/位置与 `InstallerProperties` 选项登记；HKLM `Software\Microsoft\Windows\CurrentVersion\App Paths\pwsh.exe` 指向新程序；机器级 `POWERSHELL_DISTRIBUTION_CHANNEL=MSI:[WINDOWS_PRODUCT_NAME]`（实际展开值由安装后只读登记核对）。这些来自该 MSI 的只读表核查，不等于“零环境变更”。不改 PATH、Codex/Python 配置，不启用 Remoting、右键菜单或 MU；Windows 自带 Installer 服务可按需处理安装及自身回滚，不安装新服务，不启动 Operator/AF。

**4．安装后只读核验与停止**

捕获真实退出码，并核对本次时间窗/产品对应的 Windows Installer 事件及产品登记：0 仅表示安装器报告成功；3010 标为 PENDING_REBOOT，绝不自动重启；失败、中断、退出状态未知或来源变化均停止，不重试、不清理、不自行卸载。复核原 MSI、安装版本/路径/程序签名，检查安装目录及祖先无 reparse、普通主体不可替换代码；对比安装前后的 PATH、相关登记及禁用选项。随后仅经获批的验证调用，以新程序绝对路径和 `-NoProfile` 输出版本、实际程序路径/身份，不运行业务脚本。只返回脱敏结果与退出码，不公开完整事件日志。

全部通过后才可报告 `POWERSHELL7_INDEPENDENT_INSTALL_VERIFIED`；不代表 Operator 宿主、HIL 或真实 Abaqus 准入。本轮未启动 MSI、未变更账户/ACL/注册表/环境，也未触发 Git 提交或推送。
