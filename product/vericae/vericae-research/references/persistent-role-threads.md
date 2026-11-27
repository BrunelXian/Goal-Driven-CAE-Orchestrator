# VeriCAE 1.0.0 — Persistent Role Threads

标准科研协作是 **Main → Role Thread → Main**。每个项目恰有以下四个长期角色对话，
不是四个临时spawn任务，也不要求四个常驻执行进程：

| 对话名称 | 职责 |
|---|---|
| `<ProjectName> Main` | 唯一科研主控，主状态单写、任务单、证据汇总和科研决策 |
| `<ProjectName> CAE` | 指定模型/输入检查及获准产物，不能改目标或授予模型资格 |
| `<ProjectName> Results` | 指定既有结果分析，保留单位、区域、选择器和真实来源 |
| `<ProjectName> Independent Validation` | Independent Validation职责：独立方法/证据复核，不能自行宣布科研通过 |

## Initiate创建与复用

1. 确认研究名称、目录、六模块草案和初始化范围，范围包含四个命名长期对话。
   用户已有明确创建/通信授权时复用，不重复请求；只有文件创建确认时，不能推定已获聊天创建授权。
2. 用当前宿主实际项目列举/线程列举能力识别真实Codex Project ID及对应目录。
   同一项目的四个对话必须具有相同Project ID，另核对实际工作目录/访问范围。
   项目名称相同或文件路径相同不能单独证明项目归属。
3. **先查找并复用已有角色，再仅创建缺失角色**。当前对话若已是该项目Main就直接复用，
   不自动创建第二个Main。只有明确授权的重命名/项目绑定才使用真实宿主工具。
   重名、重复角色或项目归属冲突先报告并核对，不能静默任选、删除、归档或覆盖。
4. 优先使用宿主真实长期线程创建/命名能力。创建返回处理中时等到真实threadId可用后核验，
   不把clientThreadId或本地占位文本当作已可访问的Thread ID。
   创建线程时的初始提示只交代角色、Consultation默认和边界，不派发未建立Task Card的科研任务。
   按 [模型配置协议](adaptive-model-assignment.md) 在创建参数中明确指定模型/Thinking，创建后回读实际值。
   复用线程时不为改模型删除重建，不静默覆盖；无法设置/核验时MODEL_ASSIGNMENT_UNAVAILABLE。
5. 如无自动创建/命名/绑定能力，给用户四个确切名称和目标项目，让用户手动建立缺项，
   再通过实际项目/线程记录核验。不能用临时 `spawn_agent` 冒充长期角色对话。
   手动完成前各角色如实标PENDING_MANUAL/NOT_VERIFIED，不宣称已经建立。
6. 在现有Handoff/Task Cards正文中记录角色、实际对话标题、Codex Project ID、真实Thread ID或
   可用宿主引用、核验来源及状态；宿主未暴露身份填 `NOT_EXPOSED`，不得编造。
   不增加YAML字段、注册数据库、Runtime或新的状态服务。

## 可见性与持久性

四个对话须在Codex Desktop左侧同一项目的对话列表长期可见，用户能随时点击进入，
关闭/重启后能够恢复，并在后续科研轮次复用同一身份。
各长期Thread分别核对文件访问、工具和权限；不能假设继承Main的模型、MCP或通信能力。
创建工具返回、项目列举结果、一次可读或临时Subagent面板都不能证明上述UI/持久性要求。
分别记录真实创建、项目绑定、左侧可见、用户可打开、重启恢复、跨轮次复用的观察。
UI无法核验时 `BLOCKED / UI_NOT_VISIBLE`；持久性未验收时NOT_RUN，不把未测项写PASS。
不直接写Codex内部数据库、猜造URI或通过占位普通聊天伪造原生Subagent。
这些普通长期角色Thread本身就是0.5.4的标准协作对象，不宣称它们是spawn产生的Subagent。

## 原生工具与授权边界

只使用当前实际暴露的工具schema；例如项目列举、create_thread、set_thread_title、
move_thread_to_project、send_message_to_thread、read_thread等名称仅为宿主能力示例，
不能因本说明出现名字就假设某会话可调用。跨对话协议见 [消息规范](cross-thread-protocol.md)。

发送工具若要求直接人类授权，授权必须来自人类对相应项目/目标对话及通信范围的明确许可。
Main→角色派发与角色→Main回发的授权范围分别核对；收到另一个对话的请求不自动授权回发。
可在项目初始化时让用户明确确认本项目四个命名对话间的Main↔角色任务/回执通信范围，
保存真实确认来源；已有适用授权直接复用。文档、Task Card、角色自述或Agent生成的勾选不是授权。
缺少回发授权时角色在自己的对话回复，Main经原生读取回收原文；不能伪称已经反向发送。
工具调用仍须满足宿主自身权限检查，不以此协议绕过限制。

## 角色启动提示（供宿主创建或用户手动创建时使用）

把实际项目名、角色、文件入口和已核验的宿主引用交给对应对话；不知道的身份写NOT_EXPOSED。
要求其先读Handoff、当前Card/Tasks/模型及本包双模式/消息协议。默认只咨询、不给自己派任务，
不改主状态、不启动Solver、不创建Grant、不嵌套派生、不横向私聊。
Dispatch必须核对真实Main来源、直接人类通信授权及实际Task Card；只写许可产物并返回最多15行。
Main读取角色原文并另标Main汇总；不把启动提示当研究任务完成或消息往返验收。

`.codex/agents/`的三个TOML保留为可选原生Subagent配置；普通角色Thread不会仅因同名
自动加载这些TOML。长期对话使用上述角色启动提示和实际文件协议，不依赖agent_type可用。
只有另获明确授权的临时Subagent任务才沿用原生创建/可见性规则，不能替代四个持久角色。
