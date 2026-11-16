# 私有 Preview .19 的 Desktop RPC 诊断

**结论：RPC 诊断 PASS；本次 Desktop 自动发行身份核验 BLOCKED；Setup → Main NOT_EXECUTED。** 受测已发行 .19 来自个人私有插件，源码提交 `3069b9891a7cb322b1a5e3ef9c5d5071f5ac58b6`，独立 Manifest 为 `e7ed5de9cc6f54f2d4edda7c9ac3ec70f56b8d3835969d0b67e40804a209554d`。从 Desktop 开发会话对实际安装运行外部核定的修订入口；这些源码尚未进入私有发行。

## 根因及修改

原 .18、.19 的 update.ps1 和 A 实际安装副本对应同一 Git blob `e84b475ab605493bf317347e2fa3198e4ca529b4`。回收补丁 SHA-256 `d6b92f6b0be4cfea86ab4b271621ba1a9c07d7025632e1d779b7efd538767f7e` 与交付清单匹配。核对旧报告、差异、Git 应用上下文后，移植脚本、说明和针对性测试。旧报告中的成功运行属于旧验证器与隔离 app-server。受控复现：让子进程读完 initialize 请求后退出 29，安装态旧传输返回 HOST_RPC_UNAVAILABLE。提前使用错误 CLI 参数的另一次复现发生断管写错误。上述条件说明旧错误含义不唯一，B 的实际进程环境和失败阶段仍未知。

私有身份路径复用一次只读 app-server 连接。CLI 来自进程 PATH 中的应用；缺失时仅查当前用户已注册的特定 OpenAI Desktop 包。启动前验证 Windows Authenticode 和发行者。其他发行者或无法确认的签名阻断。握手回读的 codexHome 必须匹配当前有效目录。按真实线程及回合分页读取结构化 GitHub 工具回执，再检查私有 plugin/read、plugin/skill/read 与包外 pin 固定的磁盘文件。超时、EOF、读写失败、RPC 错误、交互要求、回执窗口和待续接有不同理由；对外仅输出阶段、方法、安全代码、可用退出码等。自然退出与验证器清理进程分开记录。Main 唯一性、请求标识及写入门禁未改动。

## Desktop 能力与门禁

| 检查 | A 机实际观察 |
| --- | --- |
| CLI 与子进程 | WindowsApps CLI 定位、签名、启动、initialize、home 对照、线程头回读成功。只在测试子进程 PATH 中移除可执行入口后，正式已注册包回退同样通过。 |
| 连接器回执 | GitHub 正式接口取得 main ref 及固定提交中的 .19 receipt。Desktop 自身 read_thread 显示本回合 inProgress，两条工具调用 completed，摘要视图未交付其结构化结果。额外 app-server 对同一线程回读到 interrupted 的回合快照，修订入口在 connector_proof 以 CONNECTOR_TURN_UNCONFIRMED 停止。不能据此放行，也不能据此认定 B 遇到相同原因。 |
| 安装身份分项 | 同一 A 默认 Desktop 用户配置下，独立分项测试实际调用 plugin/read、plugin/skill/read 校验本机已启用 .19 的产品/版本、setup 正文，再检查固定 Manifest 与受保护交接文件，成功。该分项使用已知回执，未越过完整身份入口。 |
| 当前连接复用 | 已安装 CLI 提供 app-server proxy 默认控制套接字。本机探测退出 1（Windows 10050），未建立握手。当前客户端的线程摘要缺少可供脚本回验的连接器结果正文。保留一条受约束的连接，不能信任模型转述或任意 JSON。 |
| Main | 原生 list_threads 与 read_thread 可回读 A 专用 Project 内已有的 Main，其历史包含 T01/T02。本轮身份门禁未通过，未 claim、创建或重新登记 Main。观察既有 Main 不构成本次 Setup 复用或新建的证明。 |

## 回归与后续验收

- Windows PowerShell 5.1 与 pwsh 的协议测试覆盖 EOF、超时、非法响应、子进程要求交互、逐方法拒绝和数值错误码脱敏。回执测试覆盖回合/线程错配、过期、失败、不完整与窗口耗尽。
- 对独立测试目录构造未发布的修订文件集。真实 stdio T02 在临时后端 Project 读取和登记成功，重放幂等，新进程回读修订 4，执行授权 false。研究约定、Task Card、项目存储、协议拒绝和发行 Core 边界合计 104 项通过。安装形态 Sanity Model 27 项通过。身份拒绝、更新器与 Main 交接防重测试通过。
- 普通 Desktop Setup 的待验路径为取得同一回合、同一真实线程的可信回执；如果当前回合未持久化，保留草稿和原授权，在同会话续接核验。只有 VERIFIED_RELEASE_IDENTITY 才可 inspect / claim，验证同一 Project、唯一 Main、卡片接收及重复请求。始终不能以后台 thread/start、手工创建或旧 Main 的存在代替该验收。
