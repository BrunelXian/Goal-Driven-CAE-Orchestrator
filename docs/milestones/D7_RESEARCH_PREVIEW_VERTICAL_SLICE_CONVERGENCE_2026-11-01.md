# D7 Research Preview：当前代码核查与最小实现差异

日期：2026-11-01。范围为用户要求的第一步技术收敛与离线测试；不是实际 A/B 执行验收。

产品裁定采用路线 C：可信个人科研工作站、明确人工审批；不承诺阻止恶意同权限程序绕过授权。PowerShell 安装、双账户部署及新的通用安全基础设施均停止。已有强隔离实现及历史 BLOCKED/UNKNOWN 不删除、不改写。

## 1. 本轮基线与修改范围

- GD：`main@a75a614f9738af8f257fd490ceec2df4c012ea19`，开始时工作区干净。以实际代码为准，不退回旧 CP1。
- AF Develop：`Develop@7f4b8d8f3a2c862ed8b244d495295f5d51ea0d88`，已有 Standard/service/lifecycle 补丁及未跟踪 `rod_*` 实现；本轮不修改这些补丁，也不读取 Stable。
- 本轮新增 `tests/integration/test_d7_vertical_slice_readiness.py`、本报告及本轮脱敏证据 JSON。生产源码未修改，原拒绝门禁保留。
- 不运行旧安装脚本、不初始化 Operator、不启动 Owner/IPC、Solver/ODB，不创建真实 Grant，不提交或推送。

## 2. 实际正向能力与断点

| 接缝 | 当前实现与证据 | D7 状态 |
|---|---|---|
| A 合同、输入、预算预留 | `rod_real_project.py` 创建冻结 Project；`hold_a_for_review` 校验真实接口形状的 Plan/preflight 后，事务提交原始申请和一次预算 hold；支持重放与 revision 冲突 | 离线正向存在；不是人工授权 |
| A 原始来源读取 | AF `RodProduct.read_real_artifact(s)` → `rod_trusted.acquire`，读原 Receipt/Run/events/validation/launch intent；核对输入和 DAT/STA/MSG 原文件、采集摘要及完成文本 | 可复用；实际 Solver 证据尚无 |
| GD 独立数值检查 | `verify_owner_evidence`/`verify_owner_artifact_set` → GD 独立 `verify_dat`，不接受 AF 自报 PASS；检查载荷、位移、应力、反力、选择器、单位及平衡 | 字节数值正向存在；v1 固定返回来源未鉴定、V2 NOT_VERIFIED、V3 INCONCLUSIVE |
| A 接纳与预算结算 | `OBSERVE_A` 保存观察后无条件设 ACCEPTANCE_UNKNOWN；无 ACCEPT/CHARGE/RELEASE 正向动作；`real_a` 恒 NOT_READY，`_view` 恒返回未验证 | BLOCKED_CODE：不是缺一次真实运行即可解锁 |
| B 提案与输入 | `PROPOSE_B` 无条件拒绝 AUTHENTICATED_REAL_A_REQUIRED；`candidate_input()` 仅 A；`_candidate` 的 admitted_revision 固定 3 | BLOCKED_CODE：没有真实 B 准入/物化路径 |
| AF 动态 Standard Plan | `RodProduct.prepare_real` → `rod_trusted.prepare` → 原有 Store；精确 Plan/input/resources/runtime/output 身份，默认不执行 | A 的离线正向存在；prepare 和 check_plan 均只支持 phase A |
| AF 授权、派发、收尾 | `StandardOperator.request` → 现有 `product_standard_control` → `_issue`/submit/dispatch_once → 原 Supervisor/ExecutionService → StandardBackend/ManagedScope | 路由可复用；离线测试以 TEST_ONLY Grant/runner 替身验证，不是实际授权或求解 |
| 本机可信 Operator | 固定 Standard 已有当前用户 DPAPI 能力、独立 Operator token、精确 scope、一次性消费、Owner/revision/时窗及 PAUSED gate | 基础机制可复用；不能冒充已支持动态路线 C |
| 动态 Operator 激活 | `prepare_rod_a_only`、profile reopen、`rod_authority.qualified/require_decision` 均调用强隔离检查；固定 `product-protected-rod-a-only-v1`、双 SID、受保护代码/状态及 issuer 身份 | BLOCKED_CODE：需显式增加路线 C 产品模式，不能简单复用三字段旧 binding 或删除强隔离校验 |

重要边界：AF 默认 DAT 读取接口也会验证 STA/MSG；本轮损坏 STA/MSG 的负测证明其拒绝。GD v1 持久观察只保存 DAT 信封，新增 D7 接纳应采用已有完整三产物接口，并持久保留其独立检查依据，不能把“返回 DAT”误解为 AF 未查其他产物。

## 3. 最小生产实现差异（提出，尚未实施）

### A. 一条显式可信本机 Operator 产品模式

在现有 `product_standard.py`、`execution/product_standard.py` 和动态 authority/profile 分支内增加有版本的 `TRUSTED_LOCAL_RESEARCH_PREVIEW` 模式。保留受保护模式原语义；无模式/未知模式拒绝，不能由普通 RPC 参数临时切换。

复用当前用户本机能力存储和 `StandardOperator.request`。增加一个窄的人工 CLI/UI 入口：显示精确 scope，用户批准或终止拒绝，写原 management receipt；再由原 AF 公共 authorize 路径签发一次 Grant。Main 不读取 Operator 能力、不调用签发入口、不把聊天文字当 Grant。该角色约束是在可信工作站风险模型下的产品边界，不是抗同权限恶意程序隔离证明。

仍绑定 Project instance、Plan digest、模型输入、runtime/solver 配置、资源、输出、Owner、nonce、有效期和一次消费。拒绝、过期、错 Owner、错 digest、槽位冲突及 UNKNOWN 均不能靠换 key 绕过。服务端每次 authorize/dispatch/start 均校验同一模式和精确审批。

### B. 新版本 D7 来源资格与 A 接纳/预算事件

新建窄版本模块处理 D7 Project 事件，复用现有 ResearchProject SQLite、revision、审计和事务，不建第二编排器。`research/project.py` 只增加显式新版本 reducer 路由，保留 v1。

新 Project 冻结路线 C 风险模式、求解器/主机配置、模型与 Goal、验证器版本/摘要及至多两次预算。既有 `implementation_hashes()` 将当前文件摘要放入冻结合同，重开还会重建合同比较；本轮负测证明替换验证器摘要会令旧 Project 报 INTEGRITY_ERROR。因此不能原地改旧 reducer 后声称历史合同仍兼容，也不静默迁移历史库。

来源资格由绑定公共 AF reader、精确原始记录、独立原文件检查和明确人工执行审批建立，标记为可信本机下的来源资格；不能接受调用者传 `source_authentication=VERIFIED` 或自报 PASS。保留原始 envelope/三产物摘要、原始鉴定标签及资格适用范围，不把旧 NOT_VERIFIED 改写成历史 PASS。

预算结算必须与科学结论分离：确认 AF 已接受并消耗一次精确执行权后，幂等将 hold 转 charge；之后 Solver 失败或 DAT 数值不通过也不退款。Receipt/消费/启动关系不清楚时保持 hold、query-first，不自动重发；只有有界、确定的未接纳证明且符合冻结策略才可 release。不能继续依赖“仅成功 Run 才能读取”的 `acquire` 作为唯一预算证据，需复用公共 Receipt/Run/Grant 消费证据接缝。

独立验证后分别记录来源、模型不变量、Solver/数值合格性和目标状态。A 数值正确但目标未达是允许科研继续的事实；当前 Goal 把目标上下界映射到 V3，不能要求目标已经满足才允许 B，也不能把目标未达包装为 V3 PASS。必须保留每条硬约束的实际结果，另按冻结迭代规则允许对允许变量提案。V4/ODB 未要求时明确 NOT_ASSESSED/NOT_VERIFIED，不能宣称物理验证完成。

### C. A 证据驱动的 B 提案与准入，尚不授权执行

Main 仅在已接纳的真实 A 后生成结构化提案；冻结引用包括 GD Project/revision/contract、A Candidate、AF Project instance/Plan/Receipt/Run/attempt、完整产物摘要、接纳与独立验证记录摘要。不得预填所谓正确 B。

确定性准入检查引用未变、无未决 UNKNOWN、预算尚余、目标/模型不变、载荷 Decimal 有界（0.5–2.5 N）、仅 Node2 DOF1 CLOAD 可变，及独立审核结论。复用 `candidate_bytes` 和 AF `compile_candidate` 双侧精确字节检查；新 B 使用真实准入 revision、独立输入和输出身份。准入状态只到 PENDING_HUMAN_B_APPROVAL，无 Plan/Grant 执行权。

### D. B 使用同一 AF 管线，单独精确授权

在既有动态 Plan prepare/check 分支显式增加 phase B 的因果依据校验；不能只把 `phase == A` 改为 A/B 集合。维持每个 AF Project 一 Plan/Run 的现有范围：B 可使用新 AF 执行 Project，由同一 GD ResearchProject 绑定并统一两次预算，无需跨 Project 通用调度器。重复 B、旧 A 引用、预算耗尽、A 来源未定都拒绝。B 的 Plan/审批/Grant 只能在真实 A 验证及 B 准入之后生成，再单独取得用户授权。

## 4. 离线验证记录

使用登记的 `D:\XianLab\envs\LangChainEnv\Scripts\python.exe`，Python 3.12.10；pytest 已有，无依赖安装。Ruff 使用已有独立 `D:\ProgramData\anaconda3\Scripts\ruff.exe` 0.12.0，不切换项目 Python。

复用已有 `g3_d6_offline_checks.py` 和 P1 输出过滤边界，以新的 `d7-*` 标签记录；不扩展 Runtime 或测试控制器。新 pytest 临时 Project；原始测试日志保持私有，仅输出计数及允许的诊断字段。审计钩子拒绝子进程、网络连接和监听；这是防误触护栏，不是 OS 安全沙箱。

新增 11 个跨仓能力刻画用例：A hold→合成记录完成→公共读取→独立检查→持久观察；重放不结算；STA/MSG 损坏拒绝；自报路线 C/VERIFIED 拒绝；B 三种自报提案均拒绝；旧合同验证器漂移拒绝；AF B 和未部署动态授权拒绝。

首次新测试为 1 passed/10 failed；第二次为 9 passed/2 failed。修正的是新增测试：隔离公共 preflight 的只读 projection，避免沿用旧测试辅助类把真实 service backend 替换成读模型；使用外层 ProjectError；纠正“DAT 接口不查 STA/MSG”的错误预期。没有为让测试通过而改生产拒绝规则。

最终实际回归：GD 10 个文件 **220 passed / 0 failed / 0 skipped**，120.34 秒，包含新增 11 项；AF 8 个文件 **316 passed / 0 failed / 0 skipped**，174.73 秒。两次退出码均 0，原生进程/网络拒绝计数均 0。合计 **536 passed**，是定向无 Solver 回归，不宣称两仓所有测试全覆盖。新增测试 Ruff 通过；具体测试文件、源码身份及输出摘要见 `D7_VERTICAL_SLICE_OFFLINE_EVIDENCE_2026-11-01.json`。

## 5. 真实执行准入结论

**D7 当前真实 A/B 仍为 NO-GO。** 离线测试通过仅能说明所测记录链路与拒绝规则正确，不能说明上述 A–D 差异已经实现。

不再需要先安装 PowerShell 7 或创建两账户。剩余前置项是：路线 C Operator 产品入口及模式路由、新版本来源/预算/接纳语义、B 因果准入与 AF B 校验；随后冻结实际主机/解释器/Abaqus 版本和许可证、原 managed scope 环境、模型/Plan/资源/唯一输出路径，再申请一次精确 A 授权。当前 Codex 宿主历史 Job 限制仍不能忽略；求解器只由原 AF Owner 的受管执行路径启动，不在 Main 内另开启动通道。

实际 A 前只申请 A 的一次执行；A 输出产生并经独立核验后，才允许形成 B 的独立申请。任何真实来源、UNKNOWN 对账、预算或模型门槛未闭合时均停止。
