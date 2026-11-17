# CAE Agent 0.3.1 · 本机科研契约

状态为已实施的开发候选。决策范围是单用户本地服务、单项目、单基线、一个有界标量参数、一个带单位的观测量和闭区间判据。

## 权威与复用

| 本轮改动 | 已有能力与最小扩展 | 权威或调用方 |
|---|---|---|
| `project_tasks.py` 与旧 `task_cards.py` | 抽出原生 Task Card 的投影、幂等登记与读回；旧线程回执写入口继续消费同一任务实现 | ResearchProject v3 的同一事务日志 |
| `scoped_coordinator.py`、原工作流 reducer、`research.workflow.agent_*` | 将原 scoped 协调器移入共享模块，保留旧事件解码，在同一事务内登记 v2 事件、预算、证据、任务与判定；原 `scoped_fixture` 入口兼容历史项目 | ResearchProject 自己重放事件，可从原请求键重建原修订 |
| `agent_contract.py` | 原 Quantity、比较器与摘要足以校验和判断；新增冻结标量字段、理由以及上一观测摘要检查 | Core 核验提案；提出数值和选择下一步属于 Harness |
| `scoped_fixture_port.py` | 显式选择的 TEST_ONLY 测量适配器具有固定刚度和测点；历史首值和反推只供旧协议回归 | 合成观测来自适配器；区间验证只读取绑定观测和目标 |
| `research_scope.py`、`mcp_research.py` | 历史工具限定载荷并可自动给值；抽出本地授权记录和共同 stdio 分派，增加显式提案与逐候选读证据 | 受信本机操作入口选定范围，服务端按调用核验，MCP 公开项目业务 |
| `service/serve.py`、`integrity.py`、`configure.py` | 原安装启动器混合 Host 配置和业务；分出可由独立 stdio 客户端直接运行的入口，部署时核对清单、解释器、绑定和有效期 | 本机部署人员持有配置权 |
| `classic_readonly.py` | 抽出原已核查的 Classic 公共服务包装，仅发现并查询本机作业 | AbqJobPilot 自己维护队列、身份和版本 |
| Codex Marketplace、插件、Setup/Research、`installed_check.py` | 单独包装平台注册、工具发现、Skill 路由和安装态探针 | Codex 适配器；标准 MCP 客户端直接使用服务配置 |
| `examples/cae_agent` 与 QA | SDK 回归使用明示的测试提案表；安装态驱动逐份读取外部提案并返回实际观测 | 客户端不持有权威状态，工具响应与 Project 可交叉核对 |

每个项目通过现有项目根、项目标识和单一修订串联任务与工作流；此次没有新增执行数据库或调度器。完整模型资格和原有 Goal/Model/Verification 合同包继续由原 Core 维护。此入口接受明确的标量约定，尚未实现将任意完整合同包映射为可执行模型。标为 `UNCONFIGURED` 的后端可以持久化合法提案，随后在 `BACKEND_UNAVAILABLE` 停止。

## 本地授权和身份

| 旧 Host 检查保护的内容 | 本入口采用的约束 | 可作出的身份判断 |
|---|---|---|
| threadId、聊天标题、唯一 Main 窗口绑定对话来源 | 操作人员绑定项目根、持久 ID、允许操作和服务通道；进入逻辑 Main 写入事件 | `UNATTESTED`，角色是来源标签 |
| 活动 Skill 与回合后连接器回执确认路由和版本 | 安装时校验两份清单；服务逐次核验部署、授权摘要与有效期；事务检查预期修订及请求键 | 可确认载入的文件和操作范围；普通聊天路由另验 |
| 专业窗口及第二个 app-server 确认线程或安排分工 | Task Card 记录依赖、输入、交付物、逻辑角色；查询项目即可恢复 | `LOGICAL_STEP`；可对照宿主另行记录真实子会话 |

受信主体包括当前 OS 用户、操作入口、解释器及其依赖、固定的本地服务和项目存储。同一 OS 用户下恶意代码的隔离、不同聊天之间的密码学身份隔离均超出保证范围。模型无法凭 `approved`、角色或 Project ID 签发授权。开发用 Python API 供受信嵌入方使用；支持有授权边界的部署应从带清单和固定绑定的服务入口启动。

## 公共 MCP 调用约定

1. 操作入口显式选择合同、有效期、操作、全程模拟执行上限和隔离项目根。使用安装说明的 `configure.py`。受信部署独立保存返回的摘要用于重开。单作用域最多 3 次 Fixture 测量，真实 Solver 预算为零。
2. `gdcae_project_open` 可能创建项目。用其持久 ID 调 `gdcae_diagnostics`、`gdcae_workflow_status`。用预期修订和稳定键调用 `gdcae_workflow_start`，取得冻结的参数名、范围、单位、基线、目标与判据。
3. `gdcae_task_list/create/update` 所对应的三个工具分别是 `gdcae_task_list`、`gdcae_task_create`、`gdcae_task_update`；调用者可以登记辅助任务，系统保留 T01–T04。
4. 在 `PROPOSE_CANDIDATE` 时调用 `gdcae_candidate_propose`，显式提供 `parameter/value/unit/baseline_digest/reason/evidence_refs`。数值与单位分列，数值为十进制字符串。后续提案至少引用最近一次观测摘要。缺项、错单位、越界或来源不符均可从错误回执识别。
5. 依据返回的 `next_action` 调 `gdcae_workflow_advance`。用 `gdcae_evidence_read` 读取候选的原始测量、请求、输入摘要与判定。未满足目标时读取剩余预算并返回第 4 步。达到目标、预算耗尽或后端不可用时停止。
6. 断线后先用原项目和 `gdcae_workflow_status(request_key=...)` 对账。重复同键同内容可取原回执，冲突内容被拒绝。Fixture 的执行和记账发生在同一本地事务中。生产执行仍需 AbqJobPilot 的持久幂等、Grant 消费和跨进程对账。

部署命令、自然语言验收与真实模型接入资料分别见 [安装说明](../../product/cae-agent/README.md) 和 [真实 Abaqus 一次性工程输入与最小接口](SCOPED_FIXTURE_REAL_MODEL_HANDOFF.md)。
