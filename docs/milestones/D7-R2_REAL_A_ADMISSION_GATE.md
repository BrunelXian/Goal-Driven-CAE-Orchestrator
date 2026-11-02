# D7-R2 — Installed Runtime & Real-A Admission Qualification

2026-11-01。最终结论：**BLOCKED_D7_PLUGIN_ENTRY_AND_ISOLATED_OWNER_RUNTIME**。

冻结源码已经在新用户级 venv 实际安装，公开 GD/AF 无 Solver 准备链已运行；正式 Plugin 的 D7 入口与隔离 Owner 的解释器接缝仍不成立。不能提交 READY_FOR_REAL_A_APPROVAL_REVIEW。

| 必须区分的状态 | 本轮证据与结论 |
|---|---|
| INSTALL_CANDIDATE_QUALIFIED | **PASS，限隔离安装及依赖导入**。两包 RECORD、176 个源码文件、实际 import 路径与候选一致；不是正式缓存升级或执行宿主验收。 |
| CODEX_MAIN_PATH_QUALIFIED | **BLOCKED_D7_PLUGIN_ENTRY_MISSING**。本轮 Main 实际调用缓存 Plugin 的 Doctor/初始化函数；初始化仍是 `rod-real-workflow-v1`，不是 TRUSTED_LOCAL_HIL v2。没有新 Desktop @ 对话或角色身份验收。 |
| HIL_PATH_QUALIFIED | **PARTIAL，非执行性预览/拒绝通过**。真实 Plan 预览、非终端拒绝、明确替身 Operator 的 DENY 路径通过；真实人类终端→真实 Operator 的批准/拒绝持久链未观察，未初始化 Standard capability。 |
| AF_PRE_DISPATCH_QUALIFIED | **PASS，限原公共接口的持久 Plan/读取预检**。新隔离 AF Project：1 Plan，0 Run/Grant/Receipt/consumption，PAUSED。不能由此推断 Owner/dispatch 合格。 |
| REAL_SOLVER_NOT_RUN | **保持**；无 Abaqus/Datacheck/ODB/noGUI、Owner 或真实 Grant。 |
| REAL_OUTPUT_NOT_OBSERVED | **保持**；新版仍为 REAL_OUTPUT_FORMAT_NOT_YET_OBSERVED，未读取/重标历史 DAT。 |

## 精确候选与实际加载

GD main HEAD `a75a614f9738af8f257fd490ceec2df4c012ea19`；AF Develop HEAD `7f4b8d8f3a2c862ed8b244d495295f5d51ea0d88`。两仓 R1 覆盖层字节未改，未修改 Stable。

原 `dist/D7-R1_OFFLINE_SOURCE_CANDIDATE_20261101/D7-R1_SOURCE.zip`：528,665 bytes，SHA-256 `c9bb85faad74dd4fc20f1c66723c5b2bce8a56798605808c367e72c3fea8408b`。原 Manifest、ZIP CRC、176 payload 与 checkout/安装副本逐一核验；Plugin 11 文件还与实际缓存 `C:\Users\wuxia\.codex\plugins\cache\gdcae-preview\gdcae\0.1.0-alpha.5` 一致。

以下仅为本文路径缩写，不是环境变量：

`Q = C:\Users\wuxia\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\GDCAE-D7-R2-20261101-A01`

复用候选内已有 `candidate.py`，仅以已核验 ZIP 字节构建两个纯 Python Wheel，未运行构建 hooks。通过绝对 LangChainEnv Python 的 `pip --python Q\env\Scripts\python.exe install --no-index --no-deps --no-compile --no-cache-dir --disable-pip-version-check` 安装至原为空的新 venv；没有修改共享安装位置。

| 文件（位于 Q\wheels） | bytes | SHA-256 |
|---|---:|---|
| aegiscae-0.0.0+g3d6-py3-none-any.whl | 162071 | f9bdbf1b37ca08258456afdf23e6776bea036ad1b3f0d5ca6ae7faf768ed8244 |
| abqjobpilot_gdcae_internal-0.0.0+g3d6-py3-none-any.whl | 363634 | 5818137996a7360e75073c82ae6e14d26bb9c137bdb59be02d7df96887b01bcf |

版本号沿用冻结 builder 的 `0.0.0+g3d6`，**不可仅凭版本号区分旧 Core**。新 GD import 为 `Q\env\Lib\site-packages\aegiscae`，新 AF 为同目录 `abqjobpilot`；共享 LangChainEnv 仍加载旧 aegiscae，缺少 `rod_local_project`，也未安装 AF。R1 的 GD/AF/Plugin/Python 闭包摘要全部匹配。

独立 venv 不安装第三方依赖，只在其自身两个 `.pth` 中引用已存在的 LangChainEnv 包及已审阅 pywin32 bootstrap。实际导入 mcp 2.3.0、pydantic 2.13.4、win32api/pywintypes（pywin32 312）成功，Python 3.12.10。依赖仍是可变化的共享文件，不是完整逐字节环境封存；后续必须再次核对冻结版本/材料。没有修改 PATH、共享 `.pth`、账户或 ACL。

两个已定位的安装检查过程差异保留：逻辑 LOCALAPPDATA 路径受 Codex 包映射，初次 Doctor 的 resolved origin 与搜索路径字符串不同而拒绝；对同一安装改用上面的实际路径后 RECORD 通过，没有重装。最初只引用共享 site-packages 根时 pywin32/MCP 导入失败；补全**新 venv 内**既有 pywin32 所需路径/bootstrap 后实际导入通过，未安装或更改共享依赖。

## 本轮实际检查

Main 使用已安装 `gdcae:setup` Skill 规定的缓存 helper；先 Doctor，再在 `Q\plugin-v1-probe` 调用其真实 `initialize_real_research`。该调用通过安装来源校验并创建旧 v1 合同，证实入口缺失；未把它升级或当成 D7。另通过**已安装新 Core** API，在 `Q\research-qualification` 新建 v2 冻结合同和 A。这证明安装后的库调用，不冒充正式 Plugin 的 D7 初始化。

原公开 `RodProduct.create/prepare_real/preflight_real/a_only_application` 在 `Q\af-qualification` 完成持久准备。使用真实文件 identity、StandardConfig 和 LocalReadPort；没有 monkeypatch 运行资格、材料、Plan 或来源校验。必要 ENTRY/CMD/PYTHON、SMALauncher 和 ONEAPI vars 文件实际读取并冻结摘要，均未执行。

| 检查 | 实际结果 |
|---|---|
| 新合同、A 字节、输出规则与两次 Full 总预算 | 成功；A 1 N，输入 474 bytes |
| 原公共 AF Plan 准备、原记录预检、GD HOLD | 成功；held=1，charged=0，available=1，started=0 |
| 同参数 Plan 重放、同 key HOLD 重放 | 返回原结果，无第二个 Plan/占用 |
| 错误 admission revision | PLAN_STALE 拒绝 |
| 无 A 接纳时提出 B | A_NOT_ELIGIBLE 拒绝，科研状态不变 |
| 非终端 Main 调用人工入口 | HUMAN_TERMINAL_REQUIRED；未读取 Standard capability |
| 原 console + 当前 Plan，模拟 TTY/仅 DENY 的替身 Operator | 一次 review_a / DENY_TERMINAL，零 authorize；**没有真实人类确认或持久拒绝回执** |
| 跨独立 Python 进程重开 | 只读字节不变、原身份与 held 预算保留 |
| 离线 INTENT→UNKNOWN 注入、同 key 重放 | 占用不释放，未调用 submit；此测试 Project 永久保留为非执行故障样本 |
| 最终来源/安装复核 | GD 46、AF 119、Plugin 11 文件逐字节匹配，Doctor 两包 RECORD_VERIFIED |

16 个探针调用按预期返回，另有重开/提前 B 拒绝/UNKNOWN 注入检查；这是本轮实测，不是再次运行 R1 的 949 条测试。运行探针禁止子进程、网络连接/绑定及系统启动，记录 0 次被拒绝的外部调用尝试。唯一替身为明确标记的人类 DENY 测试，不用于运行来源或 AF 资格证明。

测试脚本曾将 RodProduct 对象误传给要求目录的 LocalReadPort，产生 TypeError。保留原脚本及已写回执；仅修正续检脚本，query-first 重开同一 Project/Plan 完成剩余检查，没有重跑安装或再次创建 Plan。生产源码未修改。

## HIL 与宿主：实测和未观察项

当前工具进程令牌未提升；有 Administrators 关联，但为 deny-only。仅记录 SID 摘要，不输出原 SID。新 Project 的基础生命周期 DPAPI 文件属于产品正常创建动作；未生成 `standard-operator.json`、`standard-profile.json` 或启动 intent。Main 的 RodProduct/LocalReadPort 没有通用 authorize 方法；人工窄入口绑定原 Plan scope、输入/输出/资源、候选、GD revision/预算、nonce 和最多 300 秒确认窗口。本轮没有观察未来人类终端的 SID/令牌；设计采用同一 Windows 用户的 DPAPI 可信域，实际终端仍需核对。不能据 TTY、DPAPI 或 API 分工宣称恶意同权限代码无法自授权。

只查询本进程/当前宿主，没有全机进程扫描、Job 创建、终止或抢占。`check_host` 返回 eligible=false：标准输出/错误为管道 `[3,3]`，隔离解释器也不等于 Plan 固定解释器。当前进程 in_any_job=true，外层层级 UNKNOWN；**Job 成员身份本身不是 Route C 的硬阻断**。原受管 scope 的实际创建、真实子进程退出与收尾、许可证、Owner/会话退出行为均为 NOT_YET_OBSERVED，不增加强隔离或外部 VM 前置条件。

确定的解释器冲突来自现有源码：`service_lifecycle.PYTHON=console_interpreter()` 是 `Q\env\Scripts\python.exe`；`standard_contract.PYTHON`、Config 和冻结依赖读取仍固定 `D:\XianLab\envs\LangChainEnv\Scripts\python.exe`。原 `ServiceLifecycleManager.start` 的 Standard extension 检查要求二者相等；当前组合必被拒绝。没有通过调用 start 验证，也不建议绕过管理器直接启动脚本。

## 输出静态核对与遗留测试分类

实际物化 INP 与 GD/AF v2 compiler 字节一致：`VERIFY={1,2}`、同一 NODE PRINT 行 `U1,U2,U3,RF1,RF2,RF3`、GLOBAL=YES；BAR 仅 element 1，EL PRINT 的 integration-points S11；保留实体、零值、平衡、单位及缺行拒绝。数据行分表与 NSET/ELSET/位置语义符合可读取的 [SIMULIA NODE PRINT 手册](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKEYRefMap/simakey-r-nodeprint.htm)及 [EL PRINT 手册](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKEYRefMap/simakey-r-elprint.htm)。2024 对应页面本轮仍返回 403；因此为静态合理性/冻结合同核对，不能称已由 Abaqus 2024 解析或验证真实排版。没有读取旧 DAT 或产生新结果。

| 遗留范围 | 影响分类与处理 |
|---|---|
| 23 未执行测试中的 14 项 hard-exit/crash | 恢复风险覆盖，不是已证实入口缺陷；本轮不引入原生进程家族实验。实际运行若 UNKNOWN 必须停止/保留占用；不声明已验证崩溃恢复。 |
| 3 项 junction/reparse | 路径拒绝覆盖；本轮检查所有实际路径无 reparse，未创建 junction/改 ACL；不构成新的系统权限前置。 |
| 3 项独立重开（Project/Mutation/Budget） | 本轮补充已安装 v2 的独立进程只读重开；不等同原 3 项全重跑。 |
| 2 项 side-effect 子进程哨兵、1 项多进程预算竞争 | 新安装探针有原生/网络禁用守卫；未重跑原子进程测试或并发竞争，不把未测记为失败/通过。 |
| MCP 异步子集 | 保留 BLOCKED_OFFLINE_NETWORK_BOUNDARY；本轮实际 MCP import 已通过。Proactor 自建 socket 被旧 guard 拦截不等于协议缺陷。当前 D7 初始化本身没有 MCP 写入口；不为了这项扩建执行 MCP。 |
| backend Ruff | 本轮再次检查仍为 33 项 E701/E702 风格诊断；未发现因此阻断 import/Plan/预览，不重排旧文件。两仓 git diff --check 通过。 |

真正必修的范围只有：添加正式 Plugin 的显式 D7 v2 初始化/冻结 runtime 入口；为 local v2 完成经过验证的隔离解释器绑定，保留 fixed/protected 原 pins；随后对完整新候选再冻结/安装验收。两项会改变 R1 文件摘要，故本轮不静默修补冻结候选。更改正式 Plugin 缓存将影响后续所有使用 alpha.5 的对话；当前没有批准或执行该替换。无需重开角色兼容性调查、扩展 Runtime 或安装控制器。

## 唯一 A-only 审批建议：暂不批准执行

已生成**唯一非执行性资格预览包** `Q\A_ONLY_NONEXECUTING_REVIEW_PACKET.json`，SHA-256 `7cf71dac028fb0178d3bfbc67f33fa9223527b9f6da98dc29430f3f765b1a263`。它绑定本轮真实创建的惰性 Plan，**不是可执行真实 A 申请**；测试状态后来注入 UNKNOWN，禁止使用该 Project 执行。

| 冻结/拟申请项 | 精确值或未满足状态 |
|---|---|
| 模型/输入 | axial_rod_cload_output_v2；1 N；474 bytes；SHA-256 f200e353851d453c856a991d86a60f989ce6920a76db7723bb95730934d51bb0 |
| 目标 | Node 2 U1，固定 [0.019,0.021] mm；不以解析预测代替真实结果 |
| 合同摘要 | 418d178ce7ca63583a6a9d89d87e81d86aa5655d9d8ca1019ce31970e2678af7 |
| 本轮资格 Plan | rod_real_57b0a7c5001c8accefdd9fcbeb4e24f0；摘要 22cd6e3979fdd8fccf08966e1bee32f4900f28d57c67a053781cce6c131dd938 |
| Project / 输出 | Q\af-qualification / rod_6dfc033a0c5147e9b457aed29174e93a；精确 Project/Candidate/输出身份均在预览 scope 内 |
| 资源 | slots=1、CPU=1、GPU=0、memory=2048 MB、observation=300 s、launch_budget=1 |
| 命令 | 预览包对应 `qualification.json.command_preview`，由原 backend 的纯 call_data 生成；固定 cmd /d /s /c、abq2024.bat、此 Plan job、input=axial_bar.inp、analysis interactive、cpus=1 gpus=0、2048 mb、精确 scratch；从未执行 |
| 单次 Grant | NOT_CREATED；须人类精确批准，最多一次；无 Datacheck/ODB/B 权限 |
| 总预算 | 两次 Full；本次 A 仅一份占用，accepted 才 charged；started 独立计数 |
| 预览时间窗 | 2026-11-01 11:29:36–11:34:36 UTC；不是未来执行窗，禁止延长/复用为审批 |
| 失败处置 | 任何未知先查询原 key，不换 key、不自动重试/退款/重新派发；保留原输入、日志、Receipt/Run/产物和 scope 状态 |

最短下一步是先修复上述两个产品接缝、重新冻结同一 A/B 实现，再在确定的宿主和**新** Project/output 下形成有效期内的精确 A-only 申请。届时人类才需审阅并确认单 Candidate 的 provision/review/dispatch（现入口为三次独立确认），Owner 启动另有原生命周期权限，不能计作已授权。实际点击/终端交互本轮为 0；本轮批准/拒绝模拟不计人工验收。B 必须等真实 A 接纳且 NOT_MET、正常收尾后另行申请，不能预制。

## 回执与停止状态

证据均保存在 Q：`candidate.json`（轮包/原候选身份）、`qualification.json`（16 探针及原 scope）、`reopen.safe.json`、`identity.safe.json`、`unknown.safe.json`。汇总 `closeout.safe.json` 的 SHA-256 为 `ee629e9d92d55417d55207d48c039a696992eee9774c0f0c6aa4c7b62903d822`，含各文件摘要及最终 Doctor。新测试产生的 host-bound 基础生命周期凭据保留在隔离 Project 中，不传播、不清理，不可用于真实任务。

仓库本轮仅新增本报告；其余新增安装、测试脚本、日志与惰性状态均在 Q，未覆盖 R1 或历史材料。没有更改共享 LangChainEnv、正式 Plugin 缓存、全局配置、账户/ACL，没有 Solver/Owner/真实 Grant/生产 Project 写入，没有 Git 提交或推送。以上为实际限定验收；停止等待架构评审，当前不请求真实 A 执行授权。
