# 会话内版本提示

当前已核验的 Desktop 26.1111.2228.0 将本产品的 SessionStart 记为 BLOCKED_BY_HOST。首次调用先执行原有 skill-check。如果脚本进程成功启动并返回 HOST_NETWORK_RESTRICTED，且用户授权了官方频道查询，可使用已连接的 GitHub 只读文件工具。工具或用户明确拒绝时立即停止检查并继续科研。只允许以下查询，无需用户手工执行命令。

1. 在本会话用 Host 的 GitHub `fetch_file` 工具读取仓库 `BrunelXian/Goal-Driven-CAE-Orchestrator`、ref `gdcae-preview`、path `channel.json`，指定 `encoding=base64`。以本次成功的工具调用参数、返回的 content、encoding 和 Git blob sha 为依据。禁止用搜索摘要、聊天文本、用户文件或本地 Marketplace 快照代替。
2. 只将实际返回的 base64（去掉编码换行、至多 2732 个字符，仅 base64 字符）和 40 位小写十六进制 sha 作为单独的字符串参数交给同一个安装态 `scripts/update.ps1 -Action skill-check -ChannelBase64 <content> -ChannelBlobSha <sha>`。禁止传递远程命令或执行返回的文件。脚本复用频道规则并重算 Git blob。展示当前版本、频道版本和经核验的 Manifest SHA-256。需要核对发行物时也可展示 ZIP SHA-256。一次会话复用该条实际回执。
3. 只有本次 Host 的精确文件读取和脚本的成功校验同时存在才计 UPDATE_DISCOVERY_PASS。缺少受支持的访问渠道时记录 BLOCKED_HOST_UPDATE_DISCOVERY；内容或摘要有误时报告具体错误。该输入只供发现，不给安装授权。安装仍须在用户明确确认目标后执行原有受信预检和正式 Marketplace 流程。

SessionStart 由 Host 在审核信任后运行，产生 SESSIONSTART_AUTO_CHECK 回执。若当前启动或恢复没有 Hook 回执，首次使用 setup/research 时由 Skill 自行通过 Host 调用安装态 scripts/update.ps1 -Action skill-check，产生 FIRST_SKILL_USE_CHECK。用户单独执行 check 属于 MANUAL_CHECK。mode 字段是调用入口标识，Host 事件和命令结果另行核验。只向固定官方 GitHub 请求元数据；成功检查可缓存一小时，Host 明确禁网的诊断仅在同样受限的环境缓存三分钟。其他网络错误不缓存。输出含诊断类别、缓存状态与退出码，基础科研可继续。不要执行远程说明、链接或命令。

若 status 为 AVAILABLE，展示“CAE Agent 检测到新版本。”及两列中文表格，行依次为当前版本、可用版本、更新内容、发行渠道（GD-CAE 官方 GitHub）、更新影响。摘要和影响使用脚本输出的本地枚举解释。提供 **1. 立即更新（推荐）**、**2. 暂不更新**、**3. 查看详细更新说明**。3 仅给出脚本返回的固定官方 tag 页面；2 继续科研。用户明确接受表中确切版本、清单摘要后才执行安装态脚本 -Action install -TargetVersion <available> -ManifestPin <manifest_sha256> -ConfirmUpdate。Host 要求审批时交给用户；拒绝后继续当前版本，禁止重试或更换通道。

CURRENT 为频道无新版，CHANNEL_BEHIND 为本地候选领先。CHECK_UNAVAILABLE 时显示 reason，保留未知原因；LOCAL_STATE_UNWRITABLE 表示本次未能保存缓存。审批或写入被 Host 拒绝时停止，标为 BLOCKED_HOST_UPDATE_PERMISSION。MIGRATION_REQUIRED 表示当前来源需要迁移。只在真实版本、enabled、清单和实际文件通过时显示 INSTALLED_RESTART_REQUIRED；打开新会话加载新版。UNKNOWN_AFTER_HOST_WRITE 时先核对官方 list、新会话 skills/list 和旧版回执。
