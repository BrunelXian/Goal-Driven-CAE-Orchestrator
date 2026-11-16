# Engineering Tool Integration · A 端验收（2026-11-16）

## 判定与发行范围

**PARTIAL。** 已实现可从开发源码调用的 T02 只读入口。在 Windows A 机上，它通过正式 AbqJobPilot stdio MCP 服务读取指定后端 Project，再将证据提交给现有 ResearchProject 任务账本。测试数据是隔离的正式 Project 和一条预置状态记录。现有用户工程 Project 的生产绑定、普通私有插件 UI 调用此次开发入口、真实计算和 ODB 科学验证均未验收。本提交属于源码同步。

| 验收对象 | 状态 | 可复核的结果 |
|---|---|---|
| 真实 Desktop 科研管理基线 | PASS | 通过 Host 的项目、线程列表及线程回读核对同一 Main 的 host、project、thread、title 与 VERIFIED 交接。成功命令输出含 ResearchProject schema 3 创建回执、修订 2 的 REGISTERED_READ_BACK、两次完全一致的 T01/T02 读取。父线程记录了两个完成的原生子任务，两个子线程都可回读成功命令。 |
| 原生证据回传与摘要验证 | PASS | 本轮另派一个原生 T01 只读子任务读取新建的 73 字节挑战文件。父会话独立复算后将匹配摘要交给集成测试。变更摘要被拒绝。子任务调用及归属由 Host 回执证明；单独的哈希匹配只证明字节一致。 |
| 管理基线可重跑、重启恢复 | PASS | 用正式 .18 安装文件在临时设置下执行真实 launcher、bind 和持久化。此路径明确使用合成 Host 身份。逐命令新建进程，T01/T02 登记与重试只增一次修订；状态、证据、无授权状态在新进程重开后保持一致；重复 T02 提交返回同一回执，最终修订 6。错 Main、错研究项目、错后端项目、篡改字节均被拒绝。 |
| 产品发现与版本兼容 | PASS（来源和接口）；本机安装登记 PARTIAL | A 机 Windows 卸载登记查询 NOT_LISTED，便携安装状态未知。正式源码与真实握手均为 0.2.2，MCP SDK 2.3.0，实际协商协议 2025-11-25，业务响应 schema 1.0。开发/稳定工作区均未改写。 |
| 真实服务与 T02 | PASS（隔离数据） | 从固定上游提交启动正式服务并握手。服务返回五个已审核工具。仅调用 abq_list_jobs（queue/history）和 abq_job_status（queue）。队列 1 条、历史 0 条，指定记录为 QUEUED。A/B 两个后端 Project 混淆时拒绝。前后完整目录文件摘要一致。 |
| 现有科研 Project 的 T02 联通、普通插件发现 | 未验 / BLOCKED（缺少指定绑定） | 本轮没有默认选择用户项目。已配置的业务现场身份、日常 Host 对此 MCP 的访问以及可分派的严格专业角色权限仍需分别验证。 |
| 旧版仓库架构保护测试 | PARTIAL | 干净父提交与本次源码均为 175 通过、8 失败，失败用例名一致；本轮新增协议拒绝/降级测试 10 通过。失败涉及 AF 只读边界、基线字节、依赖方向、直接写入、旧依赖、延后接口、M01 文件清单和研究存储 SQL 边界。未修改这些检查。 |

## 如何从 Main 使用开发入口

使用已有开发解释器，本轮实测 Windows CPython 3.12.10。工程 MCP SDK 是单独的可选依赖，Research Core 和私有插件的发行依赖未变。将仓库的 `src` 置于**该开发进程**的模块搜索路径，或使用已安装对应 GD-CAE 源码的开发环境。入口为 `product/research-preview/tools/abqjobpilot_probe.py`。执行时保留 Host 注入的实际线程身份。

1. Main 从已授权工程上下文取得两个不同的身份：GD-CAE ResearchProject ID、正式 AbqJobPilot Project UUID。以 `binding-ref --research-id <research-id> --backend-id <uuid>` 计算绑定引用。Main 通过既有 task-init 输入引用或经授权的 task-update 将该引用记录在 T02 中，使任务进入 IN_PROGRESS。已有卡保留其原有历史。缺少独立 UUID 时保留草稿或阻断；不要用服务的第一次响应自我确认。已有冲突绑定时要求先复核，入口不会覆盖它。
2. Main 调用 `observe --project <research-root> --host <host-id> --desktop <desktop-project-id> --backend-id <uuid> --backend-project <backend-root> --backend-python <trusted-python> --evidence-dir <local-evidence-dir>`，可加 `--queue-id <queue-id>`。证据目录须已存在、支持硬链接，并与发行目录分开。运行入口核实真实 Main 和 T02 已批准的项目对，再启动 stdio。解释器由操作者从受信部署选定，不接受任务内容或远端响应提供的可执行命令。
3. 已部署的后端可在受信解释器中以 `-I -B -m abqjobpilot.mcp.server` 启动。A 机验证使用另一种明确来源：添加 `--backend-source <checkout>` 后仅从审核的 Git 对象导出 abqjobpilot 包，在临时目录运行同一正式入口。上游提交为 `7012133e7cc0176bb3e56fc24d7154ee3b90bb81`，远端 main 已核对。工作区中未提交的代码不进入此模式。直接使用既有安装的模式仍待在现场绑定下验收。[上游 MCP 接口说明](https://github.com/BrunelXian/AbqJobPilot/blob/7012133e7cc0176bb3e56fc24d7154ee3b90bb81/docs/ABQJOBPILOT_MCP.md)
4. 每次响应都独立核对服务项目 ID、响应 schema、错误字段及所查询的 scope。查询结果只保留有界的行数、状态、协商和来源信息、结构化响应摘要。单次列表上限 50，队列、历史和详情为分次采样。RUNNING 只可报告 STATUS_UNCONFIRMED。日志正文、模型路径、实际作业名不写入证据摘要。证据文件只在完整写入后发布，冲突时核对原字节。
5. 取得保存授权后，Main 用 `submit --project <research-root> --host <host-id> --desktop <desktop-project-id> --backend-id <uuid> --evidence-dir <local-evidence-dir> --sha256 <observe返回值> --expected-revision <修订> --key <稳定键>`。直接取可信 observe 工具回执中的摘要；不要接受子任务或待验文件自报的 pin。提交前重新读取证据字节、核对项目归属，再走现有 task-update 的事务、修订冲突检查与读回。响应丢失时使用原键、原修订和原摘要重试 submit，无需重复采样。SUBMITTED 是交付物收到，verification 与 scientific_decision 保持各自原状态，执行仍未获授权。

## 科研分工

- Main 依据卡片的输入、依赖和交付标准选择是否分派原生只读子任务。指定允许读取的资产和期望的返回字段，不让子任务选择信任根。收到来源可关联的回执后，Main 从原资产独立重算 SHA-256、复核范围和版本，再决定是否更新任务。子任务完成记录不能证明独立工具权限隔离、模型资格或科研主张。
- T02 单次、本机模型条件已明确时优先评估本机 Abaqus。反演、多候选、排队或需故障恢复时推荐 AbqJobPilot。计算次数或条件不清时保留 UNKNOWN。推荐、项目绑定、能读状态都不授予提交或执行权限。本客户端没有计算、enqueue、取消或 Grant 命令。
- ODB 角色只负责读取获准产物和选择器下的结果、单位、位置、步与帧，返回来源及摘要。Independent Validation 依据冻结目标和独立参考进行检验，Deterministic Validator 负责已定义的确定性判断。Main 结合证据决定下一步；排队、Job 完成或存在 ODB 都不能代替验证。

## 重跑与审计

- **Desktop 真实回读**：`tests/integration/desktop_engineering_baseline.mjs` 导出 `verifyDesktop(call, {hostId, projectId, threadId})`。在正式 Desktop 工具环境中选择已验收 Main 的真实引用，call 将所需的 list_projects、list_threads、read_thread 转给原生 Host。测试只读既有回执；输出仅含布尔值、计数、修订及状态。若缺少真实线程、成功命令或完整未截断的结构化输出，测试拒绝判 PASS。
- **真实协议与进程重启**：在选定开发解释器运行 `tests/integration/engineering_intake.py --plugin <已验证安装目录> --manifest-pin <独立发行摘要> --backend-source <含固定提交的源码库> --native-artifact <事先选定的本地挑战文件> --native-size <子任务返回大小> --native-sha256 <子任务返回摘要>`。先在当前宿主派原生子任务只读挑战文件；验收程序只校验返回内容，不会把命令行参数视作 Host 身份证明。.18 的独立 Manifest pin 为 `4ae2c9247f579fcabe0fa43be67330960f56b3b8863406ae7ac7ee7804a1bebe`。测试创建全新的临时项目与配置，不打开用户科研项目或既有后端 Recent。
- **拒绝与既有回归**：运行 `tests/integration/test_abqjobpilot_probe_rejections.py` 的 pytest 用例；现有 139 项相关单测通过。既有 `intake_handoff_checks.ps1` 覆盖重名、重复创建、响应中断、错误项目及复用，`research_main_gate.py` 覆盖 17 个约定入口与分析入口的身份拒绝。成功握手、成功工具读取、研究包身份固定与科研结论分别保留各自证据边界。
- Git 交付仅含源码、测试、可选依赖声明和此报告。实际线程 ID、业务 Project ID、队列、数据库、子任务原文、会话日志、运行时绑定文件和本地目录保持在 A 机。
