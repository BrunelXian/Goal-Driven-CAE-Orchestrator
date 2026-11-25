---
name: initiate
description: 当用户用自然语言提出新的CAE科研问题、希望立项或开始研究时使用。理解物理问题，确认项目名称与六模块草案；确认范围后建立文件工作区及同项目四个长期角色对话并交给Conduct。纯科研规划不需要MCP、AbqJobPilot、Abaqus或Grant。
---

# Initiate CAE Research — VeriCAE 0.5.5

你把科研意图整理为实际研究文件，由 `<ProjectName> Main` 接续。
本阶段不运行Solver、不要求已有Grant、不创建或宣称已创建真实Subagent。

先读取本包的 [共同契约](../../references/three-skills-contract.md) 和
[Workspace Format v1](../../docs/vericae/WORKSPACE_FORMAT.md)。沿当前Skill路径定位插件根，
核对随包 `templates/research-project/`；不要假定当前目录就是插件或项目目录。
使用002A现有Schema，不增加Frontmatter字段，不调用历史项目创建或后台接口。

## 1. 理解研究与自然语言规划

从用户原话提取：研究命题、目标量/单位/方向/区域、已有模型或数据、关键物理条件、
允许探索范围和停止标准。区分已提供、工作假设与待检查事项；不先要求安装整套执行环境。

例如“我想研究悬臂梁末端达到1 mm位移所需的载荷”：理解为载荷反求问题，
先核实位移分量与测点、单位、几何、材料、固支与加载方式。可以提出线弹性梁理论
作为待核实的参考，不能擅自指定尺寸/材料、把位移幅值解释成已确认的方向，或给出
无来源的有限元结果。先形成研究计划和必要的少量澄清，不把所有未知项变成一次性问卷。

提议简短项目名 `<ProjectName>` 并取得用户确认；已有明确确认直接复用。
展示完整六模块Research Card Draft：保留模板上下边界、原生Markdown标题、❶–❻模块、
Model Evolution表、两张独立双列角色表、Roadmap和引用块Next Action。
使用真实草案状态；Main/CAE/Results/Independent Validation仅为拟议分工。
在项目名称及目录/创建范围未确认前，只在对话展示草案，不创建项目文件。

## 2. 用户确认后建立文件工作区

确认 `<ProjectName>`、明确目标目录及允许创建文件的范围；只询问仍缺的确认，不重复请求。
既有目录先检查：若已有研究文件，转Conduct恢复；不覆盖原文件、模型或旧工程。
在已确认的新目录复制随包模板，保留所有必需文件与空目录。由Main使用普通文件工具编辑，
不增加初始化服务、数据库、自动迁移器或新的CLI写入命令。

- `research/RESEARCH_CARD.md`：仅使用v1已有字段，更新 `project_name`、`main_writer`、
  正整数 `revision`、`phase: PLANNING`、真实模型版本及 `qualification: UNVERIFIED`。
  初始 `receipts: []`；主卡正文同步实际名称、研究问题、未知条件、模型与下一步。
- `research/TASK_CARDS.md`：记录Main拟议任务、实际输入、限制和预期成果，未派发就写未派发。
- `models/SANITY_MODEL_SPEC.md`：写明已知定义、版本、用途资格与缺口；模型未建立/未验证如实记录。
- `.abqjobpilot/link.json`：未绑定时两项ID保持null；不从项目名猜后端ID，不写任何凭据或权限。
- `docs/initiation/HANDOFF.md`：用项目内相对链接指向真实Card、Task、模型、README和link文件；
  写明当前问题、未决条件、Main接收入口、角色未建立/未验证和纯科研模式。
- `docs/research-runs/` 留作后续追加日志；初始化不虚构已执行的Run或Receipt。

更新被引用文件后，由Main使用宿主实际可用的原生文件/摘要能力维护Card的SHA-256；
不复用模板中已经失效的摘要，不编造摘要。没有摘要能力时明确摘要未验证并保留待核对事项，
不要求用户安装额外语言运行时，也不宣称确定性校验通过。
Frontmatter路径相对项目根，Markdown链接相对所在文件；不对Card自身建立循环摘要。

## 3. Persistent Role Threads — 四个长期角色对话

科研文件正式创建后，按 [长期角色对话规范](../../references/persistent-role-threads.md)
建立或复用同一Codex项目的四个长期独立对话：`<ProjectName> Main`、`<ProjectName> CAE`、
`<ProjectName> Results`、`<ProjectName> Independent Validation`。
先查找并复用已有角色，再仅创建缺失角色；不在每轮科研重复创建。
当前对话已是该项目Main时直接复用，不自动创建第二个Main。

确认初始化授权包含四个命名对话；已有明确授权直接继续，不重复询问。
只确认科研文件创建时，不能推定已经授权创建聊天或向其他聊天发消息。
用真实项目/线程列举及创建/命名能力核对同一Project ID、实际目录和角色职责；
原生创建不可用时引导用户手动创建并命名，再核验真实存在，不用spawn代替。
将实际Thread ID或可用宿主引用写入Handoff/Task Cards正文；未暴露填NOT_EXPOSED，不编造。
四个对话须在Desktop左侧同一项目列表长期可见、可随时点击、重启后恢复；逐项留待实际核验。
创建返回或静态文件不证明UI与持久性。未验证如实记录，不宣称多角色已就绪。
初始角色提示只说明Consultation默认和边界，不执行没有Task Card的科研任务。
后续按 [跨对话协议](../../references/cross-thread-protocol.md) 由Main派发、读取原回复。

## 4. 自动模型配置与实际核验

按 [Adaptive Agent Model Assignment](../../references/adaptive-model-assignment.md) 和
[模型策略](../../references/model-policy.yaml)，先核实当前目录中的完整ID与支持的Thinking。
新建四角色默认：Main `gpt-6.2-astra / high`，CAE与Results `gpt-6-luna / medium`，
Independent Validation `gpt-6.2-sol / high`；目录缺项时不猜ID或静默替换。
创建时通过真实原生线程工具明确指定model与thinking，不把提示词里的名称当成配置。
创建后核验实际生效模型和Thinking，分开记录期望/请求/实际观测值及来源，不能只记录预期。
复用已有线程先观察配置，不为改模型删除或重建，也不静默覆盖已有值。
缺设置参数、请求被拒绝、配置不符或缺实际回读能力时报告 `MODEL_ASSIGNMENT_UNAVAILABLE`，
说明用户需在哪个既有线程选择哪个模型及Thinking，并在实际核验后才报告完成。
新增专业角色先由Main做Role Capability Assessment，已有四角色够用就不新增。

## 5. 检查与交接

使用Codex原生文件查看/搜索，检查必需文件、六模块、YAML字段、引用、实际内容与未决条件。
这是原生文件检查，不等于确定性YAML解析/摘要校验；明确实际核对范围和未验证项。
`vericae check` 仅保留在开发仓库作为可选开发测试工具，不随正式插件交付或作为运行门槛。
缺少该工具或Python/Node/EXE不阻止立项与文件交接；不要求安装这些额外前置组件。

明确报告：文件检查结果、真实文件路径、模型资格未验证、未执行计算；
`AbqJobPilot MCP: UNAVAILABLE`、`connection: NOT_CONNECTED`。
这些执行缺项不阻止立项、静态模型检查或已有资料分析。

提供明确接续语句：

> 在 `<ProjectName> Main` 中使用Conduct CAE Research，先读取
> `<ProjectPath>/docs/initiation/HANDOFF.md`，再核对当前Card、Task、模型和最新日志。

不把文件交接说成真实聊天创建/消息往返；复用同项目Main，不重复创建。
宿主真实对话操作不可用时明确 `BLOCKED / HOST_CAPABILITY_UNAVAILABLE`；保留文件入口，
由现有Main继续允许的工作。这里只交付初始化，不继续求解或后端授权切片。

环境问题转 [Set Up Research Environment](../setup/SKILL.md)，已有项目转
[Conduct CAE Research](../conduct/SKILL.md)。
