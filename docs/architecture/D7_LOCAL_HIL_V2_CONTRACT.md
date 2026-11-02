# D7-R1 — TRUSTED_LOCAL_HIL v2 合同

状态：有限离线实现；真实运行、输出格式及宿主资格分别验收。此版本不迁移旧项目，不提供恶意同权限隔离。

## 输出与版本

新模型族为 `axial_rod_cload_output_v2`，新增 `VERIFY={1,2}`。同一 `*NODE PRINT` 数据行请求 `U1,U2,U3,RF1,RF2,RF3`，GLOBAL=YES、NSET=VERIFY、FREQUENCY=1、SUMMARY=NO、TOTALS=NO。`*EL PRINT` 在 BAR 的 integration points 请求 S11。载荷仅 node 2/DOF 1 的 CLOAD 标量 0.5–2.5 N 可变；L=10 mm、A=1 mm²、E=1000 MPa、边界和单元保持原模型。

选择合并表的静态依据：每个 NODE PRINT 数据行定义一张表，全零节点行可能被省略；允许的非零载荷使 node 1 RF1 和 node 2 U1 分别非零。保留全部六分量检测，不把缺失位移填零。[SIMULIA NODE PRINT](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKEYRefMap/simakey-r-nodeprint.htm)、[DAT 格式说明](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEOUTRefMap/simaout-c-printfile.htm)、[EL PRINT](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKEYRefMap/simakey-r-elprint.htm)。本轮读到的是 2025 手册镜像，2024 在线页面返回 403；不能声称已观察 Abaqus 2024 的新合并表。

GD 和 AF 分别从原始合并表字节解析，保留原行号；不互相使用对方的数值 PASS。两节点的所有六分量、element 1/IP 1 的 S11、最终 step/increment、时间、完成正文/footer、有限数和容差都必须满足。原 v1 解析器和历史 DAT 不修改。新布局状态始终明确为 `REAL_OUTPUT_FORMAT_NOT_YET_OBSERVED`，离线正向样例是人工合成，不是 Solver 产物。

## 科研状态与重放

`rod-local-workflow-v2` 在既有 ResearchProject SQLite 事务/事件链上新增 reducer 路由。旧 `rod-real-workflow-v1` 和 Synthetic 路由不转换。新项目冻结信任等级、GD/AF/Plugin/Python 摘要、依赖版本、输出规则、数值策略、原目标及 2 次 Full 上限。ContractBundle 结构没有不兼容改写；新 policy 摘要进入模型约定，初始化事件保存完整 policy。

每次写入验证冻结 GD 代码闭包；AF prepare/check_plan/qualification 和 GD 固定读 adapter 核对 AF 源、Plugin 闭包、Python/必要运行材料及依赖版本。读取旧记录不产生新权限；运行版本变化拒绝新写入/执行。一次 A→B 必须使用同一冻结工作流，不能运行 A 后现场修改 B 逻辑。

## 两 Project 与一次性权限

一个 GD ResearchProject 对应两个全新串行 AF Project，各最多一个 Plan/Grant/Run。继续使用同一个 `abaqus-standard-rod-cload-v1` backend、原 ExecutionService、原 ProductStandardControl、原 Supervisor/managed process；不增加 launcher 或 scheduler。

新 local_contract 明确区分 TRUSTED_LOCAL_HIL 与原 protected 模式；不得提供假的 protected manifest/SID。新 Profile 不能缺省到旧模式。AF 同 Project 的单 Plan/Grant/Run、初始准备租约和 PAUSED gate 保持有效。

Main 只准备候选、精确申请和科研日志，通过普通已授权 AF submit 接缝提交既有 Grant；不取得 Operator token，不调用通用 authorize。人类独立启动窄终端入口 `abqjobpilot.rod_local_console`，仅支持精确 provision/review/dispatch。入口要求真实终端、显式 Project/Plan/digest/ResearchProject 路径，显示 scope、期限、nonce、预算、revision，再读确认后的状态。无自动 yes、无默认 Project、无 Owner 自动启动或自行重试。

Operator capability 在人类当前 Windows 用户的 Project-scoped DPAPI 文件中，由人类入口读取，不返回 Main、MCP 或日志。它是可信个人工作站的产品约束，不是 OS 对同用户恶意程序的隔离。原 protected/fixed 入口仍独立保留。

## 来源、数值与目标

`LocalReadPort` 固定使用原 AF 公共读取，不接受产品调用者任选的结果提供器。离线测试仅在测试域替换其读取/运行资格，不增加生产测试开关。

- accepted：原 Receipt、Run、REQUEST_ACCEPTED Event、Grant consumption 和精确真实 Grant 身份互相匹配；不依赖成功 DAT。
- started：原 STANDARD_CREATED Event 独立记录，不从 accepted 推断。
- V0：原 AF context/Plan/Run/Receipt、三产物稳定读取与收集记录、intent/Owner/scope 一致，判为有限 `LOCAL_RECORD_CHAIN_VERIFIED`。不是防篡改签名。
- V1：精确输入、单一合法载荷变更、单位/实体不变量。
- V2：GD 自己解析当前原始 DAT；AF validation 只用于交叉核对。
- V3：根据已核实 U1 判定目标 SATISFIED/NOT_MET；NOT_MET 不改写成 PASS，仍可在预算内继续。
- V4、ODB：NOT_ASSESSED / NOT_VERIFIED，无隐含执行。

B 只有在 A 已接纳、Goal NOT_MET、原 Owner 的 orderly stop marker 与原持久 stop Receipt 相符且受管 scope 已空时才可形成。B 引用 A 的 Run、产物摘要、数值、决定摘要、观察 revision 及停止回执摘要，使用实际 admission revision、新输入/输出/Candidate/AF Project 身份。另行人工批准，不能预制 Grant。

## 预算、未知与幂等

| 动作 | held / charged | 规则 |
|---|---|---|
| HOLD | +1 / 不变 | 原 preflight、同 Candidate 一次 |
| INTENT、接受结果 UNKNOWN | 保持占用 | 查询原 key，不换 key 重发 |
| AF accepted | held −1 / charged +1 | 原子接受记录；一次消费，不等于 started |
| STARTED | 不变 | 单独累计已观察启动次数 |
| 终态/失败/accepted 后未知 | 不退款 | 科研接纳与执行预算分开 |
| preintent 原人工 DENY | held −1 / 不变 | 必须无 Grant/Run/Receipt/consumption；intent 后不自动释放 |
| B | 同一 2 次总账 | 独立 AF Project 不扩容预算 |

同 key、同 action/data 重放返回现存结果；内容冲突拒绝。不同 key 不能再次预留同 attempt。事务提交前故障回滚，提交后故障保留结果，由同 key 对账。只读查询不到 Receipt 不等于未接受。

Datacheck 是另一次 Abaqus 调用，本路线禁止；ODB/noGUI 需要独立权限，本路线禁止。纯 DAT/STA/MSG 读取不计 Full、不产生执行权限。2 次预算是 accepted 授权消费上限，started 作为不同指标记录。

## 实机前门槛

代码离线通过不包含宿主/许可证/真实材料资格。仍须确认实际独立运行宿主、原 managed scope 支持、资源排他窗口、真实新 Project 与唯一输出路径、冻结候选运行闭包、人类独立批准。新输出可据静态依据提出首次实验申请；如果实际 DAT 格式不同，保持 UNKNOWN/拒绝，不临场弱化解析器或补造零值。

安装 Core 和现有 Plugin 不自动替换。本轮候选必须以其 manifest 精确摘要审阅；当前共享环境的旧安装 Core 不能冒充新版本。
