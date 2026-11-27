# M03-F1-R1 — Offline remediation and authentication audit

日期：2026-10-29。最终状态：**BLOCKED_PRIVACY_OUTPUT**。
这是本轮硬停止与恢复交接报告，**不是 R1 离线验收 PASS，也不是 R2 授权**。
原 [F1 PARTIAL 报告](M03-F1_DELIVERY_REPORT.md) 与
[F0](../architecture/M03_F0_PERSISTENT_CODEX_MAIN_RUNTIME.md)、
[F1 架构](../architecture/M03_F1_BOUNDED_CODEX_MAIN_RUNTIME.md) 均保持原字节。

## 1. 停止事件与实际处置

在核查历史依据时，主 Agent 使用 Get-Content 输出旧 `M03-E1_DELIVERY_REPORT.md`
开头内容，意外将其中已有的原始测试线程/Turn标识重复暴露在本轮工具输出中。
该操作违反 R1 G0.4“不重复或记录原始临时测试标识”的要求，并触发任务书的
thread/private secret exposure 硬停止条件。本报告不复述任何这些值。

这是本轮操作错误，不能只归为历史文件的问题；新报告的隐私扫描通过也不能消除
已经发生的工具输出留存。没有声称这些记录已被删除，也没有修改历史报告或日志。
未打开原开发 Main 的私有会话内容，未调用 Desktop 线程读写接口。

发现后立即停止开发与测试，仅进行本轮进程收尾、只读保全和本报告交接：

- 用本轮唯一私有根限定 Python 测试进程，逐项核对 PID、创建时间及命令行身份后停止。
- 停止2个仍存活的自有测试进程；没有针对其他用户进程。
- 两个测试 runner 均返回 `TEST_EXIT=-1`，属于主动停止，不是 pytest 完整结果。
- 最后限定检查：命令行引用本轮精确测试根的 Python 进程为0。不是全机进程证明。
- 没有删除文件、清理故障 journal、回滚代码或覆盖历史证据。所有未完成改动保留待审。

## 2. 必须分别报告的结果

| 标签 | 本轮结论 |
|---|---|
| F1R1_TWO_COMMITTED_DECISIONS | **BLOCKED**：已有合法实现及首轮用例通过，最终版本验收因硬停止未完成；不是 SOURCE_API 不支持 |
| F1R1_SIDECAR_SAFETY | **PARTIAL**：保留原设计，新增实现获静态复核；完整故障/回归未完成 |
| F1R1_PAUSE_REQUEST_AFTER_CURRENT | **BLOCKED**：接口已实现，首轮三个时序通过；最终验收未完成 |
| F1R1_AUTH_DIAGNOSIS | **UNKNOWN / AUTH_CAUSE_UNKNOWN** |
| F1_REAL_OWNED_THREAD_TWO_EVENT_ACK_PASS | **NOT_TESTED**，本轮禁止 |
| DESKTOP_ORIGINAL_MAIN_RESUMED | **false** |
| AF_REAL_EXECUTION_VERIFIED | **false** |
| PRODUCTION_UNATTENDED_RUNTIME_VERIFIED | **false** |

原历史780 passed / 21 skipped仍属于F1，不能算本轮通过数量。Reviewer认可限定
设计或准确停止报告，也不等于批准全部F1/R1。

## 3. 已实施但尚未完整验收的修复

### 3.1 合法的两份 Decision 来源

独立源码探索确认现有固定 `synthetic-workflow-v1` 已支持公开
`WorkflowCoordinator.advance(expected_revision)`，按前置候选/预算/Receipt/Evidence
校验依次提交两次 `WORKFLOW_RECORDED/DECIDE`。无需原 SQL 写入或 Project schema 修改。

新增 `prepare_two_decision_runtime` 在全新 TEST_SYNTHETIC fixture 中使用该路径。
准备阶段产生两个合成候选、两次合成预算扣记、fixture端口的两个本地effects，以及
不同decision_id、事务、source revision和摘要的A/B记录。所有准备写入在Runtime
初始化前完成；不包含真实Codex、AF、Abaqus或ODB。数值仅是合成fixture数据。

Runtime采用显式 `bounded-ack-policy-r1` / `bounded-ack-runtime-r1` 和
`runtime-decision-source-r1`，绑定两份真实提交的合成Decision。旧v1 A+STOP继续按旧
含义读取，不能计入两Decision验收；旧实例不升级、不迁移。新DTO沿用同一sidecar
表和文件，不新增调度数据库；旧reader会拒绝新r1 DTO，不宣称反向reader兼容。

当前来源适配采用既有 **Project-owned validated read primitive 的内部适配器**：
`ResearchProject._snapshot()`默认只读，由原`_read_state`校验身份/schema/完整审计；
再由`_load`和`mutation._recheck`核对流程与实际候选。它不是公开稳定API。
A/B之间有合法PREPARE、候选、预算、CLAIM和OBSERVE提交，故检查递增完整审计，
不再误要求两个Decision的审计序列相邻。每次派发在intent之后、最后port调用之前
再次检查来源和freshness；源失效保留UNKNOWN而不发送。

测试增加只读SQLite逻辑dump对照，包含schema与记录；不把文件bytes变化等同于
科研逻辑记录变化。Snapshot在返回前关闭，任何Fake RPC等待都不持Project/sidecar
事务；两库和远端之间仍无原子事务，最终来源检查后仍存在不可消除的外部竞态。

### 3.2 当前尝试后暂停

新增 `request_pause_after_current_turn(operator_id, command_id, expected_revision,
expected_epoch)`，通过sidecar短事务记录`PAUSE_REQUESTED`，不取得/接管sender锁。

- PAUSE与INTENT在同一个sidecar事务权威中串行化。
- pause先提交：不能再claim后续事件。
- intent先提交：暂停回执列出已获发送权的intent，即使RPC尚未写出，该尝试仍可完成。
- 回执不宣称当前Turn已暂停/中断，不承诺此前获准的发送立即归零。
- 后续ACK重读最新journal，保留暂停状态；E2不再claim。
- UNKNOWN无论暂停或恢复都继续占用，不变成可重试状态。

独立`resume_queue`要求operator、revision/epoch CAS、当前来源freshness及sender锁；
它不清UNKNOWN、不退款、不调用port。旧`control`保留旧v1语义；r1实例必须使用新
明确入口，避免绕过epoch/来源复核。epoch仍是intent序号，不是OS进程租约证明。
Operator ID是受信调用边界标识，不是新实现的用户认证系统。

## 4. 安全认证诊断记录

执行前先在本报告草稿记录副作用审查，再进行唯一版本诊断。
本轮只读取旧F1专有目录中的已脱敏`auth-probe-result.json`；没有打开auth秘密文件、
全局session历史或真实线程manifest，没有复制凭据。

旧F1结果：login status exit1、stdout 0 bytes、stderr 318 bytes、process_exited=true。
原错误正文未保存，不能判定缺少登录、配置选择失败、provider问题或其他具体原因。

[官方认证文档](https://learn.chatgpt.com/docs/auth) 区分文件、系统凭据存储和临时
存储，并说明缓存、刷新及登录日志。[官方命令参考](https://learn.chatgpt.com/docs/developer-commands?surface=cli)
给出login status的状态含义，但不能据此证明当前安装版绝不会写共享位置或刷新凭据。
本轮因此**没有再执行login status**，没有反复远端试错、登录/登出或改变认证配置。

唯一实际诊断是当前已知绝对路径CLI的`--version`：使用新私有HOME、空cwd、白名单
环境、stdin禁用、30秒上限；不继承token或会话变量。只保存匹配版本格式的字符串、
退出码、长度和退出状态，原stderr不保存或发布。

| 认证边界 | 实际证据与结论 |
|---|---|
| OS进程启动/CLI元数据 | 本轮version exit0，`codex-cli 0.165.0-alpha.1.2`，直接子进程已回收；stderr 299 bytes未留原文 |
| 旧status的配置选择/加载 | UNKNOWN；缺少可安全归因的原错误和有效配置证据 |
| CLI用户登录状态 | UNKNOWN；exit1没有可验证的详细原因 |
| model-provider凭据/网络许可 | NOT_TESTED；版本命令不访问模型 |
| 隔离HOME与会话状态 | 新诊断根没有复制既有认证或会话；不证明整个OS凭据层隔离 |
| App Server协议初始化 | NOT_TESTED；server starts=0 |
| 模型Turn认证 | NOT_TESTED；thread/seed/turn=0 |
| sandbox/no-tool与原生Goals门 | NOT_TESTED；必须与认证分开，不因version成功放行 |

结论`AUTH_CAUSE_UNKNOWN`，不是“已确认未登录”。缺失证据为：可安全脱敏的具体旧错误、
当前安装版status路径的共享写/刷新边界、实际有效配置及被选认证源。由于本轮已硬停止，
不提出现在登录或粘贴凭据的操作；之后可另案审定一个有限本地诊断方案。

## 5. 实际测试与尚未执行项目

复用绝对解释器`D:\XianLab\envs\LangChainEnv\Scripts\python.exe`，本轮验证
Python3.12.10、pytest9.1.0、SQLite3.49.1；Ruff0.12.0。无安装或环境变更。
使用进程级PYTHONDONTWRITEBYTECODE=1、PYTEST_DISABLE_PLUGIN_AUTOLOAD=1、源码
PYTHONPATH，并将GDCAE_M01B_LIVE/GDCAE_M01C_LIVE/GDCAE_M03B_LIVE全部置空。

```powershell
# 三次运行各用不同新basetemp；下面以标签隐藏私有根
& 'D:\XianLab\envs\LangChainEnv\Scripts\python.exe' -B -m pytest tests/unit/test_main_runtime.py -k r1 -x -q -p no:cacheprovider --basetemp '<R1-private-root>/focused-1'
& 'D:\XianLab\envs\LangChainEnv\Scripts\python.exe' -B -m pytest tests/unit/test_main_runtime.py tests/architecture -q -p no:cacheprovider --basetemp '<R1-private-root>/focused-2'
& 'D:\XianLab\envs\LangChainEnv\Scripts\python.exe' -B -m pytest tests/unit/test_main_runtime.py -k 'r1_read_adapter or r1_initialization or r1_two_independent' -q -p no:cacheprovider --basetemp '<R1-private-root>/focused-3'
& 'D:\ProgramData\anaconda3\Scripts\ruff.exe' check --no-cache .
git diff --check
```

| 检查 | 实际结果及限制 |
|---|---|
| focused-1 | **6 passed, 69 deselected in176.51s，exit0**；使用最初多次公共读取的来源适配；后改为单snapshot并补测试，不能外推为最终版PASS |
| focused-2 | 主动停止，TEST_EXIT=-1，仅有进度点，没有完整统计/耗时，不计PASS |
| focused-3 | 主动停止，TEST_EXIT=-1，仅有进度点，没有完整统计/耗时，不计PASS |
| 完整无Solver pytest | **NOT_RUN_IN_R1**；硬停止后未启动 |
| Ruff | All checks passed!，exit0；最后源码修改后已执行 |
| Git tracked diff --check | exit0；只有LF/CRLF提示，无空白错误 |
| 新增报告/本轮改动空白及隐私检查 | 5文件无空白错误，限定隐私模式匹配0；报告本地链接缺失0、F1矩阵20项；不能消除前述工具输出事件 |

首轮6项覆盖：两个独立Decision与逻辑不变、三种暂停时序、另进程暂停且UNKNOWN
经恢复后仍阻断、控制幂等/身份/epoch及合同变更后恢复拒绝。
后续加入初始化/intent/ACK硬退出、源缺失/错序/foreign、候选篡改、独立进程恢复/
双dispatcher竞争和无DB跨port锁等用例，**最终完整结果未取得**。
故障测试的monkeypatch由frozen Project实例改为类级读边界；这是测试实现修正，
当前被停止的运行不据此推定已经通过。旧F1全部测试保留。

## 6. F1/F0 对齐与本轮关闭状态

Option 1A决定继续有效：Runtime内部原子提交，ResearchProject只读提供来源；
没有Project schema迁移或第二调度库。下表F0编号指原设计第11节；F1编号指原任务书。

| F1 | R1实际状态 | F0相关条件 |
|---|---|---|
| 01 | PARTIAL：已对齐裁定/来源/暂停设计；本轮发生隐私硬停止 | 全部，特别01/03/13/20 |
| 02 | PASS静态：无新Harness/DAG/daemon/AF执行者 | 20 |
| 03 | BLOCKED最终验收：合法两Decision路径已实现，首轮通过 | 04/05/11 |
| 04 | PARTIAL：新policy固定两事件/同线程，最终回归未完 | 02/17/18 |
| 05 | PARTIAL：sidecar原子设计保留，新增控制未完成全测 | 03/04 |
| 06 | PARTIAL：intent前提交/短事务已有静态复核 | 06/12 |
| 07 | PARTIAL：前驱ACK和新pause双门已实现 | 09/10/16/18 |
| 08 | PARTIAL：重复无新start首轮验证；最终未完 | 04/06/18 |
| 09 | PARTIAL：来源/epoch/foreign/摘要负向用例待完整结果 | 04/10/11/12 |
| 10 | PARTIAL：原owner锁保留；新双进程竞争运行被停止 | 07/08 |
| 11 | PARTIAL：首轮UNKNOWN跨pause/resume通过，全部故障未完 | 09/10 |
| 12 | PARTIAL：正向历史对账保留，新增AB用例运行被停止 | 10/16 |
| 13 | PARTIAL：逻辑snapshot首轮通过；最终跨进程未完 | 03/11/14/19 |
| 14 | PARTIAL：新增故障代码保留，无最终全矩阵结果 | 04/06/09/10 |
| 15 | PARTIAL：STORE_BUSY策略未改，本轮完整回归未完 | 15/17 |
| 16 | NOT_TESTED：真实seed+2明确禁止 | 18/19 |
| 17 | BLOCKED真实门：版本可执行；auth/Goals/no-tool仍未证 | 01/07/08 |
| 18 | PARTIAL：无真实Turn；首轮Fake与逻辑科研状态隔离 | 16/17/20 |
| 19 | PARTIAL：Ruff/diff通过，完整pytest未运行 | 20 |
| 20 | PARTIAL：设计/当前源码已独立审，停止报告单独复核 | 20 |

F0全部条件均以上表引用或保留历史缺口：01/02真实能力与bootstrap仍未证；03–06
离线来源/队列测试待完整；07/08未验证真实orphan/PID治理；09–12新增故障待完成；
13/14暂停语义已修、首轮测试通过但无真实身份UI；15无磁盘耗尽实测；16不升级科学
验证；17无token费用硬限；18/19真实三Turn与客户端恢复禁止；20隐私事件硬停止。

## 7. 独立审查与工作区

`/root/f1r1_source_audit`只读核查公开advance与固定AB路径，确认无需改Project schema，
不能复用只支持单A的旧E1 brief适配；没有执行测试或服务。
`/root/m03f0_review`完整阅读R1任务书及当前源码，认可intent线性化暂停、旧新policy
分型和validated snapshot内部adapter；强调最后读取与RPC无跨系统原子性，UNKNOWN
不得清除。它没有复跑测试或读取私有身份材料，不将静态意见写为运行PASS。
最终独立审阅仅读取本阻断报告，接受硬停止及限定交接的准确性，无新增报告阻断。
进程/测试/129文件摘要数量依据主Agent实测记录；Reviewer未复跑、未读取私有根或
历史标识。其明确要求本轮不得报告R1完成或PASS。

当前分支main，HEAD仍`538bfae9a3a5fcea97970b9effc4f1f168490650`。
相对R1起点仅修改4个既有F1文件：

- `src/aegiscae/research/main_runtime.py`
- `src/aegiscae/research/main_runtime_rules.py`
- `tests/integration/m03f1_support.py`
- `tests/unit/test_main_runtime.py`

新增仅本报告。Git总体仍有前轮4个tracked架构测试修改，现有14个untracked（原13个
加本报告），index为空；本轮没有再改那4个架构测试，也没有改main_runtime_store。

129个起点文件摘要核对，仅上述4个文件变化，其余125个一致；包括F0/F1架构、原F1
PARTIAL报告、E1/E2A/E2B、README、.gitignore、历史ADR和其他旧源码。
旧M01-C补丁未读内容，仅metadata仍为100674 bytes及原UTC修改时间。
忽略保护Kickoff_Docs、CAE models、本地Codex配置保持，无暂存/提交/推送/CI。

没有访问真实CAE模型、修改AbqJobPilot、启动Abaqus/AF Owner/ODB或App Server，
没有创建线程或发送任何外部Turn，没有安装依赖或修改全局认证配置。
本轮临时合成数据库、故障journal、测试日志与脱敏version结果保留在受限私有根；
不清理旧F1、M01-B或其他历史材料。本轮未将任何原始线程标识写入新增报告，但
前述工具输出留存事实必须保留披露。

## 8. 恢复与R2建议（未授权执行）

先评审本次隐私硬停止。若另行批准恢复R1，应从现有未提交实现继续，先对历史报告
采用输出前脱敏/限定字段读取，再完成新增故障测试与完整无Solver回归，不重写F1历史。
不得把本轮的进度点或早期6项通过当成最终源码验收。

R2仍需独立批准，前提是R1离线关闭、认证诊断边界和有效no-tool/Goals策略均可证明，
再准备唯一自有CLI线程seed→ACK(E1)→ACK(E2)、有界生命周期及独立读回计划。
当前不请求用户登录、编辑文件或提供私有ID；也不实施R2或只读UI替代任务。

**硬停止后仅完成收尾与报告，等待评审。**
