# M03-F1-R1-P1 — Privacy-Safe Evidence Boundary & Bounded Offline Replay

日期：2026-10-29。此报告是增补，不替换 M03-F1 PARTIAL、R1 BLOCKED_PRIVACY_OUTPUT 或 E1/E2B 历史记录。

## 范围与状态

本轮基线为 `main` / `538bfae9a3a5fcea97970b9effc4f1f168490650`，暂存区为空。沿用 Option 1A：Project-owned Runtime Sidecar；不迁移 research.sqlite3，不宣称跨库原子性。

实际运行结论：R1P1_PRIVACY_BOUNDARY_PASS、R1P1_OFFLINE_CONTRACT_PASS、R1P1_FULL_REGRESSION_PASS；最终独立收尾复核为限定 PASS。真实 CLI ACK 为 F1_REAL_CLI_ACK_NOT_TESTED，认证为 R1P1_AUTH_CAUSE_UNKNOWN。DESKTOP_ORIGINAL_MAIN_UNTOUCHED 表示本轮操作未触碰该线程，不是对其他客户端活动作保证；M03-F1 既有 PARTIAL 结论没有被改写。

本轮只新增测试输出边界、合成隐私测试和此报告。既有 R1 双 Decision 适配、暂停接口及 F1 Sidecar 实现保持原样。没有启动真实 App Server、创建线程、发送外部 Turn、启动 AF Owner、运行 Abaqus/ODB、执行真实 Candidate 或变更认证配置；没有安装依赖、暂存、提交或推送。

## 事件登记与证据访问契约

事件类别：根据用户接受的 R1 停止结论，历史 Markdown 原文读取曾将私有测试标识带入工具输出。此处仅采用 operator-provided status，没有重新读取、搜索或复制该原文及标识。

潜在输出面包括 stdout、stderr、traceback、diff/search 上下文、报告和 Reviewer 消息。当前 tracked/new artifact 是否包含原始标识：NOT_ESTABLISHED；公开传播和凭据泄露：均 NOT_ESTABLISHED。没有证据支持认证根因判断，也没有进行凭据轮换。相同的脱敏事件分类已写入本轮专用、限制 ACL 的临时目录，不包含任何原始标识。

| 访问类别 | 规则 |
|---|---|
| RAW_PRIVATE | 历史 E1/E2B 报告、旧会话、旧私有 manifest、原始日志和凭据；本轮不读取，不返回给 Main 或 Reviewer。 |
| SAFE_PROJECTION | 固定 schema、milestone、状态枚举、计数、退出码、耗时、基线 SHA、明确的 source_read_policy；失败定位仅允许当前测试源码的精确路径、函数名和数字行号。 |

SAFE_PROJECTION 是有范围的诊断输出，不是任意私有历史文件的通用脱敏器。没有拿历史私有数据试验过滤。SHA-256 仅用于绑定当前边界源码版本，不是防篡改安全证明；测试 hook 也不是针对恶意本机代码的安全沙箱。

## 输出边界实现

`tests/integration/m03f1_safe_replay.py` 使用独立 pytest hook 记录计数及获准源码位置，并与实际子进程退出码比对；不从 stdout 中的“PASS”字样判定成功。子进程 stdout/stderr 只进入有大小限制的内存缓冲，不返回原文、不显示尾部日志、不保存原始日志。启动命令还有外层固定字段投影，解析失败只返回 BLOCKED_PRIVACY_PROJECTION。

JSON 重复字段、NaN/Infinity、非 UTF-8、大小越界、缺字段和未知字段均拒绝。合成输入中的 opaque private 字段直接丢弃；不输出、截断或摘要化其值。失败诊断丢弃参数化名称、断言值和异常消息。后续 focused/full/Ruff/diff 必须先有当前 runner 与 privacy tests 源码摘要匹配的 gate PASS；任何边界修改都使旧 gate 失效。

独立审查发现的后台读取线程异常出口已修复：线程内部捕获异常，仅保留固定 drain_failed 标志，不让 threading.excepthook 输出消息或 traceback。read/kill/timeout 故障使用全新 fake process 注入；不会为测试清理而按进程名或 PID 扫描终止其他进程。

限制：超时、输出溢出或 drain 异常返回 cleanup_unknown 并阻断。对 retained child handle 的终止不等于证明 Windows 派生进程树全部退出。本轮不声称已经验证进程树强制回收；实际出现该状态必须停止后续回放。

## 实际运行记录

解释器：`D:/XianLab/envs/LangChainEnv/Scripts/python.exe`，Python 3.12.10、pytest 9.1.0、SQLite 3.49.1。Ruff：`D:/ProgramData/anaconda3/Scripts/ruff.exe`，0.12.0。使用已存在环境，无依赖安装。禁用 pytest 插件自动加载和 cacheprovider；三项 AF live opt-in 均未开启；所有 fixture 使用本轮新建隔离目录。

| 本轮运行 | 结果 | 说明 |
|---|---|---|
| gate-1 | FAIL：29 passed，0 failed，2 errors | 原始错误输出被抑制；获准定位指向解析负向测试。长 bytes 参数改为固定短用例标签后通过；没有查看原始 traceback，因此不将推测写为已确认根因。 |
| gate-2 | PASS：34 passed，0 failed/error/skipped；exit 0；1.05 s | 包含字段/schema/解析拒绝、stdout/stderr/异常抑制、fake drain read/kill/timeout、退出码核对、精确诊断白名单和 gate 摘要失效。 |
| focused-1 | PASS：269 passed，0 failed/error/skipped；exit 0；994.41 s | `tests/unit/test_main_runtime.py` + `tests/architecture`；运行器正常退出，输出投影成功。 |
| full-1 | PASS：845 passed，21 skipped，0 failed/error；exit 0；2098.30 s | 隐私门通过后，与 focused 使用不同隔离目录并行运行；运行器 exit 0。 |
| ruff-1 | PASS：exit 0；0.06 s | `ruff check --no-cache .`；输出经边界抑制。 |
| diff-1 | PASS：exit 0；0.06 s | `git diff --check`；原始输出不回显。 |
| diff-2 | PASS：exit 0；0.08 s | 最终收尾复查；新增文件另行检查空白/换行，因为它们尚未被 Git 跟踪。 |

gate-1 失败没有被 gate-2 覆盖。原始输出字节数只用于限制缓冲，并非隐私泄露数量。没有沿用历史 780 项回归数作为本轮证据。

21 项跳过全部来自本轮禁止启用的 live opt-in：M01-B AF read 1 项、M01-C MCP live 1 项、M03-B AF workflow 19 项（参数化展开）。当前测试源码的 skip 标记仅在这三个模块，未发现 xfail 标记；未把这些跳过算作真实集成 PASS。各次运行存在重叠，不相加作为独立覆盖数量。

命令使用固定允许列表：`python -B -m pytest` 加上述目标、`-q -p no:cacheprovider -p m03f1_safe_replay --basetemp <new isolated directory>`；完整回归不指定目标路径。父运行器抑制任意输出后才投影 hook 计数。gate/focused/full 均已返回实际正常完成状态；focused/full retained child wait 成功，管道读取线程完成，父启动会话退出码为 0。本轮外层回放没有 timeout、overflow、drain_failed 或 cleanup_unknown；未启动需要关闭的 Codex/AF 服务。此处不扩大为未经实测的异常派生进程树清理保证。本轮新临时材料按限制 ACL 保留，未清理历史材料。

新增三文件的限定扫描：线程链接/UUID/常见凭据模式命中 0、末尾空白 0、缺末尾换行 0、Markdown 表格列数错误 0。这是有限规则和明确范围的检查，不是全面 secret scanner，也不是历史仓库无敏感资料证明。

## R1 离线合同核查

实际源码保留 `bounded-ack-policy-r1` / `bounded-ack-runtime-r1` 与旧 v1 的分离。旧 A + STOP 不能被解释为两项科研 Decision。新 fixture 通过 `workflow_case` 的公开 create_workflow，再经 finish → until → advance → coordinator.advance 完成两个独立已提交 TEST_SYNTHETIC Decision。Runtime 仅在准备提交结束后接入只读 Project。

适配器复用内部已验证 Project snapshot 和 Workflow replay，校验 A/B 顺序、独立 transaction、source revision/digest、冻结合同及候选文件摘要。该内部 snapshot 依赖不是新增公共查询 API。Sidecar 保存队列、epoch、intent、ACK、暂停及审计事件；Project 只提供已提交来源。逻辑快照测试用于证明科研状态不变，不能扩大为跨库事务保证。

暂停语义：PAUSE_REQUESTED 是短 Sidecar 事务，不取得或接管 sender。暂停在 intent 前提交则禁止发送；intent 已提交时，该项属于当前未决工作，可继续获得 ACK，后续事件保持暂停。恢复要求 operator、command、revision/epoch 和来源校验，并取得 sender；恢复本身不调用 port、不清除 UNKNOWN。OWNER_BUSY 继续表达活跃发送者不能被接管。

本轮 focused/full 实测通过：合法双提交、跨进程重开及 E2、重复事件、并发 dispatcher、暂停线性化点、应答丢失、错误 ACK、来源漂移、初始化/intent/接受/terminal/ACK/暂停提交故障、旧 journal 阻断、只读状态不初始化、无数据库事务跨 port 边界。全部仅为 FakeCodexTurnPort 离线证据，没有真实外部 turn/start，也不是科学验证。

| 合同证据 | 当前源码用例（`tests/unit/test_main_runtime.py`） |
|---|---|
| 两笔真实合成提交、科研状态逻辑不变、重复事件 | `test_r1_two_public_committed_decisions_and_logical_read_only` |
| 暂停持久化、活跃发送者不接管、UNKNOWN 优先 | `test_r1_pause_linearization_and_no_owner_transfer`、`test_r1_pause_during_wait_other_process_and_unknown_precedence` |
| 跨独立进程恢复与竞争 | `test_r1_independent_process_history_and_status`、`test_r1_two_independent_dispatchers_have_one_effect` |
| 初始化及发送各阶段硬退出 | `test_r1_initialization_hard_exit_is_atomic`、`test_r1_hard_crash_and_fresh_process_no_duplicate` |
| 短事务和暂停提交故障 | `test_r1_all_port_boundaries_have_no_database_lock`、`test_r1_pause_commit_failure_preserves_owner_and_intent` |
| 来源缺失/漂移/错误绑定、旧 STOP 不冒充 B | `test_r1_read_adapter_rejects_broken_source_without_research_write`、`test_r1_source_advances_after_intent_before_dispatch`、`test_r1_pending_or_stop_source_cannot_gain_two_decision_policy` |
| 只读审计无隐式 bootstrap | `test_read_only_status_cannot_initialize`、`test_fresh_process_status_is_read_only` |

## 独立 Reviewer

原生独立 Reviewer 只读当前获准源码及任务书，未读取历史私有材料、运行服务或修改文件。其发现的 drain 线程异常出口已修复并加入合成测试；复查确认 gate readiness。继续核查已确认公开 fixture 提交链、Project 默认只读 snapshot、Sidecar status 的 mode=ro/query_only，以及暂停与 UNKNOWN 的分离。

最终独立意见为限定 PASS、无剩余阻断项：gate 34、focused 269、full 845 passed / 21 scoped skips 及 Ruff/diff 退出码与报告一致；正常 retained-child/pipe 收尾及 21 个预期路径/空 index 的表述未越界。Reviewer 没有独立重跑测试或读取私有原始结果，审查依据是获准源码、新报告和经过边界的固定字段执行证据。其要求继续保留认证 UNKNOWN、真实 ACK 未测试、原 F1 PARTIAL、异常 Windows 进程树回收未验证和历史材料敏感性 NOT_ESTABLISHED，均已保留。

## P1-01～P1-12 验收

| 编号 | 当前结果 | 证据/限定 |
|---|---|---|
| P1-01 | PASS | 本轮未读取/回显历史 E1/E2B 或私有 manifest；历史文件仅路径元数据。 |
| P1-02 | PASS | versioned strict allowlist；失败固定阻断，无 raw fallback。 |
| P1-03 | PASS | gate-2 的新合成隐私 fixtures；危险 marker 未写入 Git 产物或工具输出。 |
| P1-04 | PASS | 源码来自本轮获准非私有路径；执行结果仅固定计数/状态/定位；未复制、截断或转换原始 ID。 |
| P1-05 | PASS | 公共 API 提交双 Decision 的静态调用链及 focused-1 实测均通过。 |
| P1-06 | PASS | focused-1：持久化暂停、当前 intent 允许完成、发送者不接管、UNKNOWN 不因 resume 清除。 |
| P1-07 | PASS | focused-1：Project 逻辑快照不变，Sidecar 短事务；无跨库原子性主张。 |
| P1-08 | PASS | focused 269 passed；full 845 passed / 21 scoped live skips；无失败或错误。 |
| P1-09 | PASS | 限制 ACL 临时目录内的脱敏事件登记；此报告仅安全摘要。 |
| P1-10 | PASS（限定离线复核） | 原生独立 Reviewer 已完成源码、隐私修复、全部结构化运行结果和最终收尾审查；不依赖私有原文。 |
| P1-11 | PASS（限定收尾） | main/HEAD 不变，21 个预期路径，index 空；运行器正常完成。异常 Windows 进程树清理不在本轮已验证范围。 |
| P1-12 | PASS（边界） | F1_REAL_CLI_ACK_NOT_TESTED；R1P1_AUTH_CAUSE_UNKNOWN；没有接触 Desktop Main。 |

## 变更与保留

本轮新增：

- `tests/integration/m03f1_safe_replay.py`
- `tests/unit/test_main_runtime_privacy.py`
- `docs/milestones/M03-F1-R1-P1_PRIVACY_SAFE_REPLAY_REPORT.md`

本轮开始时实际为 4 tracked 修改、14 untracked 路径，较任务书的 13 个多一份已有 R1 报告；没有擅自清理差异。实际工作区核对为 4 tracked 修改、17 untracked，共 21 个预期路径，UnexpectedPaths=0、StagedPaths=0；main 与冻结 HEAD 均未改变。以下为完整清单；full-1 已正常完成，收尾限定见实际运行记录。

`Kickoff_Docs`、`CAE models`、`.codex/config.toml` 的忽略规则均仍生效；只核对忽略元数据，没有访问模型或本地配置内容。

继承并保留的 tracked 修改：

- `tests/architecture/test_af_read_boundary.py`
- `tests/architecture/test_forbidden_direct_writes.py`
- `tests/architecture/test_package_skeleton.py`
- `tests/architecture/test_research_boundary.py`

继承并保留的 untracked 路径（历史文档及 patch 只核对路径，不读取原文）：

- `docs/architecture/M03_F0_PERSISTENT_CODEX_MAIN_RUNTIME.md`
- `docs/architecture/M03_F1_BOUNDED_CODEX_MAIN_RUNTIME.md`
- `docs/milestones/M01-C_SOURCE_DIFF.patch`
- `docs/milestones/M03-E2A_DESKTOP_COMPATIBILITY_AUDIT.md`
- `docs/milestones/M03-E2B_DESKTOP_INTEROP_DELIVERY_REPORT.md`
- `docs/milestones/M03-F1-R1_OFFLINE_REMEDIATION_AND_AUTH_AUDIT.md`
- `docs/milestones/M03-F1_DELIVERY_REPORT.md`
- `src/aegiscae/research/main_runtime.py`
- `src/aegiscae/research/main_runtime_rules.py`
- `src/aegiscae/research/main_runtime_store.py`
- `tests/architecture/test_main_runtime_boundary.py`
- `tests/integration/m03f1_auth_probe.py`
- `tests/integration/m03f1_support.py`
- `tests/unit/test_main_runtime.py`

## 剩余限制与下一步

认证根因 UNKNOWN，R2 真实 ACK 尚未执行，Desktop 互操作及历史 BLOCKED 结论不变。只读 status 返回完整结构供内部调用；本轮 runner 提供受限输出边界，不代表所有将来的调用方自动具备隐私保护。未来新增诊断字段或 source 必须先扩展显式契约和合成测试。

下一步仍须单独批准 R2，先限定认证诊断与进程所有权，再考虑新建测试线程的 Seed + 两次 ACK；不得由本报告自动启动实验。本轮停止等待架构评审。
