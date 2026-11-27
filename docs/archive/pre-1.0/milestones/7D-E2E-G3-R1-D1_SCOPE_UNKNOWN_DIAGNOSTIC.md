# G3-R1-D1 — Scope UNKNOWN 诊断与离线修复

日期：2026-10-30。结论：**G3_R1_D1_DIAGNOSTIC_PASS（限定诊断与离线修补）**。

本次 B1 的具体运行时根因仍未确定。已确认并修复的是**失败位置和数值错误信息丢失**，不是已证明的 Owner 自等待。没有启动新原生 fixture、Job、Owner 或安装；没有查询、附加、终止或关闭原 Owner/Job。

```text
HISTORICAL_B0=PASS
HISTORICAL_B1=BLOCKED_FIXTURE_SCOPE_UNKNOWN
B2=NOT_RUN
BUILD_05=NOT_READY
OWNER_LIVE_STATE=UNKNOWN
OWNER_OBSERVABILITY=NOT_OBSERVABLE
ORIGINAL_OWNER_QUERY_COUNT=0
NEW_NATIVE_FIXTURE_COUNT=0
RUNTIME_ROOT_CAUSE=UNRESOLVED
DIAGNOSTIC_INFORMATION_LOSS=CODE_CONFIRMED
REAL_A_READY=FALSE
```

## 1. 来源、白名单与保存范围

两仓基线核验为 GD `main@69b144cea9aecc515e15cc830368972b09258af9` 和 AF `Develop@7f4b8d8f3a2c862ed8b244d495295f5d51ea0d88`。入场时分别保留 5、4 个已跟踪修改；索引均为空。GD 有 25 个非忽略未跟踪文件，AF 有 59617 个；只保存文件名清单的私有摘要，不打开这些非目标材料，也不清理、暂存或重置它们。

本轮仓库内仅新增此报告。修补位于原任务根下的独立 `d1-offline` 子目录，不覆盖六份原源码、原 `b1_owner.py`、旧报告、原账本或回执。位置以环境变量表达：`%LOCALAPPDATA%/GDCAE-G3-R1-B1-20261030-A01/d1-offline`，下文简称 `D1_ROOT`；原六文件目录简称 `SOURCE_A`。未新建原生 Owner，也未修改原 Owner 所加载的文件。

D1 根、source、evidence 子目录沿用新任务根的受限继承；只读核查确认所有者及三个允许主体符合既有资格，未修改任何 ACL。当前令牌/目录检查不等于原 Owner 状态查询。

| D1 文件白名单 | 变化 | 作用 |
| --- | --- | --- |
| `source/g3_install_controller.py` | 修改副本 | 失败事件附加白名单诊断；记录控制流阶段；读取时校验新增诊断。 |
| `source/g3_install_win32.py` | 修改副本 | 为 accounting、wait、exit-query、cleanup、close 失败附加固定位置及数值信息。 |
| `source/g3_scope_diagnostics.py` | 新增 | 纯函数、版本化严格字段投影，无 OS 操作。 |
| `source/test_g3_d1_diagnostics.py` | 新增 | 37 项纯 fake-kernel / controller 故障注入。 |
| `source/d1_safe_checks.py` | 新增 | 复用原 B0 runner 的输出抑制和禁止操作守卫，固定三份测试模块并分组计数。 |
| 另四份原 fixture、原测试及原 runner 副本 | 字节不变 | 保留对照，不增加实际执行入口。 |

两份修改副本的统一差异保存在 `D1_ROOT/evidence/diagnostic-only.patch`；全部证据文件均仅在任务目录内。历史 G3、R0、R1 和 B1/B2 报告以字节摘要核验，不直接输出含私有标识的历史正文。

## 2. 可证伪的根因分析

以下原代码位置均指 `SOURCE_A` 的冻结文件，不以 D1 新行号替换历史定位。

| 检查 | 级别 | 源码位置与结论 |
| --- | --- | --- |
| Job 创建与计数拓扑 | CODE_CONFIRMED | `g3_install_win32.py:221` 的 `prepare` 创建新的 unnamed Job，要求初始 total=0；`:250` 的 `spawn` 仅将 fixture root 经 Job-list 在创建时加入。`:310` 查询的是 `self.job`，没有把 Owner 加入这个新 Job 的调用。 |
| Owner 所属宿主 Job | CODE_CONFIRMED / NOT_OBSERVABLE | `IsProcessInJob(current, None)` 只查询 Owner 是否属于某个 Job，不是加入新 Job，也不能证明原宿主策略。宿主层级策略及当前成员状态未查询。 |
| Owner 自等待假设 | 不获源码支持 | 不能因为 Owner 可能处于宿主 Job，就认为它计入自己的新 child Job。原代码没有显式持久化 Owner 对确切新 Job 的 nonmembership 记录，故不宣称拥有独立实时成员证明。 |
| 父子循环等待 | CODE_CONFIRMED：源码未发现 | `g3_install_fixture.py:13` 启动固定 sleep child，三个标准流为 DEVNULL；parent sleep 后非阻塞 poll 并返回。没有消息、管道 EOF、join 或 child.wait 依赖。 |
| 后续 Owner 保持循环 | CODE_CONFIRMED | `b1_owner.py:57` 的 hold 路径在 controller 返回未关闭回执之后进入，刻意保留句柄。它解释历史上的等待状态，不能解释此前 UNKNOWN 的来源。 |
| 原始句柄 | CODE_CONFIRMED | `spawn` 保留 CreateProcess 原始输出；Job handle 是原 CreateJobObject 返回值。没有 OpenProcess、OpenJobObject、DuplicateHandle 或 PID 接管路径。`:351` 的 close 逐个清空已成功关闭的字段。 |
| 句柄继承与范围 | CODE_CONFIRMED | Job 用空 security attributes 创建，root 的 bInheritHandles=False；自身 Job flags 只有 ACTIVE_PROCESS 上限 3，没有 breakaway 或 KILL_ON_JOB_CLOSE。未查询的宿主策略不能推定为相同。 |
| accounting 与 root 观察 | CODE_CONFIRMED | `observe:319` 先查 Job，再查 root wait/exit；这是多个 API 调用，不是原子快照。矛盾观察继续拒绝，不能直接解释为逃逸。 |
| 错误折叠 | CODE_CONFIRMED 缺陷 | `ScopeError:17` 只保留 code；`_account:310`、`observe:319`、`cleanup_expired:336` 等共享错误码；controller `fail:368` 只记 primary/cleanup，通用异常也可能折叠为 UNKNOWN。失败 API、返回值及即时 last-error 没有落盘。 |
| 超时与关闭 | CODE_CONFIRMED | 正常观察环有时限，超时路径先记录 `FIXTURE_TIMEOUT_CLOSED`，再尝试原 scope cleanup；成功关闭前要求 root signaled 且 scope empty。hold 路径没有查询/退出协议。本轮没有改变任何终止或关闭时序。 |
| ABI | 静态未发现明显缺陷 | `_api:72` 所审阅的 Job query、Wait、GetExitCode、CreateProcess 签名及结构字段未发现明显位宽错误；这不是新运行时 ABI 资格验证。 |

Microsoft 明确新建 Job 初始没有关联进程；创建者不会仅因创建动作自动加入。默认子进程归属和 breakaway 是另外的 Job 规则。[CreateJobObjectW](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-createjobobjectw)、[Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects)

`ActiveProcesses` 是当前关联计数；`TotalProcesses` 是生命周期累计；`TotalTerminatedProcesses` 针对 limit violation，不能拿来等同全部自然退出。文档关于退出和引用释放的说明不能证明本次发生了哪种状态，更不授权关闭原句柄。仅凭 active 不归零，不能认定是 Owner 自等待或进程仍在执行。[Accounting 定义](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_accounting_information)

### 分支范围可以缩小，但不能指认一个 API

已持久化的历史字段为 primary=null、cleanup=`FIXTURE_SCOPE_UNKNOWN`，最后一次成功接受的观察仍为 root 未 signaled、active=2、total=2。结合冻结控制流：

- 正常 deadline 分支会先设置 primary=`FIXTURE_TIMEOUT_CLOSED`，与已有字段不吻合。
- controller 的 `INVALID_OBSERVATION` 拒绝会保留相应 cleanup code，也与该历史 code 不同。
- 下一次 native observe 的共享 ScopeError 分支，或观察环中的通用 BaseException 折叠，是优先调查集合。

这是**基于源码与已接受证据的推断**，不是一次失败 API 的实际返回记录。Job query 失败、计数范围检查、binding check、wait 异常返回、首次 signaled 后的 exit-code 查询失败以及通用异常，仍不能由现有记录进一步区分。不得将其改写为已确认的访问拒绝、超时、逃逸、句柄丢失或自然退出。

## 3. 原现场证据与当前不可观察状态

使用原 reader 只读验证准确的任务私有账本，SQLite integrity、摘要链与 flow 校验均通过。输出前仅投影固定事件枚举、字段存在与否及允许的计数/布尔值，没有输出真实进程身份、句柄、令牌或命令行。

历史顺序仍为 `ATTEMPT_CREATED → SCOPE_PREPARED → SPAWN_INTENT → ROOT_REGISTERED → RESUME_INTENT → ACTIVE(1/1) → ACTIVE(2/2) → UNKNOWN`。两次已接受观察均为 root 未 signaled、exit=null、terminated=0、in_job=true。没有成功 CLOSEOUT。

账本保存了 root 身份字段、image digest 及 scope policy；没有持久 owner 进程身份、epoch 或独立 Job 对象身份。请求摘要可用于审计关联，但这些数据不能在 Owner 丢失后重建原始句柄能力。

原 `b1_owner.py` 没有受支持的 stdin/RPC/socket/事件/命令文件查询入口；hold loop 不调用 observe。因此本轮 **零次原 Owner 查询**，没有轮询旧执行会话，也没有对现存进程进行扫描、attach 或借用句柄。过去观察到 Owner 保持运行，不证明它现在仍运行或已经退出。当前 active、root signaled 和原始 handle-table 状态全部 `NOT_OBSERVABLE`。

只读证据：`D1_ROOT/evidence/static-and-history.safe.json`。该文件中的旧账本与旧回执字节摘要只用于前后完整性检查，不是不可篡改证明。

## 4. 最小离线修补及其边界

独立 Reviewer 确认诊断丢失是可静态证明的局部缺陷，支持在新副本修复；没有确认的拓扑缺陷，不改 Job 成员关系、原 Owner hold、deadline、cleanup/close 授权或公开回执。

新增 `g3-d1-diagnostic-v1`：字段严格限定为 `schema/site/reason/return_code/win32_error`。site/reason 使用固定枚举；数值必须是非 bool 的 UINT32 或 null。未知键、任意文本、异常消息和越界数值拒绝；损坏的 backend diagnostic 投影为固定的阶段/未分类异常，不输出原值。

native 副本为 accounting、root wait/exit、cleanup 和 close 的受审查分支增加诊断。只有对应 API 明确失败时才即时读取 ctypes last-error；成功和非 API 检查不读可能陈旧的 last-error。等待异常返回与 WAIT_FAILED 区分。没有记录原始 observation payload、PID、handle 值或异常 repr。

controller 在已有 UNKNOWN/BLOCKED_CLOSEOUT body 中可选附带版本化诊断，并记录 OBSERVE、VALIDATE、CLOSE 等实际阶段。新 reader 校验该可选字段；旧的无诊断 body 仍可读，公共 receipt 的 schema/字段保持不变。没有修改旧 ledger、给旧 UNKNOWN 补写失败原因或宣称旧 reader 会强制新增诊断语义。

诊断落盘仍是 best-effort：磁盘/账本写失败时保留先前已提交 intent，仍 BLOCKED，不补造成功、不重试执行。尚未为每一个 prepare/spawn 原生 API 增加数值诊断；这些异常可能只得到固定 controller phase。此补丁不保证所有故障都能完整记录，也不增加原 Owner 查询能力。

### 源码与测试归因

| 修改点（D1 行号） | 保持的安全属性 | 代表测试 |
| --- | --- | --- |
| native `ScopeError:19`、`checked:31`、`_account:322`、`observe:333` | 同样失败关闭，不关闭失败 scope；即时数值诊断 | `test_native_failure_sites_are_distinct_without_native_calls`、`test_success_never_reads_stale_last_error` |
| native `cleanup_expired:351`、`close:368` | 原顺序与授权不变；只增加失败描述 | `test_cleanup_failure_diagnostics_use_fake_kernel_only`、`test_fake_close_failure_has_numeric_diagnostic_and_retains_failed_handle` |
| controller `fail:377`、`run_attempt:347` | 原 receipt 不变、UNKNOWN 无重试；失败写入不造成功 | `test_historical_shaped_observe_fault_persists_site_not_false_root_exit`、`test_diagnostic_write_failure_does_not_close_retry_or_invent_success` |
| controller `_validate_flow:156`、诊断模块 | 版本化可选字段、严格投影、旧无诊断记录可读 | `test_diagnostic_schema_rejects_unknown_text_and_non_numeric_fields`、`test_old_failure_body_without_diagnostic_is_still_readable` |

“self_count / mutual_wait” 新测试只是条件状态模型：持续 active 时必须有限停止且不得 PASS；它们不能识别实际 Job 成员，也不是本次自等待的证据。没有把字典里的数字改名后当成真实拓扑验证。

## 5. 实际测试与检查

使用登记的 LangChainEnv Python 3.12.10、pytest 9.1.0，现有 pywin32 312；Ruff 0.12.0。没有安装依赖或切换环境。

| 检查 | 实际结果 | 回执 |
| --- | --- | --- |
| 原六文件 fresh B0 | **93 passed / 0 failed / 0 skipped / 0 errors** | 原任务 `evidence/b0-run04.safe.json` |
| 最终 D1 固定三模块集合 | **130 passed / 0 failed / 0 skipped / 0 errors** | `D1_ROOT/evidence/b0-run03.safe.json` |
| 最终集合分组 | 71 controller + 22 native pure + **37 新增负例** | 同一最终运行的 groups，不拼接不同运行结果 |
| 禁止操作守卫 | 0 触发；native families 0；源码前后摘要一致 | Popen/socket/system/native API/security 入口在 pytest 前设 trap |
| Ruff，D1 source 九文件 | exit 0、0 diagnostics | `static-and-history.safe.json` |
| 两仓 diff、限定补丁及报告隐私 | 见最终完整性回执 | `final-integrity.safe.json` |

测试前审查了三份实际模块：原 controller fake、原 native AST/fake-handle、新 fake-kernel。runner 在当前 Python 测试进程内调用 pytest，原始 stdout/stderr 被抑制，只输出计数、白名单测试定位及摘要。禁止入口 guard 不是通用 OS 沙盒；结论也依赖已审查测试源码。普通 Python 测试命令与 Ruff 进程不属于受管 native fixture/Owner；没有执行 B2 的进程集成选择。

真实过程记录：首个修补集合 124 passed（新增 31）；按 Reviewer 意见补齐六个负例后 130 passed。首次 Ruff 报 E701/F811，修正 task runner 的格式与测试 fixture 导入别名后，最终集合重新执行仍为 130 passed，Ruff 为 0。没有以预期数量代替结果，也不把原 93 与新 130 相加宣称 223 个不同测试。

最终完整性检查确认：GD 未跟踪数 25→26，唯一新增为本报告；AF 仍为 59617，原清单全部保留。两仓 tracked diff 摘要、HEAD、branch 和空索引均不变。两仓 `git diff --check` 均 exit 0；两份实际修改副本的 `git diff --no-index --check` 返回 1、非 warning 输出 0，保留这个真实返回值，不将其写为 exit 0。报告的 UUID、原始 SID、thread URI、凭据模式和私有 profile 路径匹配均为 0。该扫描不是对全部历史私有资料的重新认证。

最终修补文件 SHA-256（不是执行授权）：

| D1 source 文件 | SHA-256 |
| --- | --- |
| `g3_install_controller.py` | `4a0539e68911b5979d3aef22dafd518a0d8e872dfbf6ace03de81789f51895bd` |
| `g3_install_win32.py` | `79b5385f0bd85fa19128e958968fe1f33acc2283a22cbfeaddb3b3e34917ba8d` |
| `g3_scope_diagnostics.py` | `b518e9c3ba0e0cbd71143681924a5c581be7f98074de80807d22feeb359d01f7` |
| `test_g3_d1_diagnostics.py` | `e9d21326d5a07e7f12c74080ef55cd74fcce34279a2a74af6bba03732c8df6d8` |
| `d1_safe_checks.py` | `17fcef9b51296e23ba8ccaf55a6a07dce699e0d1f2e5a369925993a47f2b2ab9` |

## 6. 独立审查与验收矩阵

独立源码审查者和只读 Reviewer 均不支持将 Owner 自等待或父子互等作为已确认根因。Reviewer 要求修正未启动分支的 phase 标注，补充 prepared-close/validation 及 cleanup 诊断负例；已经落实。Reviewer 独立读取最终 130 项回执并重算受测源码摘要，原六份冻结源码仍匹配。Reviewer 未调用原生 API、现存进程查询或测试。

| ID | 结果 | 证据 / 限制 |
| --- | --- | --- |
| D1-01 | PASS | 两仓 HEAD/overlay/index 与未跟踪清单保存；仅本报告为仓库新写入，无提交推送。 |
| D1-02 | PASS | 所有历史 BLOCKED/NOT_RUN/NOT_READY 保留，旧报告字节不变。 |
| D1-03 | PASS | 明确区分历史 1→2→UNKNOWN 与当前不可观察。 |
| D1-04 | PASS | 原证据先白名单投影；不输出真实身份、句柄、异常正文。 |
| D1-05 | PASS，静态范围 | 精确新 Job 创建/纳入/查询代码；无 Owner 自加入路径；没有当前成员表证明。 |
| D1-06 | PASS，运行根因仍 UNKNOWN | 错误分支可定位到集合；诊断丢失确证，不能指认具体 API。 |
| D1-07 | PASS，审查范围 | 句柄/等待/管道/breakaway/kill-on-close 审查完成，宿主策略未查询。 |
| D1-08 | PASS：NOT_OBSERVABLE | 没有现成安全入口，因此未查询、未注入、未新建 Owner。 |
| D1-09 | PASS | 两个 task 副本的局部诊断修补、37 个纯模拟负例；不增加执行权。 |
| D1-10 | PASS，离线限定 | fresh 93 与最终 130 真实结果、Ruff/diff/摘要/隐私检查；native/B2 未运行。 |
| D1-11 | PASS，限定审查 | 独立复核保留失败 API、当前占用及原句柄状态的证据缺口。 |
| D1-12 | PASS：审批草案 | 下节为唯一下一步请求；没有自动授权新 B1、Owner 处置或安装。 |

## 7. 唯一下一步安全操作审批单（未执行）

**请求对象：D2 原尝试状态处置与下一次 B1 准入裁定。当前不具备安全启动新 B1 的条件。**

1. **当前精确状态：** 原 B1 历史 UNKNOWN；原 Owner 当前运行/退出、Job 占用和句柄生存均 NOT_OBSERVABLE。无现成同 Owner 查询通道，持久 root 身份不是重新取得原始句柄的授权或能力。
2. **本次推荐裁定：保留。** 未证明原能力可用前，不向原 Owner 发控制操作，不强关、不抢锁、不从 PID 接管、不借新实验代替旧收尾。任何清退方案须先说明准确对象归属、操作能力来源、影响范围及无法恢复的后果，并取得单独精确授权；本报告不提供一个假装已可执行的终止命令。
3. **新 B1 的先决条件：** 先对原未知尝试作出独立批准的保留/处置决策并满足单家族约束；确认任务根与实际祖先链资格；冻结新的完整依赖摘要，包含新增诊断模块；将新诊断版本和 owner 的受支持只读观察能力纳入独立预检。原 wrapper 的旧六文件 pin 不能直接当作 D1 新依赖闭包。
4. **未来实验上限（仍需另批）：** 一次全新、精确标识的无害 parent+child family；创建前持久 intent、原始句柄、固定输入、限定 timeout；失败位置/数值返回必须通过投影保存。查询接口须在新 Owner 创建前审查，不得给原 Owner 注入改造。
5. **立即停止条件：** 身份或摘要不符、原能力丢失、API/占用结果 UNKNOWN、意外成员、隐私输出或未批准副作用。保持原状态，不重试；B2 只有取得新实验真实 clean closeout 后才可另行恢复。build_05 与真实 A/B 不包含在此申请内。

本轮到此停止。`G3_R1_D1_DIAGNOSTIC_PASS` 只说明诊断与离线修补完成，不是 B1/B2/build_05/真实求解资格。
