# M03-F1 — Bounded Persistent Codex Main ACK Runtime delivery

日期：2026-10-29。整体状态：**PARTIAL**。真实阶段：**BLOCKED_TEST_AUTH**。
基线保持 `main@538bfae9a3a5fcea97970b9effc4f1f168490650`，未暂存、提交、推送或触发 CI。
本报告更新本轮早先的存储冲突停止报告；历史 F0/E2A/E2B 保持原样。

## 1. 裁定与交付范围

最初依任务书第0节停止：F0 独立 sidecar 与任务书“不得第二数据库”冲突。
用户明确裁定 **A：保留 F0 sidecar**，后续实现才开始。F1-05 因而按新裁定验收：
Runtime 内部原子事务，Project 只读提供来源，没有跨库事务和旧库迁移。

新增三个生产模块，完成固定两来源队列、历史快照、短事务、Windows 单发送者、
intent-before-send、UNKNOWN 阻断、正向对账与只读 status。无新增 Agent Harness、
调度服务、进程启动器或 MCP 工具。结构详见
[M03-F1 实现说明](../architecture/M03_F1_BOUNDED_CODEX_MAIN_RUNTIME.md)。

本轮来源为 A 科研 DECIDE 加独立事务的 STOP 控制记录，具有不同 source 身份、
递增序列和摘要，但只有**一份科研 DecisionRecord**。不冒充任务书的两份科学决策，
不执行 B，不改 Project schema 凑验收。因此 F1-03 明确 LIMITED。

| 必须单独报告的标签 | 结论 |
|---|---|
| M03F1_BOUNDED_ACK_RUNTIME_PASS | 未达到；整体 PARTIAL |
| F1_OFFLINE_QUEUE_CONTRACT_PASS | PASS（限定）：A+STOP 实际合同通过，不替代 F1-03 两科研Decision要求 |
| F1_REAL_OWNED_THREAD_TWO_EVENT_ACK_PASS | NOT_RUN / BLOCKED_TEST_AUTH |
| F1_DUPLICATE_UNKNOWN_BLOCK_PASS | PASS：Fake 与隔离进程范围，不外推真实 RPC |
| DESKTOP_ORIGINAL_MAIN_RESUMED | false / NOT_TESTED |
| PRODUCTION_UNATTENDED_RUNTIME_VERIFIED | false |
| AF_REAL_EXECUTION_VERIFIED | false |
| SCIENTIFIC_V2_V4_VERIFIED | false |

## 2. G0、当前接口与认证门槛

已阅读任务书、完整 F0、E1/E2A/E2B、ADR-003/004、Project/Workflow/Continuation
及安全守卫；使用全局环境登记中的既有 LangChainEnv。Python 3.12.10、pytest 9.1.0、
SQLite 3.49.1；Ruff 0.12.0。无依赖安装或环境修改。

当前实际 CLI/App Server：`0.165.0-alpha.1.2`，核验安装可执行文件、help 并离线生成
schema。检查 thread/start、resume、read、turn/start、完成通知及 Goal 查询。
接口存在不证明业务幂等、无工具权限或 Desktop 同步。

原生 Goals 可能与 Runtime 形成双重续回合控制。官方依据与本地 schema 限制见
架构说明第7节。F1 要求显式 native_goal=null、自动来源禁用及前 owner 已退出。
缺字段/活动 Goal 在 Fake 中拒绝。真实配置、Goal 空状态、无工具策略及 orphan-owner
退出均未证明；不调用任何既有线程 Goal 写接口。

仅一次隔离认证探针：新私有测试根、独立 CODEX_HOME/CODEX_SQLITE_HOME、空 cwd、
环境白名单，无凭据复制。只调用 `codex login status`，30秒上限，stdin禁用，
捕获后丢弃 stdout/stderr 原文，仅保存结构化结果：

| 观察 | 实际值 |
|---|---|
| 子进程退出 | exit1；直接子进程已等待回收，非 timeout |
| stdout / stderr | 0 / 318 bytes；原文未保存或输出 |
| 认证 | 未确认；BLOCKED_TEST_AUTH |
| thread / seed / turn / App Server | 0 / 0 / 0 / 0 |
| 凭据复制 / 全局配置修改 | false / false |

只读复核本轮私有根、empty-work及isolated HOME：均非reparse point；ACL只有当前
用户与SYSTEM两项。根禁用继承，子目录继承该受限ACL。未读取HOME中的认证文件。

原始错误未留存，**不能确认具体失败原因**，不能断言一定未登录或已解决。
保留 USERPROFILE/APPDATA 等基础环境意味着未证明 CLI 从不查询 OS 凭据存储；
这里只声明没有复制、打印或持久化认证输出。没有回退共享 HOME、自动登录或再试。
正常退出不构成任意后代进程治理证明；本轮没有 App Server 服务需收尾。

## 3. 持久化、幂等与限制

固定 `main-runtime-v1.sqlite3` / `main-runtime-v1.owner`，无旧库迁移。
INITIALIZED 原子保存两来源、policy、seed、source revision、operator与文件身份。
严格单表/字段、摘要链、事务 ID、UTC/序列，64项/单条64KiB/库4MiB上限。
历史快照是观察证据；摘要和时间不是不可篡改证明。

`QUEUED → TURN_START_INTENT → TURN_STARTED → ACK_COMPLETED`；不确定转 UNKNOWN。
第二事件在前驱正向 ACK 前 WAITING_PREDECESSOR。每事件最多一次有意 start；
intent、远端响应、终态、历史匹配和语义 ACK 分别处理。
新进程不重发旧 intent/started；相同事件重放没有额外 port 调用。

全部 port 方法在 Project/Runtime SQLite 事务关闭后执行，保留独立 sender mutex。
未知不能释放配额、退款或换线程。reconcile 只读取 port，只有 exact seed/历史前缀、
唯一 Turn、输入摘要、completed、零工具及 exact ACK 才提交本地正向对账。
Project revision 前进后可读旧 receipt/对账，但禁止新 dispatch；初始化旧来源不能
伪装当前 revision。status 无初始化、修复或业务写。

暂停/恢复采用 operator+command ID+revision CAS。发送期间暂停返回 OWNER_BUSY，
未实现 F0 的即时持久暂停意图。mutex 只约束合作本地进程，不是远端 fencing；
epoch 是每次 intent 单调序号，不是持久进程 lease generation 或接管证明。
owner 退出字段来自 port，真实进程证明仍缺。没有可投入使用的真实 F1 adapter、
bootstrap/seed 防重复流程或进程恢复实现，不宣称长期运行服务可用。

## 4. 实际测试记录

解释器始终绝对调用 `D:\XianLab\envs\LangChainEnv\Scripts\python.exe`。
进程级 `PYTHONDONTWRITEBYTECODE=1`、`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`、源码
PYTHONPATH；`GDCAE_M01B_LIVE`、`GDCAE_M01C_LIVE`、`GDCAE_M03B_LIVE` 均置空。
各 basetemp 使用本轮私有根下不同新目录；只用合成文件。

```powershell
& 'D:\XianLab\envs\LangChainEnv\Scripts\python.exe' -B -m pytest -q -p no:cacheprovider --basetemp '<private-test-root>\full-final'
& 'D:\ProgramData\anaconda3\Scripts\ruff.exe' check --no-cache .
git diff --check
git diff --cached --check
```

| 执行 | 实际结果 |
|---|---|
| 改动前 architecture + test_continuation | 221 passed，194.06s，exit0 |
| 新单元测试首轮开发运行 | 49 passed / 1 failed，204.85s，exit1；测试引用不存在的 helper，后以真实冻结版本推进测试替代 |
| 中间 architecture | 169 passed，4.57s，exit0 |
| focused2：test_main_runtime + architecture | 225 passed，281.94s，exit0；后补用例以完整回归为准 |
| 最终完整无 Solver 回归 | **780 passed, 21 skipped in 1129.82s (0:18:49)**，exit0 |
| Ruff | All checks passed!，exit0 |
| tracked/index diff --check | exit0；无空白错误，仅 Git LF/CRLF 提示 |
| 新文件no-index / 保全审查 | 9文件无空白错误；120基线中仅4个允许的守卫变化；详见第7节 |

日志保存在本轮私有根，不入Git；不公开实际根、线程标识或认证内容。
历史 E1 的703/21不作为本轮结果。AF live skips 是禁止启动 Owner 的明确门控，
不是 Mock 替代 AF 真验收；F1 真实 ACK 阻断单独报告，没有隐藏为 pytest skip。
21项具体为 AF read live 1项、AF workflow live 19项、MCP read live 1项。
本轮11个实现/测试文件在最终全回归启动后没有修改，结果覆盖最终代码；之后只改报告。

测试覆盖：独立 Python 进程 status/E2 恢复；两个独立 coordinator 只有一个 start
副作用标记；每个 port 方法期间可取得独立 DB 写事务；重复/变造/身份/历史冲突；
UNKNOWN、容量、退出和终态丢失；KeyboardInterrupt、os._exit(23)、初始化/intent/ACK
提交前后；旧 journal/WAL/SHM保留；冻结新版合同后新dispatch stale、旧receipt可读；
输入/候选篡改、重算摘要后元数据语义矛盾、时钟回退、额外schema、替换/硬链接和锁污染。

## 5. 任务书 F1-01～F1-20 与 F0 对照

左列来自本轮任务书；F0编号指设计第11节，同号含义不同。下表 OFFLINE 指
已通过的 Fake/隔离进程验收范围，最终测试结果见第4节，不推导真实 RPC PASS。

| ID | 实际要求与证据 | F0关联 | 结论 |
|---|---|---|---|
| F1-01 | 完整设计/代码对齐；冲突先停获A裁定 | 全部，特别03/04/12 | LIMITED：差距逐项披露 |
| F1-02 | 无Harness/DAG/daemon/AF owner | 20 | PASS：源码/守卫 |
| F1-03 | A DECIDE+独立STOP；仅1科研Decision | 04/05/11 | LIMITED：非两份科研Decision |
| F1-04 | 固定Project/Workflow/thread、seed、两事件policy | 02/17/18 | OFFLINE；真实绑定未建 |
| F1-05 | 按用户A在sidecar原子持久，Project只读 | 03/04 | OFFLINE；非跨库事务 |
| F1-06 | durable intent/epoch先于start，port无DB长锁 | 06/12 | OFFLINE |
| F1-07 | E1正向ACK才放E2，无steer/queue | 09/10/16/18 | OFFLINE |
| F1-08 | 完整重复无额外调用，变造冲突 | 04/06/18 | OFFLINE |
| F1-09 | foreign/变造/stale/输入及合同推进拒绝 | 04/10/11/12 | OFFLINE |
| F1-10 | 线程/两个独立进程竞争，loser无start | 07/08 | OFFLINE；远端排他未证 |
| F1-11 | 丢回应/容量/退出挡E2，无重试 | 09/10 | OFFLINE |
| F1-12 | 唯一历史对账；缺失/模糊阻断 | 10/16 | OFFLINE；真实分页未验 |
| F1-13 | 新进程status/E2，科研与旧E1字节不变 | 03/11/14/19 | OFFLINE |
| F1-14 | 初始化/intent/RPC接受/terminal/ACK故障 | 04/06/09/10 | OFFLINE；无真实server崩溃 |
| F1-15 | 旧journal/WAL/SHM拒绝保留，无修复退款 | 15/17 | OFFLINE |
| F1-16 | 真实同线程seed+2及独立读回3Turn | 18/19 | NOT_RUN / BLOCKED_TEST_AUTH |
| F1-17 | 本地版本/schema/Goals负向；真实owner未证 | 01/07/08 | STATIC_ONLY；真实门未过 |
| F1-18 | 核心无科研写、Fake零工具；真实ACK未发生 | 16/17/20 | OFFLINE；真实NOT_RUN |
| F1-19 | 原7+2工具未改，780/21回归、Ruff/diff | 20 | PASS（适用无Solver范围） |
| F1-20 | 独立源码/文档复核，测试由主Agent实测 | 20及第12节 | 限定复核通过；真实阶段仍未验 |

F0 全部条件补充：

| F0 ID | 当前对应与缺口 |
|---|---|
| 01 | 当前版本/schema+安全停止；真实有效权限/auth未证 |
| 02 | Fake固定seed/thread；真实bootstrap/seed intent与丢回应生命周期未实现 |
| 03 | sidecar与只读Project/E1 byte检查；旧D代码未改，未新增D库专门运行样本 |
| 04 | 两来源同INITIALIZED事务+重放；无动态inbox/cursor扫描器 |
| 05 | 相邻两来源和上限拒绝；无乱序缓冲或持续背压 |
| 06 | intent-before-start与故障注入 |
| 07 | 两独立进程mutex竞争，无TTL接管；PID复用/实际server handle未验 |
| 08 | Fake previous_owner_exited门；孤儿App Server处置未实现/验证 |
| 09 | 丢回应及新进程旧intent不重发 |
| 10 | 唯一history正向；真实分页/游标边界仍缺 |
| 11 | 合同revision推进后旧status/reconcile保留 |
| 12 | port方法无DB长锁；ACK无科学准入权 |
| 13 | LIMITED：在途pause为OWNER_BUSY，无即时持久暂停请求 |
| 14 | 空闲operator/CAS/command幂等；无真实认证UI/interrupt/drain |
| 15 | journal/损坏/时钟/中断测试；未做真实磁盘耗尽 |
| 16 | 精确ACK/零工具/科学分离；无效输出UNKNOWN，未细分全部失败disposition |
| 17 | 固定两intent、UNKNOWN不释放；科研预算不变；无token费用硬限 |
| 18 | 真实seed+2未运行 |
| 19 | Fake跨进程恢复范围；真实客户端重连/退出未运行 |
| 20 | 窄模块/四个精确守卫例外；全回归与审阅见下 |

## 6. Reviewer 与风险

独立 Reviewer `/root/m03f0_review` 只读检查，没有修改文件或执行测试/服务。
初审两项离线阻断已修：

1. E1的一次授权可能被两事件使用：新增独立F1 policy，明确两次配额与A+STOP，
   旧E1 policy拒绝测试覆盖。
2. 旧来源可能借当前revision显得fresh：初始化revision必须等于STOP来源revision，
   用真实冻结新版合同负向验证；历史读与新发送分离。

复核未发现新的离线核心阻断，确认无SQLite跨port长事务或隐式迁移。
要求保留STOP语义、pause BUSY、真实认证/owner/Goals未验限定。认证helper的静态
窄范围获得认可；任何exit0亦不能单独放行真实smoke。文档复核要求在首次seed之前
也证明Goal为空，并澄清epoch仅为intent序号，已纳入。最终限定文档复核通过，无新增
文档阻断；Reviewer确认保全陈述未扩大为绝对安全证明。其未独立读取私有日志或
重跑测试，最终测试数和Git状态归属于主Agent实际工具测量。

| 剩余风险 | 处置 |
|---|---|
| 两事件不是两科研Decision | LIMITED，待评审控制事件语义或另批最小来源模型 |
| 隔离auth、有效no-tool、Goals/自动源未证 | 真实BLOCKED，不回退共享HOME或启动线程 |
| 无真实adapter/bootstrap/子进程恢复 | 不可部署；旧E1不替代本轮证明 |
| 本地mutex不约束外部writer；在途pause BUSY | 不宣称跨客户端安全或F0完整控制接口 |
| 本地提交/远端不原子 | 单尝试、UNKNOWN、人工审阅，无自动retry |
| ACL、SHA、UTC的信任限制 | 一致性边界；非签名/敌对同用户隔离 |
| 私有测试DB、故障journal、schema和日志留存 | 本轮受限目录保留，不入Git；不清理历史材料/凭据 |

## 7. 文件、保全与收尾

本轮新增9文件：

- `src/aegiscae/research/main_runtime.py`
- `src/aegiscae/research/main_runtime_rules.py`
- `src/aegiscae/research/main_runtime_store.py`
- `tests/architecture/test_main_runtime_boundary.py`
- `tests/unit/test_main_runtime.py`
- `tests/integration/m03f1_support.py`
- `tests/integration/m03f1_auth_probe.py`
- `docs/architecture/M03_F1_BOUNDED_CODEX_MAIN_RUNTIME.md`
- `docs/milestones/M03-F1_DELIVERY_REPORT.md`（更新本轮早先停止报告）

修改4个既有架构测试，仅增加固定Runtime路径/schema/创建例外与包文件清单：
`test_af_read_boundary.py`、`test_forbidden_direct_writes.py`、
`test_package_skeleton.py`、`test_research_boundary.py`。
新增守卫验证例外不适用于任意SQL/其他路径/生产调用；既有生产源码未改。

起始4个未跟踪资料：F0、E2A、E2B及M01-C旧审阅补丁，均保留。
旧补丁只核metadata、不读内容；README、.gitignore、旧ADR及既有源码不变。
对120个基线文件重新计算摘要，只有上述4个架构测试变化，其余116个一致，包含
F0/E2A/E2B、README、.gitignore、历史ADR和旧源码。旧补丁仍100674 bytes，
LastWriteTimeUtc为2026-10-28T04:02:46.0959302Z。9个新增文件no-index空白检查
无错误（exit1表示存在新增差异，只有LF/CRLF提示）；本地文档链接缺失0、矩阵20项。
新增9文件扫描原始线程链接、UUID、用户私有路径和高置信凭据模式均0；这是限定
模式审查，不是任意形式秘密不存在的证明。Kickoff_Docs、CAE models和本地Codex配置
仍被原.gitignore精确排除。Git复核为4个tracked修改+13个untracked
（9个本轮文件+4个旧资料），暂存区为空，main/HEAD不变。

未运行Abaqus/ODB/AF Owner，不访问真实模型、不操作原Desktop Main、不改AbqJobPilot。
无F1 App Server需停止；一次认证子进程已回收。离线测试子进程由pytest检查退出；
最终限定进程检查：命令行引用本轮精确私有根的Python进程为0。
这不是任意后代进程的完整枚举，不声称全机不存在其他用户进程。

## 8. 后续建议（未实施）

先评审PARTIAL的来源语义及认证/能力方案。继续真实F1需要另行审定专用认证安排、
配置查询范围、无工具/自动源关闭证据、bootstrap/seed intent及子进程归属；不复制
现有凭据。之后实现窄adapter和唯一线程3Turn实测。错误原文未留存，下一轮先设计
可脱敏诊断，不假定登录解决所有门槛。

研究者只读status UI可限定展示queue/UNKNOWN、观测时间/类型、来源摘要、阻断原因
与资格；打开页面不能初始化、恢复或派发。审批控制、真实外部事件各自另案设计。

**完成报告后停止等待架构评审，不自动进入下一阶段或创建Git Checkpoint。**
