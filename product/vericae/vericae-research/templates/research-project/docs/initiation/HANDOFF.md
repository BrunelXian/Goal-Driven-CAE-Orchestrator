# Initiate → Conduct Handoff

状态：DRAFT；尚未开始 Conduct，没有执行授权或已完成求解。

接收方为项目 Main。接续前读取实际文件，核实内容与摘要，明确仍待确认的研究条件：

- [Research Card](../../research/RESEARCH_CARD.md)：当前研究草案与下一步。
- [Task Cards](../../research/TASK_CARDS.md)：任务输入、限制、预期输出；当前尚未派发。
- [Sanity Model Specification](../../models/SANITY_MODEL_SPEC.md)：M0-DRAFT / UNVERIFIED。
- [Workspace README](../../README.md)：目录职责、单写者与日志纪律。
- [AbqJobPilot link](../../.abqjobpilot/link.json)：当前未绑定；不含凭据或 Grant。

下一步：Main 确认研究问题和模型定义，记录明确任务与允许的成果目录。
本交接文件是研究资料入口，不替代实际消息交接，也不证明 Main/Subagent 会话已建立。
研究日志后续追加到 `docs/research-runs/`，本模板不创建日志或科研任务。

若需要执行事实，应通过 AbqJobPilot 核实原始 Receipt/Run；文件检查器的本地 PASS
不代表人类授权、预算、求解资格、数值结果或物理结论已成立。

## 长期角色对话（由Main核验后维护）

同一实际Codex项目；先查找复用，再只补缺项。名称确认前下列ProjectName为模板占位。
本模板未创建任何真实聊天；身份未暴露不编造，文件存在不能证明线程存在。

| 角色 | 预期对话名 | 实际Thread ID/宿主引用 | 实际Project ID | 核验状态/依据 |
|---|---|---|---|---|
| Main | `<ProjectName> Main` | NOT_EXPOSED | NOT_EXPOSED | NOT_CREATED / 未核验 |
| CAE | `<ProjectName> CAE` | NOT_EXPOSED | NOT_EXPOSED | NOT_CREATED / 未核验 |
| Results | `<ProjectName> Results` | NOT_EXPOSED | NOT_EXPOSED | NOT_CREATED / 未核验 |
| Independent Validation | `<ProjectName> Independent Validation` | NOT_EXPOSED | NOT_EXPOSED | NOT_CREATED / 未核验 |

另记录左侧同项目可见、用户可打开、重启恢复的人工观察；未测写NOT_RUN。
直接人类对项目/目标及Main↔角色通信范围的授权来源须真实可核验，不能由正文自签。
后续Main先写Task Card再原生跨对话派发，角色在本线程产生原回复供Main真实读取。

## 模型配置记录（请求值与实际值分开）

以下为0.5.5请求默认，须核对当前目录后通过原生参数配置；本模板没有创建线程或验证生效。

| 角色 | 期望model / thinking | 实际请求 | 实际观测model / thinking | 真实Thread引用与核验来源 | 状态 |
|---|---|---|---|---|---|
| Main | gpt-6.2-astra / high | NOT_RUN | NOT_VERIFIED | NOT_EXPOSED | NOT_RUN |
| CAE | gpt-6-luna / medium | NOT_RUN | NOT_VERIFIED | NOT_EXPOSED | NOT_RUN |
| Results | gpt-6-luna / medium | NOT_RUN | NOT_VERIFIED | NOT_EXPOSED | NOT_RUN |
| Independent Validation | gpt-6.2-sol / high | NOT_RUN | NOT_VERIFIED | NOT_EXPOSED | NOT_RUN |

创建成功或写出预期值不证明配置已生效；缺设置/回读能力报告MODEL_ASSIGNMENT_UNAVAILABLE及最小人工操作。
复用既有线程不删除/重建，不静默覆盖模型；需要调整先提案记录，真实配置核验后生效。
