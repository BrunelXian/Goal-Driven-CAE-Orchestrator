# D7-R0 — Contract & Execution Path Reconciliation

审计日期：2026-11-01。结论：**D7_R0_BLOCKED**（输出覆盖契约尚不能冻结；不是要求恢复双账户或安装基础设施）。

本轮只有只读源码/安装身份核查、纯内存解析探针及本报告写入。没有修改 GD/AF 源码，没有创建 ResearchProject、AF Project、Operator、Grant、Owner，没有运行 Solver、ODB、安装器、pytest 或 Git 提交。已有历史 BLOCKED/UNKNOWN 不变。本报告中的“建议”均未实施。

## 1. 当前源码、补丁与运行版本

| 对象 | 本轮实际观察 | 含义 |
|---|---|---|
| GD checkout | `D:\Projects\Goal-Driven-CAE-Orchestrator`，main，HEAD `a75a614f9738af8f257fd490ceec2df4c012ea19` | 不能继续以早期 CP1 SHA 代替当前源码 |
| GD 原工作区 | tracked clean；未跟踪的 D7 convergence MD、offline evidence JSON、`tests/integration/test_d7_vertical_slice_readiness.py` | 全部保留；本报告是唯一新增项 |
| AF checkout | `D:\Projects\abqjobpilot_dev`，Develop，HEAD `7f4b8d8f3a2c862ed8b244d495295f5d51ea0d88`，有本地补丁 | HEAD 本身不包含动态 D6 能力；不以远端 Develop 代表实际运行源 |
| 选用解释器 | `D:\XianLab\envs\LangChainEnv\Scripts\python.exe`，Python 3.12.10 | 遵循已读取的 `D:\XianLab\envs\ENVIRONMENTS.md`；探针使用绝对路径和 `-B` |
| 依赖 metadata | aegiscae `0.0.0+g3d6`；pytest 9.1.0；mcp 2.3.0；pydantic 2.13.4；pywin32 312；psutil 7.2.2 | 本轮没有安装或更改依赖；版本不等于完整运行资格 |
| Core 实际默认 import | `D:\XianLab\envs\LangChainEnv\Lib\site-packages\aegiscae\__init__.py` | 默认使用安装副本，不自动使用 GD checkout |
| AF 默认 import | LangChainEnv 的默认 `find_spec('abqjobpilot')` 为 None | 审计探针明确加入本地 Develop 源码；发行入口必须明确固定该来源 |
| Core 安装记录 | Name `aegiscae`，Version `0.0.0+g3d6`，Requires-Python `>=3.12,<4`，无 Requires-Dist；RECORD 59 个带 hash 条目全部匹配、无缺失 | RECORD 完整不代表已安装最新源码，也不保证外部依赖闭包 |
| Plugin | `0.1.0-alpha.5`；下述三个副本的 11 文件闭包相同 | 已知激活成功；精确角色身份仍为历史 `BLOCKED_PLATFORM_ROLE_ATTESTATION`，本轮不复验 |
| Solver 入口 | `D:\ABAQUS2024\Commands\abq2024.bat` 存在 | 未启动；实际许可、完整安装闭包、运行宿主资格仍 UNKNOWN |

当前 AF tracked 修改范围（仅源码/测试查询，不扫描历史私有材料）：

- `abqjobpilot/execution/`：closeout、interruption、lifecycle、product_standard、recovery、service、standard_backend、standard_contract、test_authority；另有 `abqjobpilot/product_standard.py`。
- 测试辅助：`tests/run003_process.py`、`tests/supervisor_helpers.py`。
- 未跟踪生产模块：`abqjobpilot/product_rod.py` 及 execution 下 rod_authority、rod_authorization、rod_dat、rod_evidence、rod_evidence_port、rod_lifecycle、rod_plan_adapter、rod_profile、rod_real_source、rod_review、rod_standard_adapter、rod_trusted。
- 未跟踪相关测试：g2_fake_rehearsal、test_d3_rod_real_source、test_d4_rod_trusted、test_d5_rod_preflight、test_d6_rod_authority、test_g2_fake_live、test_g2_rod_product、test_g3_fake_evidence_live、test_g3_rod_evidence_port、test_g3_rod_lifecycle、test_rod_plan_adapter、test_rod_preview。其存在不等于真实执行通过。

源码身份采用 sorted `{path,size,sha256}` 行的 canonical JSON（ASCII、sort_keys、紧凑 separators）SHA-256；只涵盖注明闭包，不声称代表全部脏工作区：

| 闭包 | 数量 | SHA-256 |
|---|---:|---|
| GD `src/aegiscae/**/*.py` | 41 | `c3274a4abe55c303dd54d83cdca917284a65e2e8d6ba90b3f5074b2d734f6c1e` |
| AF `abqjobpilot/**/*.py`，包含本地动态补丁 | 114 | `c5d0b8703cdebcbf000a33d036d813fb10496cdce5e5cba2a8a2a7c9ce09072a` |
| 安装 Core 的 Python 文件，排除 `_gdcae_plugin` | 43 | `c4833e61b57b6049be78c49cadf233e7cf48adc83802599cee60e46b8f43fb06` |
| Plugin 三副本的 11 文件闭包 | 11/副本 | `ff784538b2fc18adbf7f6fee865e1cceff76697a04afbf753fa311b5643be078` |
| 选用 python.exe | 1 | `0b471133e110cfb53a061cad528ce8e517d7b9ac41a0a396c39ad795a487fc14` |

Plugin 三副本为仓库 `plugins/gdcae`、`C:\Users\wuxia\.codex\plugins\cache\gdcae-preview\gdcae\0.1.0-alpha.5`、上述 site-packages 的 `aegiscae\_gdcae_plugin`。闭包包括 plugin.json、两个 scripts、两个 skills、handoff、runtime-contract、四个角色 TOML。没有据此推断角色已加载。

**同版本 Core 漂移**：安装副本额外含 `_gdcae_operator/audit.py`、`preview.py`（部署提案，非已启用审批入口）；两个关键文件与 checkout 不同：

| 文件 | checkout SHA-256 | installed SHA-256 |
|---|---|---|
| research/rod_real_project.py | `911d398825f025bc454304d14bbcfe5ec9e7d443936d63179952c6ef2b389b2b` | `5f318253a8458db312641302b7a938bf7b8f75fb39708b0e6c9f4662bcc7f51b` |
| research/rod_real_verify.py | `c56577e77fd1e22e474323c5b36a3f31738f0b3cc2026ab0f0de07c1d866a84b` | `4b1583a64c7eb888940e86196e21658527b689f171c0554506b5fa3201384b58` |

安装副本缺少 `verify_owner_artifact_set`。Plugin 的 `initialize_real_research`（scripts/gdcae.py:400）导入安装 Core，不能用 checkout 测试结果为它背书。`direct_url.json` 记录来源为 D6 `candidate-final-r2/gdcae/aegiscae-0.0.0+g3d6-py3-none-any.whl`，archive hash 为 `c3f772d2527743eee7554b5f46f51022115475876042bf24862bd18f762bcfd9`；这是安装来源记录，本轮未重新核验该旧 Wheel。

## 2. 四个核心接缝：实际 API 与缺口

以下行号对应本轮 checkout；GD 路径相对 GD 根，AF 路径相对 Develop 根。

### 接缝一：Candidate → Plan → 人工决策 → Grant

- GD `src/aegiscae/research/rod_real_project.py:101` `_candidate` 确定输入和身份，但 `admitted_revision=3` 固定；`candidate_input():228` 只返回 A。`hold_a_for_review():306` 核对精确 preflight/binding 并占预算，不签发 Grant。
- AF `abqjobpilot/product_rod.py:288` `RodProduct.prepare_real` 是动态真实 Plan 公共准备入口；:302 强制 phase A。:233 `preflight_real`、:267 `a_only_application` 只读输出精确申请；申请不等于批准。
- AF `abqjobpilot/product_standard.py:111` 附近 `prepare_rod_a_only` 当前要求 `rod_authority.protected_context`；受保护双身份模式仍是硬依赖。Route C 尚无实际 provisioning 正向实现。
- 同文件 :154 `review_rod_a_console` 只是 Python 函数适配器，接收 `choice` 并调用原 IPC；没有交互式人工确认 UI。:85 `StandardOperator` 读取当前用户 DPAPI 的 `standard-operator.json`，使用独立 operator token。普通 AF client 没有该 token，不等于同用户恶意程序无法读取它。
- `execution/product_standard.py` 的 `ProductStandardControl.invoke` 区分 review_a、authorize、dispatch_once；review 不签发 Grant，authorize 仍须精确服务端复核。`rod_authority.qualified/require_decision` 还要求保护清单和 Issuer 身份。

结论：不能把现有函数名中的 console 当成已交付的人类入口，也不能直接让 Main 调用 StandardOperator 获得通用签发能力。原固定 Profile 不应被 Route C 替换。

### 接缝二：Grant → accepted Receipt/Run → 唯一 Owner → 原受管执行

- `execution/service.py:206` `ExecutionService.submit`：namespace 由 Project instance、client namespace、submit 组成；同 key 同 request digest 返回原 Receipt，内容不同拒绝。在一次 accept 事务中写 Run、REQUEST_ACCEPTED Event、Receipt、Grant consumption。提交后应答丢失抛 ACCEPTANCE_UNKNOWN，并要求查询原 key。
- accepted 时 Run 已消耗单次 Grant，但仍可能 `PLANNED/PENDING/NOT_CALLED`。accepted 不是 started，更不是 completed。
- `execution/product_standard.py:125` authorize 要求 grants/runs 均为 0；:163 dispatch 要求 runs 恰为 1，精确绑定 Plan、Owner/revision、启动窗口。Standard retry_of 不支持，不能用 retry 作为 B。
- `execution/standard_backend.py` 原 `execute` 经原 managed scope 创建进程；命令是 Standard `analysis interactive cpus=1 gpus=0 memory="2048 mb"`。没有另一个可复用的“直接启动 Solver”许可。
- `service_lifecycle.start`、`service_owner.py`、原 Supervisor worker 是既有生命周期。Supervisor 类名含 Fake 不代表 Standard dispatch 使用 Fake backend；应看 config、backend_id、simulation 和实际派发实现。

现有离线测试覆盖这些接缝的模拟正向与拒绝；没有本轮真实 Grant、Owner 或 Solver 正向证据。实际受管宿主、资源无冲突、退出资格仍需独立运行前批准，不能用旧 build_04/B1/D2 UNKNOWN 补造。

### 接缝三：AF 原始来源 → 独立数值检查 → A 科研接纳

- AF `execution/rod_trusted.py:491` `acquire` 串联原 Receipt、Run、Event、Validation、launch/collect intent、输入及 DAT/STA/MSG；要求 completed、无 reconciliation、受管范围为空及 simulation false。即使单数 DAT API，也检查三产物。
- 公共读取为 `RodProduct.read_real_artifact` / `read_real_artifacts`。这是已存在的来源核对骨架，不是防同权限篡改证明，也不是失败 Run 的预算对账接口。
- GD `rod_real_verify.py:109` `verify_owner_evidence`、:212 `verify_owner_artifact_set` 核对身份、字节和来源记录；独立 `rod_preview_dat.verify_dat` 不信任 AF 自报 PASS。
- 当前验证器强制来源 `AF_OWNER_RECORD_CHAIN` 且 authentication `NOT_VERIFIED`；GD `OBSERVE_A`（rod_real_project.py:171）保存观察后仍为 ACCEPTANCE_UNKNOWN，不 charged、不 release、不接纳。`_view:216` 固定 V2 NOT_VERIFIED、V3 INCONCLUSIVE、HIL BLOCKED。
- GD 观察公共入口目前用单 DAT envelope，尚未将三产物核对、有限信任接纳、目标判定和结算组成一个可重放事务。

### 接缝四：已接纳 A → PROPOSE_B → 新身份/新预算/新授权

- GD `PROPOSE_B:181` 无条件拒绝 AUTHENTICATED_REAL_A_REQUIRED；没有实测 A 引用驱动的真实 B admission。不得删除 require(False) 作为修复。
- 新 B 必须引用 A 的接纳记录/原始产物摘要/数值指标/验证版本/目标状态，保持原冻结目标和模型不变量。Inverse 建议不是 PASS 或授权。
- B admission revision 必须取实际成功提交的 revision；不能复用 A 的固定 3。B 输入、candidate、output、AF context、Plan/Grant/Run、request key 均需新身份，且共享同一 GD 总预算。
- AF prepare/check_plan 当前均拒绝 phase B；人工申请、review 动作和 authority scope 也为 A-only。只改 phase 检查不足以形成合法 B。

## 3. 唯一首选 A/B 执行路径

**一个 GD ResearchProject，两个全新、串行、各一次的 AF execution Project。** A 彻底收尾且获得有限接纳后才允许生成 B；B 由人重新批准。不会预制 B Plan/Grant。

| 选择 | 代码事实与影响 | 裁定 |
|---|---|---|
| 同一 AF Project 后继 Plan | `store.acquire_initial_preparation_store:504` 要求 supervisor_started=0 且 runs=0；rod_trusted.prepare:170 要求 plans/runs/grants/receipts/consumption 全空；profile 绑定唯一 Plan；authorize/dispatch 单 Run 限制；重启 Owner 不恢复 initial preparation | 必须改变准备租约、profile、历史 Run/Grant 路由及生命周期，多处安全语义受影响；本轮不选 |
| 两个串行 AF Project | 保持每 Project 单 Plan/Grant/Run 与初始准备语义；增加明确的 B phase/因果 scope 及 GD 跨 Project 总账 | 唯一首选，改动最小；目前仍缺 B 公共正向契约 |

A 完成的必要证据包括原受管范围 EMPTY、Run 终态且 reconciliation NONE，以及原 Owner 正常 stop 的可查询回执。`service_lifecycle.require_idle/stop` 可复用其限定逻辑；不停止未知进程。A 的 Owner/作用域状态 UNKNOWN 时，不准备执行 B。单 Project slot 不等于全机互斥：使用精确人工排他执行窗口和受限资源冲突检查；不建设通用跨 Project scheduler，也不宣称已有全局资源锁。

## 4. 新建项目冻结的可信单机契约草案（未实施）

新 Project 冻结 `TRUSTED_LOCAL_HIL` 等级及版本、运行代码/依赖摘要、模型与输出契约、目标、V0–V3 规则、预算和每次精确人工授权。旧 Project/旧观察保留原状态，不追认。现有 reducer 用当前 implementation_hashes 重建 real_bundle；直接改变验证器会使旧记录重开失败。应新增版本化路线并保留旧版重放身份，不能静默替换规则或迁移合同。

### 人工批准与 capability

1. Main 只能形成不可执行申请和读取状态，不获得 operator token，也不在工具接口暴露通用 authorize。
2. 人单独启动精确本地审批入口；显示 research/AF context、Candidate/合同/revision、输入摘要、完整命令与环境、资源、输出位置、预算 reservation、有效期和一次性 nonce。APPROVE_EXACT 与 DENY_TERMINAL 分开持久化，默认拒绝。
3. 该人类入口持有 Project-scoped capability，经原 AF control 签发一次精确 Grant；Owner 再核对决定、Plan 和时效。人类同意 A 不延伸到 B、其他 Project 或其它参数。拒绝、过期或未知不得签发。
4. 当前强隔离 API 保留；Route C 需独立、显式模式，不能通过伪造 protected proof 或降级现有 qualified 检查实现。
5. capability 不进入 Main prompt、日志、MCP 或共享申请包。可信个人工作站依赖操作者与运行软件守约；同用户 DPAPI 不隔离同权限恶意 Main。普通 Main 的产品路由没有通用自授权入口，但不能宣称 OS 已阻止恶意同权限绕过。若需要此保证，应另用保留的强隔离路线。

### 证据与验证语义

| 层面 | 接纳要求 | 不允许的推论 |
|---|---|---|
| V0 来源/执行 | 原 AF context、Owner、Plan/Grant/Receipt/Run/attempt/Event、输入及三原始产物、受管完成与退出相符；scope/source/collect 完整 | 字符串 AF_REAL、退出码声明或一份 JSON 自报不能证明来源 |
| V1 模型 | 冻结 rod 输入与依赖精确一致；仅被授权载荷变化，单位/实体/材料/边界不变量通过 | 文件 hash 相同不证明物理模型正确 |
| V2 数值 | GD 独立读取实际 DAT 所需行；单位、有限 Decimal、最终 step/increment、残差/解析解容差等满足冻结规则 | 不能接受 AF PASS 代替复算，不能为缺行填零 |
| V3 目标 | 从已核验实际指标判定 SATISFIED / NOT_MET / INCONCLUSIVE，并保留硬约束覆盖 | A 有效但目标 NOT_MET 可在明确迭代 Policy 下申请 B；不得写成目标 PASS，也不能因目标未达标伪造数值失败 |
| 安全与物理范围 | 可信本地 record-chain 一致性，明确非抗恶意同权限篡改；V4/ODB 未执行 | SHA/时间戳不是不可篡改证明；杆解析解一致不等于一般物理验证 |

## 5. 预算与幂等：当前缺口和建议状态表

现有真实 reducer 只有 held/unknown 路径；底层 counters 可计算 available，但没有可信 accepted 结算动作。通用 BudgetLedger 的 synthetic oracle 不能作为真实消费证明。建议冻结：总上限 2 次 Full 授权消费，accepted 即 charged；另记实际 started 次数，避免把 accepted 称为真实 Solver 调用数。

| AF/GD 事件 | held | charged | available | 重放/后续策略 |
|---|---:|---:|---:|---|
| 初始 | 0 | 0 | 2 | 无执行授权 |
| A 精确预留 | 1 | 0 | 1 | 同 key/内容返回原快照 |
| 已写 submit intent，或接受结果 UNKNOWN | 1 | 0 | 1 | query-first 查原 namespace/key；不换 key 重提 |
| 原 Receipt + Run 证明 accepted | 0 | 1 | 1 | AF 同事务消费 Grant；只结算一次，尚不等于 started |
| started、运行中、失败、成功或 accepted 后完成状态 UNKNOWN | 0 | 1 | 1 | 不自动退回；完成 UNKNOWN 阻断 B |
| 明确拒绝且尚未有 intent/接受 | 0 | 0 | 2 | 可在原子终态中释放；超时/Receipt 暂缺不能充当拒绝证据 |
| 合格 A 后 B 预留 | 1 | 1 | 0 | 必须新候选与新人工决定 |
| B accepted | 0 | 2 | 0 | 一次结算，不允许第三次 Full |

AF 原 accepted 事务已经把 Receipt、Run、Event、consumption 一起提交；公共读取尚无独立 consumption 投影。限定可信本机可以明确依赖该已冻结实现的不变量，以原 Receipt/Run/Event 交叉核对；如要求单独消费证据，只增加受限只读 projection，不让 GD 直接改 AF 数据库。`rod_trusted.acquire` 仅处理成功产物，不能用于全部失败/未启动的预算 reconciliation，应复用原 Receipt/Run 查询并严格核对身份。

GD `_record` 同 key 同 action/data 在 stale revision 检查前返回原结果；内容变化拒绝 IDEMPOTENCY_CONFLICT。新接纳/结算应继承这一行为；不同 key 也不能绕过同 Candidate/attempt 唯一性。AF namespace 跨 Project 不同，所以两个 AF Project 必须仍受一个 GD 原子预算约束。应答丢失与实际消费不明均保持占用；不因 grant expiry、空查询或进程退出自动退款/重试。

| 操作类型 | 预算/授权分类 |
|---|---|
| Full Standard | 本路线唯一启用求解类别；每个 accepted attempt 消费 1；started 独立记录 |
| Datacheck | 也会启动 Abaqus；不是免费的预检。本 D7 未启用，若以后允许需独立精确授权及明确计费 |
| ODB / CAE-noGUI | 独立工具权限和资源预算；不能藏在 Full 后当免费额外调用。本路线不启用，状态 NOT_VERIFIED |
| 已有 DAT/STA/MSG 只读解析、提案、人工拒绝 | 不计 Solver 消费；不产生执行权限 |

## 6. 历史真实 DAT 的本轮只读兼容探针

限定读取 AF 保存的 `docs/agent_first/run_011/result_review_001/ORIGINAL_DAT.bin`：10,334 bytes，SHA-256 `23ac0cdd7714ef956f481fdf1ec97530cd0cf44a160ae286cd689400efc3f045`。历史 VALIDATION 中存在匹配 hash（只投影此事实，不输出原始私有记录）。前后文件摘要未变化。更早 manifest 指向的临时 DAT 当前不存在，不据此推测清理原因。

| 当前解析器 | 实际纯函数结果 |
|---|---|
| AF `standard_dat.parse` | DAT_COMPLETION_TEXT_OBSERVED；PRIMARY_THREE_PASS；ODB NOT_RUN |
| GD `rod_preview_dat.verify_dat` | ContractError：DAT_MISSING_ENTITY |
| AF 动态 `rod_dat.parse_bound_dat` | ExecutionError：DAT_MISSING_ENTITY |

最后一项仅在内存中构造 OFFLINE_AF_SUBSTITUTE binding 测试数值布局；exit=0/EMPTY 是探针输入假设，不是历史进程资格证据，不落库、不创建真实 Plan/Grant。

实际表行：element 1 S11（原文件第 203 行）；U 表只有 node 2（218 行，U1=0.01）；RF 表含 node 1（227 行，RF1=-1）和 node 2（228 行，RF1=0）。**缺的是 node 1 的 U 行，不是 node 2 的 RF 行。** 当前两个动态解析器都要求 U/RF 的 nodes {1,2}，并检查固定端 U 为零。因此旧三指标解析通过不能证明新完整数值契约通过；合成 complete_dat fixture 补齐行也不能解决真实输出兼容性。

必须先冻结解决方式：首选保留全部数值拒绝规则，审查一个能明确产出所有必需测量行的新输出契约/Profile；其实际输出覆盖目前 UNKNOWN。若拟改变验证覆盖，必须明确记录未观测项并单独审查新 VerificationContract，不能把边界条件当作已经测得的零或暗删检查。输出请求若改变输入，必须有新模型/Profile 身份及新项目，不能用原输入摘要冒充。解析器还固定标题、Abaqus 版本、日期格式及最终步布局，应对未来实际输出进行有界兼容验证，不扩大为任意 DAT 解析器。

历史字节只证明格式问题，绝不成为本次真实 A 的 V0/V2/V3 证据。

## 7. 最小实现差异与验收清单（本轮不实施）

| 最小差异 | 拟修改边界 | 保留的不变量 |
|---|---|---|
| 新可信本机合同/事件版本 | GD rod_real_project、rod_real_verify、Project 版本路由 | 新建冻结，旧合同/重放不追认；不新建编排器 |
| A accepted/unknown/terminal 对账及预算原子结算 | GD 真实 workflow，复用 AF 原只读查询 | intent-before-submit、query-first、同 key 幂等、一次消费 |
| 三原始产物来源接纳与目标结果 | GD observation/verification；必要的 AF 受限只读 projection | 原数据保留、数值独立复算、UNKNOWN 阻断 |
| 实际 A 驱动 B 的 proposal/admission | GD candidate 构造与合法 mutation、实际 revision、因果引用 | 不预制答案；旧 A 不覆盖；B 新输入/输出身份 |
| 两串行 Project 的 B scope | AF product_rod、rod_trusted、受限 review/authority scope | 每 Project 仍单 Plan/Grant/Run、唯一 Owner、原 backend |
| 人工本机精确批准入口 | AF 现有 product_standard/control 的显式新模式与窄交互入口 | Main 无通用签发工具；旧 protected/fixed 模式不降级 |
| 真实输出覆盖修复 | 待冻结 Profile/output/VerificationContract 后确定 | 不填零、不删除缺行拒绝、不冒充真实 V2 |
| 可复现运行闭包 | 新已审查 Core 候选和显式本地 AF 来源绑定 | 不以同版本或远端 HEAD 冒充本地补丁；本轮不安装 |

所需离线测试（允许使用明确标注的合成 bytes/stubs 验证逻辑，但结果不得升格为真实执行）：

1. 新 Project 的 Route C freeze/reopen；旧 Project 仍按旧版本重放，禁止旧观察追认；安装副本与待运行源码闭包匹配。
2. 精确 A prepare → human approve/deny → 单 Grant → 原 submit/dispatch 接缝；模型、命令、资源、输出、身份、expiry、nonce 任一变化均拒绝。测试中使用受控替身，不签发真实 Grant。
3. 原 accepted Receipt 对账正向、before/after-commit 故障、应答丢失、同 key 同内容/冲突、不同 key 重复候选、跨进程与跨 AF Project 预算竞争；accepted-not-started 不误退款。
4. 正确三产物链接纳；错误 Run/attempt/Owner、旧输出污染、收集前后篡改、缺 STA/MSG/DAT、退出/作用域不明、伪造 source label 均拒绝。源链有效和数值有效分别验收。
5. 保留历史 DAT 的已知拒绝回归；后续经批准的新输出契约另有正向 fixture 和实际格式资格，缺行/重复实体/错单位/NaN/Infinity/错误 step/容差边界均拒绝。不得把旧数据嵌入新 A acceptance。
6. A 有效且目标 NOT_MET 才可按冻结 Policy 生成有界 B；A 未接纳、目标不明确、预算不足、证据冲突均不生成可执行 B；Proposal 自报 PASS 无效。
7. B 实际 revision、独立 Candidate/输入/输出/AF Project 身份、原 A 证据摘要与新人工授权；A Owner 未收尾、任何 UNKNOWN、重复 Grant 或跨 Project token 均拒绝。A/B 共享两次上限。
8. Datacheck、ODB、额外 Solver 调用、直接 backend 启动和通用 authorize 路由均被产品入口拒绝。Main 不持有操作能力的接口审查与本机风险模型分别记录。

已有测试证据仅复用，不声称本轮重新执行：D7 安全回执记录 GD 220 passed、AF 316 passed，合计 536，0 failed/skip，属于限定集合而非全仓总回归。GD 包含 11 项新 characterization。AF 正向测试存在 StandardConfig/原生执行替身、TEST_ONLY 授权等隔离；这些不证明真实本机授权或 Solver 正向可运行。

回执摘要：`d7-gd-regression-01.safe.json` 为 `61b903b56980265f3ec1b4fe2bd260895a277ba89edb82df93b9fbd82e0a07d8`；`af-d7-regression-01.safe.json` 为 `bde0a0720937d4eacf1d2d6239f4220689ed277a2b212fa7100cd81000109898`。详细历史位置保留在现有 D7 evidence JSON；本报告不复制私有会话标识。

## 8. 门槛、UNKNOWN 与最终裁定

| 门槛 | 状态 | 精确剩余项 |
|---|---|---|
| 实际本地代码/安装身份区分 | PASS（只读识别） | 已明确安装 Core 漂移及本地 AF 补丁，不代表发行兼容 PASS |
| A/B 唯一最小路径选择 | PASS（设计推荐） | 两串行 AF Project；公共 B scope 尚待实现 |
| 数值/输出契约可冻结 | **BLOCKED** | 真实历史布局被两个动态解析器拒绝；完整 node 1 U 实际采集方式未资格化，不能继续假定合成布局代表真实输出 |
| 可信本机精确人工入口 | BLOCKED（待实现） | 当前只有 protected provisioning 与函数适配器；Route C 新模式、实际交互和 capability custody 未交付 |
| A 有限接纳与预算结算 | BLOCKED（待实现） | 当前只观察并保持 UNKNOWN，无 accepted settlement/目标判定事务 |
| B 新版本与合法授权 | BLOCKED（待实现） | 固定 revision、A-only 读入/申请/校验、PROPOSE_B 硬阻断 |
| 实际运行资格 | UNKNOWN / 未授权 | 唯一执行宿主、原 managed scope 支持、资源排他窗口、Solver/license、绝对输出路径与当前材料完整冻结未完成 |
| 抗同权限恶意绕过 | 不提供 | Route C 风险接受不能改写为强 OS 隔离保证 |
| 当前 A/B 实测、ODB、V4 | NOT_RUN / NOT_VERIFIED | 本轮未执行，无任何真实成功声明 |

**D7_R0_BLOCKED**：执行路线与最小差异已收敛，但严格数值覆盖与真实输出之间尚有一个未裁定的合同缺口，不能把它降格为普通字符串兼容修复。下一轮先审阅并冻结“如何实际取得全部必需测量行”的最小输出契约，再授权表中有限实现；可并行实现无争议的幂等/预算/精确人工入口部分，但必须另行获得实现授权。本轮到此停止。真实 A 授权仍须等新项目、模型/输出、运行闭包、资源、Plan 和人类审批范围全部精确冻结后单独申请；真实 B 必须等真实 A 合格后重新申请。
