# PowerShell 7.6.9 — 已审查逻辑的单文件封装

**本轮仅封装及离线验收，等待用户确认新脚本和摘要后才可运行。** 未执行安装。原暂存失败证据保持不变；不再使用自定义暂存脚本。

回执的 `source_sha256` 是批准的预期摘要，早期 BLOCKED 时不是实测成功证明；只有完成相应检查才能陈述已核验。宿主检查核实管理员、64 位及系统 Windows PowerShell 路径，不证明第一层进程来源；独立控制台仍须由操作者按要求选择。

- 脚本：`D:\Projects\Goal-Driven-CAE-Orchestrator\docs\milestones\Install-PowerShell769-Approved.ps1`
- SHA-256：`2e9babbf27a587505bbcc08514c793e301d801f1bc2e60364d6f800005aa2719`
- 大小：9132 字节。ASCII 内容，按 UTF-8 解码；摘要覆盖完整文件字节。
- 唯一 MSI：`C:\Users\wuxia\AppData\Local\GDCAE-PowerShell-769-Qualification-20261031-A01\PowerShell-7.6.9-win-x64.msi`
- MSI：117493760 字节；SHA-256 `50d33c7494aaf82b987cfd4de3f232d04f91fdd4c0deeca8a669cced3e7cf8f9`。

确认摘要后的唯一人工步骤：在 Codex 宿主之外的**第一层、64 位、已提升权限的系统 Windows PowerShell**中，粘贴下列一行；门禁通过后输入一次 `INSTALL_769_ONCE`，等待并保留末尾脱敏 JSON。不要启动嵌套 PowerShell，不使用缓存 pwsh，不自动提权。不要求手工计算摘要。

```powershell
& { $b=[IO.File]::ReadAllBytes('D:\Projects\Goal-Driven-CAE-Orchestrator\docs\milestones\Install-PowerShell769-Approved.ps1'); $h=[Security.Cryptography.SHA256]::Create(); try { if ([BitConverter]::ToString($h.ComputeHash($b)).Replace('-','') -ne '2e9babbf27a587505bbcc08514c793e301d801f1bc2e60364d6f800005aa2719') { throw 'SCRIPT_HASH_MISMATCH_STOP' } } finally { $h.Dispose() }; & ([scriptblock]::Create([Text.Encoding]::UTF8.GetString($b))) }
```

启动行只读取脚本一次，对 `$b` 校验并执行同一字节快照，不再从路径调用脚本。摘要应以用户确认的本操作卡/聊天中值为信任锚，不能运行时从相邻 Agent 可写摘要文件取值。这防止脚本校验后重读替换，不承诺抵御同用户恶意进程或 MSI 祖先路径替换；沿用用户对普通本机可信环境和 Capability SID 残余风险的一次性接受。

脚本保持已批准的固定安装属性与一次安装语义：源路径/大小/摘要、Microsoft 有效签名/时间戳/在线证书链、冲突及 reparse 检查、`FileShare.Read` 持锁至结束；无 RunAs、重试、卸载或清理。最终目录 `C:\Program Files\PowerShell\7`；允许 MSI 正常产品/App Paths/发行标记登记，禁用 PATH、Remoting、右键菜单、MU 集成及自动重启。不修改 Codex/Python 环境，不部署 Operator。

**停止规则：**任何摘要/签名/冲突/来源异常即停。安装意图记录后异常为 UNKNOWN；3010 为 `PENDING_REBOOT_STOP`；其他非零退出为 `INSTALLER_NONZERO_STOP`。控制台关闭、被中断或没有完整 JSON 均视为 UNKNOWN，禁止再次粘贴、重试、重启、修复或卸载。JSON 仅控制台输出，无自定义特权日志落盘；请返回 JSON 以供独立只读验收。退出 0 仅为 `INSTALLER_EXIT_0_PENDING_READONLY_VERIFICATION`，不能自行宣称最终安装 VERIFIED。

离线记录：系统 Windows PowerShell 5.1.26100.9818，`Test-PowerShell769-DirectOffline.ps1`；协调函数使用内存源句柄和进程替身，测试不执行生产脚本、不启动 MSI、不读写安装登记、不进行在线签名查询。独立审查结论及最终测试数量见配套 `POWERSHELL769_PACKAGED_INSTALL_OFFLINE_RECEIPT_2026-11-01.json`。离线通过不替代执行现场门禁或安装后只读验收。
