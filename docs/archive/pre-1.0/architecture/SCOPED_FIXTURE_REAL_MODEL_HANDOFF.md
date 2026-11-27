# 真实 Abaqus 接入前的一次性范围决定

截至 2026-11-17，A 机实验仅使用合成模型。目标为指定观察点在物理向下方向达到 1.0 mm，闭区间 [0.9, 1.1] mm。本次真实 Solver 预算为 0。附件记载的是历史候选，不能据此指定坐标分量、符号、测点或边界条件。

## 可复用接口与精确缺口

- Classic 固定源码 7012133e7cc0176bb3e56fc24d7154ee3b90bb81，服务版本 0.2.2。独立候选的正式工具为 abq_list_jobs、abq_job_status。Classic 的 prepare_enqueue 也不能提供实时求解提交回执。
- 只读核查的 Agent-first Develop 源码 HEAD 为 7f4b8d8f3a2c862ed8b244d495295f5d51ea0d88。execution/client.py 提供 health、inspect_plan(plan_id, expected_digest)、submit(request)、receipt(key)、run、events、progress、validations。execution/service.py 对提交校验项目及实例、计划和 Grant，并按 namespace、业务 key 和请求摘要处理回执。这是可定位的源码能力；本候选未部署或调用生产 owner。
- execution/standard_contract.py 的 issue_execution 和 check_grant、execution/standard_sequence.py 的序列门禁及产品限定的 rod_standard_adapter 均需由后端方确认适配所选模型、Operator 和安装版本。没有把固定杆件配置推广到任意 INP 的资格。真实模型还缺面向该模型族的输入准入、允许改动检查、任务级有界委托、提取器和本地公开适配。
- 若需改后端，申请范围为新增一个受限本地适配模块及其协议测试；优先调用已有 client、standard_contract 和模型族的准入。仅在现有 Grant 无法消费任务累计预算时，另申请 execution/standard_contract.py、execution/standard_sequence.py 及其预算原子性测试。确切文件差异须按对方选定的版本评审。此次未修改 AbqJobPilot。

## 资格、授权与实验顺序

| 一次性输入或决定 | 进入下一步的证据 |
|---|---|
| 权威 CAE/INP、包含文件和材料等依赖、版本与授权根目录；可读基线与独占候选/输出目录 | 文件大小、摘要、生成记录、单位体系、几何/单元、材料、接触与边界检查，确认是载荷控制还是位移控制 |
| 物理向下单位向量及其坐标系，实例、节点/集合、步、帧/时刻和位移基准 | 预先冻结选择器、局部/全局转换、分量或投影和长度单位；检查节点唯一性或冻结集合聚合规则 |
| 唯一可变载荷 F 的定义、单位、方向、作用点/区域、幅值、合法区间与最小步长 | 白名单变换生成确定性输入及摘要；逐项比较其余模型内容、网格、步和输出请求 |
| 后端与 Solver 安装版本、服务 owner/协议、项目实例、工作槽、CPU、内存、时限、磁盘与许可证范围 | 本机只读 health 与能力发现；冻结计划摘要、输入 SHA-256、资源摘要、输出身份，核对 owner 及专属测试目录 |
| 操作集合、全任务最多实际启动次数 N、到期时刻、允许诊断与停止动作 | 由受信 Operator 建立任务委托，每候选绑定精确元组并由后端原子消费 Grant 和任务预算。N 由授权人填写；当前 N=0 |
| ODB 或 DAT 中的提取渠道 | 使用已核验版本的只读解析器，对新 Run 的产物摘要、步/帧/实例/节点和单位给出签明来源的标量；缺帧、陈旧或路径关联不明即停止 |
| 独立检查、失败与停止方式 | 事先冻结区间规则、数值质量与平衡检查、独立解析/参考载荷或实验依据；拟合数据与验证数据分开。仅凭位移在区间内无法证明物理有效性 |

建议实验顺序为只读资格检查 → 一个受控试点 → 仅在响应可用且预算有余时依照上一观测提出下一候选。每次保留 request key、Grant 消费、Receipt、Run、产物身份及独立比较。接受不明时只按原 key / namespace / owner 查询；无法对账时冻结新提交。已确认失败可按授权的诊断策略记录，新执行另计预算。取消先停止产生新候选；活动作业仅使用后端明确支持并获授权的 orderly stop / 管理动作。stop_service 的存在不能证明能够取消活动 Solver。缺少受支持的停止方式时保留 Run 并交给 Operator。

**下轮一次性授权请求**：请在选定真实模型后，在其所属机器的受信入口确认上表中的模型、观察定义、F 范围、资源、N、到期、判据与停止策略。未完成模型和后端资格前，可授权只读资格检查并继续把 N 设为 0。
