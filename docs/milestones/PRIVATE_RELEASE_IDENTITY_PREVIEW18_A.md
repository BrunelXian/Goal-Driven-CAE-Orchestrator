# 私有发行身份与 Setup → Main 验收记录

总体 PARTIAL。测试对象是在独立 A 机配置中通过官方 plugin/install 安装的个人私有 0.2.0-preview.17；待验实现来自 0.2.0-preview.18 本地候选。已发布的 .17 本体没有安装新入口。

## 原因及实现

.17 的交接脚本需要独立 Manifest pin。引导说明让用户查交付清单；早期自动查询只识别 Git Marketplace 的固定 Tag 和 GitHub Release。GitHub 连接器实测 .17 的 Release 按 Tag 查询返回 404。开发验收报告和 Plugin Creator 私有发行都有独立身份。

为已通过平台回读的 .17 增补包外 Publisher Release Receipt。定位时只从官方仓库 main ref 取完整提交，再以该提交读取版本对应的 JSON 并复算 Git blob。验证产品、私有渠道、插件 ID、版本、平台发行 ID 形态、来源提交及两个发行摘要。通过官方 plugin/read 按后端 ID 查询实际安装身份、localVersion、启用状态及来源；通过 plugin/skill/read 对照安装态 setup 原始字节。平台展示的最新版本不能代替 localVersion。包外记录由发行者审核后同步；候选构建不会自动登记成已发布版本。

- plugins/gdcae-research/scripts/update.ps1 新增只读 handoff-identity，复用 Host 当前线程的结构化连接器回执、RPC、固定 Git Tag 和 Release 验证。独立核对安装位置、清单、setup、交接脚本和运行时检查脚本。发现成功不授予执行权。
- references/project-main.md 定义首次移交时的证明获取、执行包内脚本前的 Host 原生哈希预检和失败行为。既有打包器将同一说明嵌入 setup 与 research。references/runtime-options.md 采用同一证明入口。
- product/research-preview/publisher-receipts 保存包外证明。tools/publisher_receipt.py 从已独立回读的报告、逐文件清单及发行 ZIP 生成版本记录，输出文件已存在时拒绝覆盖。测试重新生成 .17 记录，字节一致。该工具不会上传文件或对平台发行。
- tests/integration/private_release_identity.ps1 覆盖来源绑定、不同版本和拒绝行为。插件清单、安装指南、启动器、版本化绑定路径与打包器同步版本。交接脚本及唯一 Main 状态机未变。

## 真实 Host 证据

A 端使用独立 CODEX_HOME、官方 ChatGPT 登录及 Codex CLI 0.169.0-alpha.11.1。远端目录的详情显示已安装 .17；独立配置实际取得 .17 文件后，官方 plugin/skill/read 返回 setup，正文 SHA-256 为 9fe5603b3e8bb6a899bbe78ad5402237bffa1481a338de312617dd9dae18644d。测试以该安装的 Skill 和原始 1 mm 向下位移、容差 ±0.1 mm 的需求发起，附既有创建 Main 授权。为跨版本验证，测试驱动注入候选中的发行发现说明，调用候选自身的 PowerShell 对私有 .17 安装进行核验。验收不覆盖未经发布的 .18 私有 UI 自然激活。

| 环节 | 实际结果 |
|---|---|
| 取得官方证明 | github.fetch 取得 refs/heads/main，再用 github.fetch_file 获取固定提交 812c8d4d5f70a35bdb2814f6dcd600ec39e29050 的版本记录，blob f39c68b6938a64d4ab033767231b819387c592e3。平台发行 pluginrel_6af9be046c1c8191a20dc4030f8d987f。 |
| 首条科研回复 | 显示 LoadInv、目标与 UNKNOWN、T01/CAE、T02/Diagnostics、DRAFT_NOT_PERSISTED、MANAGED_WORKFLOW 及 AbqJobPilot 评估建议。未估算 F，也未调用 Solver。 |
| 首轮证明读取 | 当前活动回合的第二个 app-server 读取视图可返回 thread=notLoaded、turn=interrupted，即使两条 MCP 项均为 completed 且时间新鲜。拒绝将此视图作为已确认的回合；最终入口返回 RELEASE_IDENTITY_UNAVAILABLE / CONNECTOR_TURN_UNCONFIRMED。此前中间版本曾误分类为过期。 |
| 同线程接续 | 首轮结束后测试驱动通过 thread/resume 续接，未重发 GitHub 查询，也未要求用户提供 pin 或再次授权。已审查的测试包装器先检查真实线程与隔离配置，再调用候选入口。进程退出 0，返回 VERIFIED_RELEASE_IDENTITY、.17 私有发行身份和独立 Manifest SHA-256 8ad1928d4e909a8ee38d91ba9b31b272cedaa9fef4edb57eaeca029e3c7b971d。此步骤是驱动辅助接续，普通 UI 首轮全自动接续仍待验证。 |
| Main 创建或复用 | BLOCKED_HOST_MAIN_CREATION。隔离 Host 的工具枚举未提供 Codex Desktop Project 选择及可按项目创建、回读可见 Main 的接口；thread/start 的本机协议没有 projectId。未返回 Main 引用，未将当前线程改名或使用另一实例代办。 |
| 较早限制配置 | approvalPolicy=never 时仅记录到两条成功的 GitHub 调用。助手报告本地检查受策略限制，未取得命令成功回执。最终真实命令测试使用 on-request + auto_review。 |

## 可复算的回归

- 单测运行器最初拾取了共享解释器中的旧包，随后遇到默认 TEMP 权限错误。指定此次 checkout 的 src 和独立临时目录重跑后，139 项 Task Card、项目、科研约定、能力发现和会话单测通过。安装态 27 项 Sanity Model / 约定检查通过。
- 私有记录测试包括 .17 和合成未来版本、移动 ref、连接器失败或缺失、Git blob 篡改、版本或后端插件 ID 不符、清单与交接依赖篡改、宿主 setup 内容不符、安装版本不符。未来版本是同一逻辑的离线测试，未冒充真实平台发行。
- 现有固定 Git Marketplace 路径继续验证 ref、Tag、Release、HEAD 和安装文件。17 项更新器边界回归通过；使用 GitHub 的真实 .11 Tag 和 Release 回执跑原有发行摘要校验，Manifest 为 6877078efd70f9effb8d7a420faef79931ad364baba725793573cb79feb7b478。本轮未执行 Marketplace 升级。
- Creator 规范化布局投影下 bind、doctor、基础约定和 23 项拒绝用例通过。15 项立项路由检查通过。错误调用身份对 17 项操作均被拒绝；交接脚本的已验证 Main 复用、创建不明保持原请求、标题冲突、错误项目及冲突回执测试通过。这些状态机测试使用合成身份。
- 本地 .18 ZIP SHA-256 为 9b7c8edcfe058e581e63a8baa7aa00657c25d274d236b20140863b073a414d55，Manifest SHA-256 为 4ae2c9247f579fcabe0fa43be67330960f56b3b8863406ae7ac7ee7804a1bebe。ZIP 含 23 个文件。

**结论**：PRIVATE_RELEASE_IDENTITY_DISCOVERY = PASS（同线程续接）。FIRST_TURN_AUTOMATIC_HANDOFF = PARTIAL。SETUP_TO_VERIFIED_DESKTOP_MAIN = BLOCKED。B_UI_END_TO_END = NOT_TESTED。.18 保留为本地候选，下一次正向验收需要能在同一隔离配置中证明 Desktop 项目归属和 Main 回读的宿主。

两次回合均由官方 thread/read 在结束后回读，摘录包含两个 GitHub 工具的请求、状态、身份入口的退出码与实际最终回复。[脱敏 Host 回执](PRIVATE_RELEASE_IDENTITY_PREVIEW18_HOST.json)
