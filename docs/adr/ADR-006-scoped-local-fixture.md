# ADR-006 本机有界 Fixture 的授权与逻辑 Main

**ACCEPTED · 2026-11-17 · 适用面为独立本地候选。** ADR-005 的原生会话约束仍适用于要求原生会话证明的动作。本决定为普通 Fixture 业务另设入口。Supersedes / Superseded by 均无。

## 调用链与决定

旧 Setup / Research 经交接脚本取得 Host / Desktop Project / thread 回执。task_cards.main_identity 校验 VERIFIED 及当前线程，t02_service 将这项校验与 backend pin、用户同意和 Task Card 状态结合。0.0.2 的 gdcae-core 只转发 ProposalIngress.status；另一 stdio 进程只公开 Classic 的 list/status。新入口由部署者预置本机 stdio 服务、发行清单、绑定文件及独立保存的绑定摘要。服务在每次工具调用时核验绑定、时限、操作和项目，在产生写入的 Core 事务内检查预期修订及状态转换。

| 原检查保护的事实 | 普通 Fixture 入口采用的机制 | 放弃或保留的保证 |
|---|---|---|
| threadId / 项目回执指认原生 Main | 固定项目根、持久 Project ID、明确记录进入逻辑 Main | 来源为 HOST UNATTESTED，窗口无法凭名字授权 |
| 活动 Skill 回执指认调用代码 | 安装方验证发行文件与实际加载 Core、后端和部署绑定摘要 | 能复查安装身份，无法证明当前回合选择了哪个 Skill |
| 第二个可见窗口证明交接已展示 | 在 ResearchProject 持久化 Main 启动、目标及首批任务 | 不保证另一个窗口可见 |
| 专家窗口 / 角色证明保证原生隔离 | AgentHub 任务契约、依赖、交付物及证据引用；Fixture 中明确记录逻辑角色 | 保留职责与可复算检查；缺少原生对话身份时不声称原生分派 |
| 回合结束后再读连接器，避免假交付 | 同步工具回执、提交后读回、预期修订与幂等 key | 直接核对持久记录，无法据此推断用户看到了消息 |
| 第二个 app-server 查询用户状态库验证 Host 来源 | 本机 stdio 启动配置 + 固定服务身份；独立 Host 只用于安装验收 | 正常业务不读 Host 私有库；Host 的 OS 和审批权限仍有效 |

保留正式 ResearchProject 事务、输入归属、任务账本、冻结判据、真实作业 Grant 及后端预算语义。对底层只读查询的证据登记属于项目写操作。授权主体是本用户预置的服务通道及其本地操作范围；模型传来的角色、布尔值、项目标识或自制 JSON 均不能扩大该范围。权限通过操作白名单限制，服务端从固定绑定选择资源，客户端不能提供文件路径、命令、许可或新目标。撤除绑定或改变其内容使原通道停止接受写入。重新配置须经本机受信入口。

## 为什么扩展现有 Core

旧 WorkflowDefinition 固定 A/B 两个模板和两次预算，并校验 max_solver_calls 等于 2。旧 DurableSyntheticPort 默认按步骤名返回预设数值。将它们直接套在零 Solver 预算的位移反馈案例上会混淆预算与证据。此候选为限定的 Fixture 协议版本，沿用项目内事务和一致性检查。Classic 0.2.2 没有本案例所需的提交与 Grant 接口。Fixture 工具只推进固定测试运算，真实提交仍由 AbqJobPilot 执行服务负责。

## 后果与未采用方案

同一 OS 用户可修改启动配置或执行其他代码，绑定摘要不是抵御该用户的签名，也不提供聊天间的密码学隔离。旧线程拒绝测试继续保护旧入口，新入口测作用域、到期、幂等、资源和篡改。未采用复写 VERIFIED、代理自签 Grant 或在 GD-CAE 中复制执行数据库。部署环境、权限或完整性错误按实际缺项处理，正常范围内的推进不需要重复同意。
