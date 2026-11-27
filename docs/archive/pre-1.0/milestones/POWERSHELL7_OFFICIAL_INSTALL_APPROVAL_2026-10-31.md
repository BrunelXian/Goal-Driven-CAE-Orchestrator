# 独立 PowerShell 7 最小安装授权申请

日期：2026-10-31。状态：**PLAN_ONLY / NOT_AUTHORIZED**。
`BLOCKED_ADMIN_CONSOLE_RUNTIME_UNQUALIFIED` 保持不变，Operator Foundation 暂停。
本轮未下载 MSI、安装软件、修改环境/ACL、执行 Operator Apply 或提交 Git。

## 精确候选

| 项目 | 拟批准内容 |
|---|---|
| 产品/版本 | Microsoft PowerShell 7.6.9，Windows x64，稳定版 MSI；不使用 Preview、latest 自动解析、MSIX 或 Codex 缓存副本 |
| 唯一文件 | `PowerShell-7.6.9-win-x64.msi` |
| 官方来源 | `https://github.com/PowerShell/PowerShell/releases/tag/v7.6.9` 中的同名资产 |
| 直接下载地址 | `https://github.com/PowerShell/PowerShell/releases/download/v7.6.9/PowerShell-7.6.9-win-x64.msi`；仅接受官方 GitHub Release 资产交付，禁止镜像替换 |
| 固定 SHA-256 | `50d33c7494aaf82b987cfd4de3f232d04f91fdd4c0deeca8a669cced3e7cf8f9` |
| 安装位置 | `C:\Program Files\PowerShell\7`；新管理员入口为该目录的 `pwsh.exe` |
| 执行者 | 用户在 Codex 宿主之外，使用 Windows 自带的可信安装入口并人工响应 UAC；Codex 不提权、不代输密码、不执行安装 |

候选版本、文件名和摘要来自[微软 PowerShell 官方 Release](https://github.com/PowerShell/PowerShell/releases/tag/v7.6.9)。官网安装说明的示例版本可能滞后，本申请固定上述资产，不跟随更新自动改版本。
微软说明 PowerShell 7 与 Windows PowerShell 5.1 并存，MSI 是支持的部署方式，默认稳定版目录为 Program Files 下的 PowerShell/7。[官方安装说明](https://learn.microsoft.com/en-us/powershell/scripting/install/install-powershell-on-windows?view=powershell-7.6)

## 已核对与尚未核对

- 本机 AMD64、Windows 10.0.26300，指定 `...\PowerShell\7` 目录不存在。
- 系统文件 `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe` 与 `C:\Windows\System32\msiexec.exe` 的 Authenticode 状态实际为 Valid，签名主体为 Microsoft Windows / Microsoft Corporation。
- 上述仅为文件和主机元数据核查，不是已经进入独立管理员控制台的证据。
- **MSI 实际字节、精确文件大小、签名证书/指纹/时间戳尚未检查**：本轮没有下载包。不能用官方下载页或摘要替代实际签名验证。
- 不使用 Windows PowerShell 5.1 执行 Operator 脚本；它至多用于安装前的只读核验或调用系统 Windows Installer。Operator 的 PowerShell 7.4+ 门槛不降低。

## 请求范围与安装前门禁

1. 批准后，仅下载这个固定 MSI 到全新任务目录。记录精确字节数和 SHA-256，与官方固定值逐字匹配；不自动替换版本或重试失败下载。
2. 使用 Windows Authenticode 验证，要求 Status=Valid、签名发布者为 Microsoft Corporation、可信代码签名证书链及时间戳验证成立。记录证书指纹等实际证据，不预造证书值。无签名、HashMismatch、未知信任、无法判定或异常发布者均停止。[Get-AuthenticodeSignature 官方说明](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.security/get-authenticodesignature?view=powershell-7.6)
3. 只读检查 MSI 产品/架构/版本/目录及环境表、安装动作与所选属性，确认不覆盖既有 PowerShell 安装、不引入计划外环境或服务配置。包大小/签名与 MSI 属性核查前，不交付可执行安装命令。
4. 安装前管理员从独立可信控制台重新核验同一 MSI 字节。安装源在提交安装期间不得被 Agent/普通用户替换；需要管理员保护的独立安装暂存目录时，须作为此次 PowerShell 安装准备明确记录，不能复用或改动 Operator 暂存区。
5. 全部通过后，由用户确认执行**一次**标准 MSI 安装，保留交互确认，禁止静默自动升级、自动修复或自动重启。若发现同产品/目标目录已存在，停止，不卸载/覆盖/接管。

## 最小安装选项和允许的系统变化

拟定 MSI 选项如下，获准下载后还须以该精确 MSI 核验效果：

| 选项 | 值/约束 |
|---|---|
| ADD_PATH | 0，不修改用户或系统 PATH |
| ADD_EXPLORER_CONTEXT_MENU_OPENPOWERSHELL | 0 |
| ADD_FILE_CONTEXT_MENU_RUNPOWERSHELL | 0 |
| ENABLE_PSREMOTING | 0，不启用远程管理/WinRM 配置 |
| REGISTER_MANIFEST | 0，不主动注册 PowerShell Event Logging manifest |
| USE_MU / ENABLE_MU | 0 / 0，不由本次安装加入更新配置；不撤销或重写既有 Windows Update/GPO 策略 |
| Telemetry | 不请求持久环境变量变更；验收会话如需退出遥测，仅设置该会话的环境，不修改机器级设置 |
| 重启/执行策略 | 不自动重启；不设置 ExecutionPolicy Bypass，不修改既有执行策略 |

这些选项由[微软 MSI 参数文档](https://learn.microsoft.com/en-us/powershell/scripting/install/install-powershell-on-windows?view=powershell-7.6)说明；不以选项名字代替对实际包动作的核验。
允许的安装效果仅限该产品的程序文件、正常 Windows Installer 缓存/产品卸载登记及默认快捷方式。MSI 使用 Windows 自带安装机制，可能按需运行 Windows Installer 系统服务；不安装新服务，不启动 Operator/AF/WinRM 服务，不修改账户权限。

不修改 LangChainEnv、Python、Codex 全局配置、原有 Operator ZIP/Plan/脚本。安装 PowerShell 不自动解除 Operator 其他门槛。

## 安装后只读验收与停止条件

- 核对 MSI 退出状态、产品版本、实际 `pwsh.exe` 路径/文件签名及必要运行时文件；存在重启要求时保留 PENDING_REBOOT，不自动重启或重装。
- 检查程序目录和祖先无 reparse/用户可替换路径，受可信管理员/SYSTEM/TrustedInstaller 控制，普通 Agent/用户不得写入代码；不修补既有目录 ACL 来强行通过。
- 用户从 Windows 桌面独立启动新安装的 `pwsh.exe -NoProfile`，人工提升；核对实际路径、版本、提升令牌、无 impersonation 和 `IsProcessInJob(..., NULL)=false`。仅看到“管理员”窗口标题不算通过。
- 版本签名、目录权限或宿主环境任一无法确定，保持阻断；不尝试换入口、放宽 Job 检查或调整全局策略。
- 保存脱敏回执：版本、包/文件摘要、签名状态、安装退出状态、路径、ACL和令牌/Job布尔结果。安装日志若需要保存，仅置于管理员保护目录，不导出完整环境、密码或私有会话。
- 最多报告 `INDEPENDENT_POWERSHELL_READY`，随后停止。**不自动执行 Operator Foundation；不报告 HIL_ENFORCEMENT_PASS 或 REAL_A_READY。**

## 请求用户精确批准

请批准以下限定动作：**从上述官方 Release 下载并核验固定 SHA-256 的 PowerShell 7.6.9 x64 MSI；只有全部安装前门禁通过后，由用户在独立管理员环境中确认安装一次到 `C:\Program Files\PowerShell\7`，按上述最小选项执行，并完成只读验收。**

任何失败均停止、保留证据，不自动重试/卸载/修复/删除或继续 Operator 部署。若实际包要求超出这里的变化，重新报告并等待授权。
