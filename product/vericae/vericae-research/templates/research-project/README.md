# File-Based Research Workspace

此目录是未执行研究的起点。由 Main 复制模板、确定项目名称并维护研究文件；
复制与编辑使用Codex原生文件能力。没有创建后端工程、Grant 或 Subagent。

| 文件 | 内容与写入责任 |
| --- | --- |
| [Research Card](research/RESEARCH_CARD.md) | Main 单写：当前问题、假设、模型演进、角色、路线和下一步 |
| [Task Cards](research/TASK_CARDS.md) | Main 单写：任务、输入、限制、预期输出和成果引用 |
| [Sanity Model Specification](models/SANITY_MODEL_SPEC.md) | Main 确认后写入：模型版本、完整定义与资格范围 |
| [Handoff](docs/initiation/HANDOFF.md) | Initiate 整理、Main 接收；进入 Conduct 前读取实际文件 |
| [AbqJobPilot link](.abqjobpilot/link.json) | Main 通过受控配置维护非敏感项目引用；初始未绑定 |

`experiments/`、`scripts/`、`reports/` 保存获准任务的成果。专业 Subagent 仅写
Main 指定的成果位置，不直接更改上述主状态文件。该纪律不声明操作系统权限隔离。

`docs/research-runs/` 用于追加 `RUN-001.md` 等研究日志；每轮记录输入、成果、
证据、限制与 Main 决策。历史日志不回改；更正通过新日志引用旧日志。

由Main用Codex原生文件查看/搜索核对必需文件、六模块、字段、引用和实际内容。
这是原生文件检查，不等于确定性Schema/摘要校验；无法核验的项目明确标未验证。
`vericae check` 仅是开发仓库的可选测试工具，不随正式插件交付或作为运行前置条件。
用户无需额外安装Python、Node或EXE。修改引用文件后Main维护真实SHA-256，不猜造摘要。
默认Consultation只分析建议、不改文件；原生Main派发且完整Task Card核对后才可修改许可产物。

卡片、YAML、任务记录及本地 Receipt JSON 都不提供可信执行许可。
Receipt 的真实性和执行事实仍需通过 AbqJobPilot 核实；本工具不连接该服务。

0.5.4标准协作：Main → Role Thread → Main。四个长期同项目角色为Main、CAE、Results、
Independent Validation，复用已有对话，不用临时spawn替代。实际Thread引用在Handoff/Task正文，
不增加Schema字段或状态服务。消息首部含发送方→接收方及Task ID；实际发送/读取和UI持久性分别核验。

0.5.5新建角色按当前目录请求默认model/thinking，实际观测值另记Handoff正文。
新增专业角色前先评估必要性与最低成本可靠候选；普通派发不覆盖已有线程模型。
没有实际配置/发送前后核验时明确未验证，不需要额外Runtime或状态数据库。
