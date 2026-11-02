# D7-R1 — Bounded Research Preview Implementation

日期：2026-11-01。结论：**D7_R1_OFFLINE_READY（限定范围）**。

独立审查结论为 **OFFLINE_REVIEW_PASS_LIMITED**。本结论仅准许进入实机准入评审，不是执行授权。没有运行 Abaqus、Datacheck、ODB/noGUI，没有签发真实 Grant、创建真实执行 Project/Owner、安装共享环境包、部署账户或提交/推送 Git。

| 维度 | 实际状态 |
|---|---|
| 新版本合同、来源/预算、人工入口、A→B 接缝 | OFFLINE_IMPLEMENTED |
| 本报告列明的受限测试集合 | OFFLINE_TESTED |
| 真实宿主、许可证、资源窗口和 managed scope | HOST_NOT_QUALIFIED |
| 本次 A、B 和真实输出 | REAL_NOT_RUN |
| 新版合并 DAT 表 | REAL_OUTPUT_FORMAT_NOT_YET_OBSERVED |
| MCP 异步测试子集 | BLOCKED_OFFLINE_NETWORK_BOUNDARY |
| D7 安装与 Desktop 产品激活 | 未执行；旧 Core/Plugin 不代表 D7 |

## 1. 新输出合同与旧版本保留

新增 `axial_rod_cload_output_v2`，新增 `VERIFY={1,2}` 节点集合；同一 NODE PRINT 数据行请求 U1/U2/U3/RF1/RF2/RF3，EL PRINT 在 element 1 integration point 1 请求 S11。材料、尺寸、边界、单元及单位不变，只允许 node 2、DOF 1 的 0.5–2.5 N CLOAD 标量改变。

旧请求中的 U 与 RF 分表、全零节点可能省略，不能满足“两节点必须都有 U1/RF1 原始值”的严格检查。新非零载荷下 node 1 的 RF1、node 2 的 U1 分别非零；合并表有静态手册依据。GD 和 AF 各自直接解析合并表，保留原始字节/行号；不填零、不改写历史 DAT、不互用数值 PASS。仍拒绝缺行、重复实体、错误集合、非有限值、错误载荷、非零受约束分量、不平衡和不完整 footer。

静态依据及精确版本规则见 [版本合同](../architecture/D7_LOCAL_HIL_V2_CONTRACT.md)。查得的是 SIMULIA 2025 手册镜像；2024 在线页不可读取。本轮没有观察新版真实 DAT，因此保留 `REAL_OUTPUT_FORMAT_NOT_YET_OBSERVED`。合成正向解析不构成真实输出验收。

旧 v1/Synthetic 路由及历史 DAT 不改变；新 policy 仅在新 ResearchProject 冻结。没有不兼容迁移已冻结合同，没有追认旧记录为 TRUSTED_LOCAL_HIL。

## 2. 实际实现与权限

复用 ResearchProject 事务/事件存储，新增 `rod-local-workflow-v2` reducer。冻结模型、输出、目标/验证规则、信任等级、GD/AF/Plugin/Python 源码与版本身份、必要运行材料、两次 Full 预算。每次新写入检查冻结 GD 闭包；AF 准备、资格及 GD 固定读取接缝复核 AF/Plugin/Python 和必要材料。

AF 仍经公共 RodProduct、原 ProductStandardControl、ExecutionService、Supervisor 和原 managed Standard backend。保持每 Project 单 Plan/Grant/Run。没有第二条 Solver 启动路径、通用调度器或新 Supervisor。

人工窄入口 `abqjobpilot.rod_local_console` 提供 provision/review/dispatch；必须为交互终端，显示并确认精确 Project、Plan、Candidate、输入/输出、资源、期限、nonce、GD revision/预算。确认后再读科研状态。provision/review 要求 HELD，dispatch 要求已由原 AF 接受。旧非交互 `review_rod_a_console(choice=...)` 拒绝新 local 模式，不能用旧入口绕过确认。

Main 只准备非执行性申请、持久 intent，并提交已经由人类批准的精确权限；不持有或获返 Operator capability，不自行调用通用签发接口。人类入口使用 Project-scoped DPAPI 能力存储。**同用户恶意程序仍可能访问或绕过此产品边界；这不是强 OS 隔离保证。** 原 protected/fixed 分支保持独立，不伪造其 protected proof。

未来获准后的顺序为：新 GD/AF A 准备与 HOLD → 人类 provision/受控 Owner 准入 → 人类 review（HELD）→ GD 记录 INTENT → 原 AF submit/accepted → 人类窄 dispatch → 独立读取 started/产物 → 接纳 A → 原 Owner orderly stop/空 scope → 形成实际 B → 全新 AF B Project 与新的逐项人工授权。该顺序本轮只在离线 fixtures 中测试，不创建真实运行对象。

## 3. 来源、数值、目标与预算

固定 `LocalReadPort` 仅接受原公共 RodProduct 和已资格化运行闭包，不接受任意 duck-typed 证据提供器。公共 AF 验证函数封装私有实现；GD 架构例外限精确模块/名称/方法，另有四项拒绝测试。

| 判定 | 必要材料与语义 |
|---|---|
| accepted | 原 Receipt、Run、REQUEST_ACCEPTED、Grant consumption、精确真实 Grant；不等 DAT 成功才收费 |
| started | 原 STANDARD_CREATED 独立计数，不从 accepted 推断 |
| V0 | context/Plan/Run/Receipt、原 DAT/STA/MSG 稳定收集记录、Owner/scope/intent 与输入身份；LOCAL_RECORD_CHAIN_VERIFIED，不是抗篡改签名 |
| V1 | 冻结输入、允许的唯一载荷变更、单位/实体/不变量 |
| V2 | GD 从原始 DAT 独立解析与数值检查；AF validation 为交叉核对 |
| V3 | 从已核实数值计算 SATISFIED 或 NOT_MET；不得将 NOT_MET 改写为成功 |
| V4/ODB | NOT_ASSESSED / NOT_VERIFIED |

| 状态/事件 | held | charged | available = 2 − held − charged |
|---|---:|---:|---:|
| 初始 | 0 | 0 | 2 |
| A HOLD/INTENT/接受结果 UNKNOWN | 1 | 0 | 1 |
| A accepted | 0 | 1 | 1 |
| A started、失败或 accepted 后 UNKNOWN | 0 | 1 | 1 |
| pre-intent 人工最终 DENY，且无 Grant/Run/Receipt/consumption | 0 | 0 | 2 |
| A 接纳且 NOT_MET、正常收尾后 B HOLD | 1 | 1 | 0 |
| B accepted | 0 | 2 | 0 |

UNKNOWN 保持占用，查询原 key，不能换 key 绕过 attempt；未查到 Receipt 不等于未接受。同 key 同 action/data 返回已有结果，不同内容拒绝。提交前故障回滚，提交后应答失败保留已提交记录以供重放。accepted 后不因数值拒绝退款。Datacheck、ODB/noGUI 不在两次 Full 权限内；纯产物读取不消耗 Full。

B 必须引用 A 的实际 Run、产物摘要、数值/决定、观察 revision 和原 orderly-stop 回执摘要。只有 A 已接纳、Goal NOT_MET、Owner 正常收尾且 scope 为空才形成 B；B 使用实际 admission revision、新 Candidate/输入/输出/AF Project。A/B 共享同一 GD 总账和同一冻结实现版本；没有为 B 预制真实 Plan/Grant。

## 4. 修改文件清单

下表是本轮改动范围，不把 AF 既有 D6 未提交补丁算作本轮新写。文件内容摘要见 [离线证据](D7-R1_OFFLINE_EVIDENCE.json)。

| 仓库 | 文件 | 本轮动作 |
|---|---|---|
| GD | src/aegiscae/research/project.py | 新 reducer 路由 |
| GD | src/aegiscae/research/rod_output_v2.py | 新增版本化模型/输出合同 |
| GD | src/aegiscae/research/rod_output_dat_v2.py | 新增严格原字节解析 |
| GD | src/aegiscae/research/rod_local_verify.py | 新增 local 来源与独立验证 |
| GD | src/aegiscae/research/rod_local_port.py | 新增固定公共只读接缝 |
| GD | src/aegiscae/research/rod_local_project.py | 新增新合同下的预算/状态/A→B |
| GD | tests/architecture/test_package_skeleton.py | 精确新模块登记 |
| GD | tests/architecture/test_forbidden_legacy_dependencies.py | 窄公共读取例外及四项负测 |
| GD | tests/integration/test_d7r1_local_preview.py | 新增 30 项离线用例 |
| GD | docs/architecture/D7_LOCAL_HIL_V2_CONTRACT.md | 新增版本合同决定 |
| GD | docs/milestones/D7-R1_DELIVERY_REPORT.md | 本报告 |
| GD | docs/milestones/D7-R1_OFFLINE_EVIDENCE.json | 新增脱敏回执及摘要 |
| AF | abqjobpilot/product_rod.py | 新合同 prepare 与原记录读取/public reader qualification |
| AF | abqjobpilot/product_standard.py | local 格式及旧入口跨模式拒绝 |
| AF | abqjobpilot/execution/rod_profile.py | 精确 v2 compiler 分支 |
| AF | abqjobpilot/execution/rod_trusted.py | local 合同/runtime 及 v2 收集策略 |
| AF | abqjobpilot/execution/product_standard.py | 互斥 local/protected 权限绑定 |
| AF | abqjobpilot/execution/standard_backend.py | 现有 backend 选择版本化验证策略 |
| AF | abqjobpilot/execution/rod_output_v2.py | 新增精确 v2 输入编译 |
| AF | abqjobpilot/execution/rod_output_dat_v2.py | 新增 AF 独立严格解析 |
| AF | abqjobpilot/execution/rod_local_hil.py | 新增 policy/材料/runtime/人工决定核对 |
| AF | abqjobpilot/execution/rod_local_read.py | 新增 accepted/started/denial/stop 原记录读取 |
| AF | abqjobpilot/rod_local_console.py | 新增人类交互窄入口 |

另在忽略的 dist 下生成两个候选交付文件，未安装、未暂存。先前 D7-R0/Convergence/证据及测试文件、D6 补丁和历史材料均保留。GD 当前有 3 个 tracked 修改；AF HEAD 的全量 diff 含先前补丁，不等于上述本轮差异。

## 5. 真实离线测试与限制

执行解释器：`D:\XianLab\envs\LangChainEnv\Scripts\python.exe`，3.12.10；pytest 9.1.0、mcp 2.3.0、pydantic 2.13.4、pywin32 312。未安装依赖。通过已有 `tests/integration/g3_d6_offline_checks.py` 受限包装器执行，禁止原生启动及网络；真实 issuer/native runner 在测试域另外阻断。原 AF TEST_ONLY fixtures 的受控准备写入、合成 DAT 和 monkeypatch 不构成真实 Grant/执行证明。

| 最终回执 label | 实际结果 | 秒 | 被拒绝的原生/网络调用尝试 |
|---|---|---:|---:|
| d7r1-source-final-03 | 250 passed，0 failed/skipped | 112.14 | 0 |
| d7r1-core-final-02 | 383 passed，23 deselected，0 failed/skipped | 70.62 | 0 |
| af-d7r1-source-final-03 | 316 passed，0 failed/skipped | 150.81 | 0 |

三个选定集合合计 **949 条通过记录**，不是全仓所有测试 PASS，也不以计数回执宣称已完成用例集合去重。精确 safe JSON 路径、摘要、计数见离线证据文件。

GD 集成组覆盖新 30 项及既有 rod/preflight/evidence 回归；core 组覆盖架构、ResearchProject、Mutation Guard、BudgetLedger；AF 组覆盖 rod preview/plan/lifecycle/evidence/real-source/trusted/preflight/authority。core 的进程/junction/hard-exit 等 23 项不在本轮安全运行范围，未执行。正向 A→B 使用两个隔离 AF TEST_ONLY fixture，并验证两次 charged；负测涵盖 identity、runtime、输入污染、缺证据、错误输出、非有限数、重复/冲突 key、revision、并发、提交前/后故障、未知保持占用、未收尾、人工拒绝及非终端审批拒绝。

保留失败记录：初期新测试的构造参数、字段/异常预期错误已修正；一次边开发边运行导致冻结源码摘要变化，运行守卫正确拒绝，之后固定版本重跑。较宽 `d7r1-core-01` 曾得到 383 passed / 61 failed / 24 deselected：5 项架构规则问题经精确修订修复；56 项 MCP SDK 异步用例在 Proactor 自建 socket 处被既有网络边界拒绝。没有放松边界，没有完成被禁止的网络/进程副作用。该异步子集保留 **BLOCKED_OFFLINE_NETWORK_BOUNDARY**，不以随后排除它的 core PASS 替代验收；既有七 MCP 工具源码未修改。

Ruff 0.12.0：本轮新/改文件（除下面所述旧 backend）默认规则通过；`standard_backend.py --select F` 通过。该旧文件完整默认规则仍有 33 项既有 E701/E702 单行风格问题，本轮未扩大重排，不能宣称全仓 Ruff PASS。两仓 tracked `git diff --check` 通过；新源码/文档另做尾随空白检查。Git 的 LF→CRLF 提示不属于 diff 错误。

## 6. 冻结来源与候选

| 项 | 身份 |
|---|---|
| GD main HEAD | a75a614f9738af8f257fd490ceec2df4c012ea19 |
| AF Develop HEAD | 7f4b8d8f3a2c862ed8b244d495295f5d51ea0d88 |
| GD Python 源码闭包 | ad78f75f363d192e264d82247af465ebdd21104119f5a78904bde18a0208d85d |
| AF Python 源码闭包 | d66f76cdb54efd4cc567c6e169cfedce3963171dffd36cf7036972f83a2b99f6 |
| Plugin 闭包 | a546000142266f2bb376d3461932f9c3accc728b374b61901b2a4081963947c2 |
| Python 程序摘要 | 0b471133e110cfb53a061cad528ce8e517d7b9ac41a0a396c39ad795a487fc14 |

源码闭包算法为排序 `(relative_path, "sha256:" + file_sha256)` 二元组，以紧凑 JSON 编码后 SHA-256；与旧 R0 inventory 算法不同，不直接横比摘要。manifest 保存每个文件大小、摘要、来源及 HEAD/未提交覆盖层。必要 ENTRY/CMD/PYTHON 材料与实际依赖版本必须再核对；这不是整个共享环境逐字节证明。

候选目录：`D:\Projects\Goal-Driven-CAE-Orchestrator\dist\D7-R1_OFFLINE_SOURCE_CANDIDATE_20261101`。

- `D7-R1_SOURCE.zip`：528,665 bytes；SHA-256 **c9bb85faad74dd4fc20f1c66723c5b2bce8a56798605808c367e72c3fea8408b**。
- `D7-R1_RUNTIME_CANDIDATE_MANIFEST.json`：外部审阅 manifest，含 ZIP 摘要和运行身份。
- ZIP 共 178 entries：176 白名单 payload（GD 46、AF 119、Plugin 11）加 CANDIDATE_MANIFEST.json/NOTICE.txt。内部 manifest 不包含自身 ZIP 摘要。
- 复用现有候选包构建组件，未增加安装控制器。逐文件与当前源字节匹配；无模型/DAT、数据库、凭据、历史报告或未知未跟踪文件。私有标识模式扫描零命中，不等于绝对隐私证明。
- **SOURCE_ONLY_NOT_INSTALL_WHEEL**。未替换已安装的 `aegiscae 0.0.0+g3d6`；Plugin `0.1.0-alpha.5` 默认初始化仍是旧 v1，不能宣称 D7 Desktop 激活或四自定义角色身份通过。

## 7. 独立 Reviewer

独立 Reviewer 对源码、最终三份 safe 回执及候选逐字节复核，结论 **OFFLINE_REVIEW_PASS_LIMITED**，未发现尚未解决的 P0/P1。审查提出并已修复：空运行材料、任意读取提供器、输出摘要不精确、审批窗口、否决释放状态、旧审批入口跨模式、Owner `-I -S` 下依赖元数据可见性。Reviewer 单独运行过纯只读隔离 Python 元数据探针，没有启动 Owner。

Reviewer 重算 ZIP、176 payload 和四项 runtime 摘要，均匹配；支持限定 D7_R1_OFFLINE_READY，同时要求保留 HOST_NOT_QUALIFIED、REAL_NOT_RUN、REAL_OUTPUT_FORMAT_NOT_YET_OBSERVED、MCP 异步子集阻断及 Ruff 遗留限制。没有将合成证据升级为真实求解或强权限隔离证明。

## 8. 实机前剩余门槛

1. 单独审阅并激活同一冻结 GD/AF/Plugin 运行闭包；当前源码候选不是可直接安装 Wheel，旧 Core 不能承担新入口。A/B 必须使用同一版本，不得 A 后临时修补 B 业务逻辑。
2. 独立确认执行主机、原 managed scope、许可证、准确 ENTRY/CMD/PYTHON、资源排他窗口和原 Owner 生命周期。历史 build_04/B1/D2 UNKNOWN/BLOCKED 不变，新离线测试不补造其证明。
3. 单独授权准备本次新 GD/AF A 的实际冻结输入、路径、Plan/Request 与人类独立 capability；然后以精确对象、有效期、一次性权限申请 A-only 执行。不得根据本报告自行 provision、签发、启动 Owner 或 Solver。
4. A 真正完成后取得实际 DAT/STA/MSG，独立 V0–V3 判定。格式不合约即保留拒绝/未知，不补零、不伪造验证。仅在真实 A 接纳且 NOT_MET、正常收尾后形成 B，另行精确批准 B。

以上为待批准或待真实观察条件，均未在本轮实施。交付后停止等待实机准入评审。
