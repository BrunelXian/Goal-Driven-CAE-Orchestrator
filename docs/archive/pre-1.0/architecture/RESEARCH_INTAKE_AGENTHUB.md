# Research Intake & Task Cards v1

本决定适用于 Research Preview。一个研究项目只有一个科研 Main。专业角色由任务、输入、证据需要和宿主的权限能力决定。AgentHub 负责项目内的编排状态；可选的监控对话只能展示该状态。每个项目无需启动单独的后台服务。

## Setup 到 Main

1. Setup 消化已给出的研究目标、变量、约束、资产与判据，生成可用于会话标题的短名，显示摘要以及 T01 模型资格、T02 能力发现两份草稿。用户可以暂时没有模型、Python 或可写项目。
2. Setup 通过宿主确认 Desktop Project，先检查同项目 Main 的交接回执。请求键绑定本机 Host 与 Desktop Project。claim 只允许一个创建者；响应丢失后从已有键对账。未知结果保持 CREATE_UNKNOWN。已取得会话引用但尚未核对时保持 REF_RECORDED。项目、标题、引用及 Main 的接收内容核对后才标 VERIFIED。经过核对可复用，不为重试创建第二个 Main。
3. Setup 结束。阻断时保留两张 DRAFT_NOT_PERSISTED 草稿、摘要、UNKNOWN、接续条件。Setup 没有科研求解、迭代或提交作业的职责。
4. Main 首屏读回研究目标、基准资格、任务与状态、UNKNOWN 和下一步。明确授权保存后，新项目使用现有 v3 ResearchProject。Main 使用 Host 注入的线程身份与同用户配置下的 VERIFIED 回执，按项目 ID 和修订登记任务。会话创建和写库是两次不同的动作。

## 权威存储与状态转换

v3 ResearchProject 的 SQLite 工作流审计日志保存 research-task-v1 事件；沿用现有事务、锁、修订、存储世代及哈希链。新旧项目共用现有数据库结构。Task Card 可以在冻结研究约定之前登记。后来建立的约定不追溯改写旧卡的输入。v1 角色契约及重放规则应保持兼容；语义不兼容的更改需要新的事件版本与显式迁移。

| 操作 | 输入与门禁 | 权威结果 |
|---|---|---|
| task-init | 经核实的 Main、授权保存的项目、预期修订、稳定请求键、摘要与两张完整草稿 | 同一事务登记两卡，保留各自目标、判据、交付物和资产摘要 |
| task-create | 同一身份、未占用任务 ID、已发布任务类型、已存在的前置卡 | 记录责任角色与契约、职责、输入、证据要求、权限边界和当时的约定摘要 |
| task-update | 合法前态、依赖、有效修订及请求键 | OPEN → IN_PROGRESS 或 BLOCKED，BLOCKED → IN_PROGRESS，IN_PROGRESS → SUBMITTED 或 BLOCKED，SUBMITTED 可返回 IN_PROGRESS |
| task-list | 指定 v3 项目，重新打开并重放审计链 | 返回项目修订、摘要和卡片，不要求写权限 |

每次写入后重新打开快照并比较请求摘要。重复键和同一输入返回原回执；键重用但内容不同、身份变化或陈旧修订均拒绝。SUBMITTED 需要证据引用；引用附 SHA-256，文件内容的独立验证由相应验证流程完成。依赖 SUBMITTED 只表示已收到材料。执行进度、证据验证、科学判定和作业授权是四个不同维度。任务记录本身不授予后端权限。调用身份验证覆盖正常受信的本机用户环境，不构成针对控制本机用户文件或进程环境的对手的安全边界。

## 动态角色与专业会话

1. Main 建卡，项目 AgentHub 先登记，再匹配版本化角色定义。每项定义含支持的任务类型、所需输入、交付物、允许工具及证据要求。当前提供 CAE、Diagnostics、ODB、Independent Validation、Optimization、Research 六种起始定义。注册或查询任务不会创建任何专业会话。
2. 专业会话的复用条件是同一项目、角色定义摘要、有效工具边界、Host 身份和有效授权。每次领取新任务仍须校验具体 Task 及输入。多个符合条件的任务可以分配给同一专业角色。新契约应在可信发行源中扩展；用户任务文本不能注册可执行角色。
3. Host 必须证明实际会话、项目、角色、任务及有效工具许可。当前产品报告 BLOCKED_HOST_ROLE_BINDING。已验收的旧 AOO SessionHub 仍管理它自己的专业任务记录；它可以显式装载额外获准的角色文件及摘要，其旧版“一任务一会话”路径未接入这个产品。v1 不在 Host 缺少证明时启动或复用专家。
4. ODB 负责按选择器提取数据。Independent Validation 用独立来源评估模型、数值结果与主张；不得改动冻结条件。Deterministic Validator 属于可信计算组件。任务执行者自述、分析完成或单条响应曲线均不能提升科学状态。Main 汇总审查，研究者保留约定与执行授权。

## AgentHub 与执行后端的边界

本次交付项目级 Task 状态、Main 身份、请求回执和 Artifact/Evidence 引用。通用 Message 投递、后端 Approval/Grant、专业会话执行与独立验证签收不在 v1 中实现。它们可以引用已有任务 ID 和修订，不能仅由任务提交者填写成功标志。

capability-discovery 仅检查指定本地入口及公开发行源码元数据，分别返回 Abaqus 文件、AbqJobPilot 源码版本、公开工具声明、服务状态、项目身份及授权。生产服务仍需要正式 MCP 或受支持的服务入口、真实项目绑定及对应授权。测试适配器或软件安装信息不能证明生产连接。
