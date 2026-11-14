---
name: setup
description: 在 Windows 引导研究用户按需选择独立 CPython 运行时或自备解释器，并核实本次安装的 Core 身份。
---

# 首次配置

科研讨论、Sanity Model 审查、Model Contract 解释和规划可直接进行。单纯安装或打开插件不触发下载、运行解释器或写回执。仅在用户要求启用 Core、计算或读写 ResearchProject 时进入此流程。

1. 若有用户保管的本版本绑定摘要，先按下述方式核对发行清单和 launcher，再由当前安装的 launcher 执行 doctor。旧版回执、错误 pin、被拒绝的权限或不匹配的文件均停止并报告，禁止修补缓存、降级校验或自动重试。
2. 无已验证的绑定时，将[双方案表格](../../references/runtime-options.md)原样以中文 Markdown 呈现并停下。选择“暂不配置”直接返回科研讨论。不可代选。此步骤不需 Python 或网络。
3. 从 Host 确认当前安装根与 0.2.0-preview.6。要求用户通过独立发行记录取得 package-manifest.json 的 SHA-256；不可使用安装目录自报的摘要作为信任来源。用 PowerShell Get-FileHash 核对清单，再根据清单的 files 核对要执行的 scripts/runtime.ps1 或 scripts/launch.ps1。摘要不符或缺少独立来源即停止。
4. 用户选 1：以当前安装的 scripts/runtime.ps1 执行 `-Action plan -Choice managed -ManifestSha256 <独立摘要>`。用中文显示实际来源 URL、字节数、SHA-256、目标绝对路径及写入范围（私有暂存、版本化运行时和用户绑定回执）；说明会验证、执行固定解释器并绑定，不改系统注册表或 PATH。单独询问是否确认这些下载、写入及执行。回复“1”本身不足以授权。仅在确认后按原计划执行同一脚本 `-Action install -Choice managed -ConfirmDownload -ManifestSha256 <同一摘要>`，记录真实退出码。若 Host 要求审批，遵循其审批流程。权限拒绝则停止。
5. 用户选 2：请用户提供其信任的 python.exe 的本地绝对路径，说明将运行该解释器验证版本、x64、隔离模式和标准库并写入该版本的本地绑定回执。取得用户同意后由已验证的 launcher 执行 `-Action bind -PythonExe <绝对路径> -ManifestSha256 <独立摘要>`。当前支持列表只有 3.12.10。不扫描系统寻找其他解释器，不使用 pip。
6. 成功返回 BOUND 后由用户在安装目录之外保管 binding_sha256，再通过已核验的 launcher 执行 `-Action doctor -BindingSha256 <回执摘要>`。以实际退出码和状态答复。已有、冲突或中断的安装应保留诊断与目录，请用户复核；不覆盖或盲目重新绑定。配置成功后回到用户原本请求的 Core 操作。
