# G3-R1-D2 — 单次原生资格复验：预检阻断

日期：2026-10-30。**本轮在 Gate A6 停止原生实验准入，未进入 Gate B。**

```text
D2_PREFLIGHT=BLOCKED_HOST_JOB_LIFECYCLE_UNPROVEN
D2_NEW_NATIVE_ATTEMPT=NOT_RUN_PREFLIGHT_BLOCKED
NEW_NATIVE_ATTEMPT_COUNT=0
NEW_JOB_OR_OWNER_CREATED=false
NATIVE_ATTEMPT_QUOTA_CONSUMED=false
B2_CURRENT_FULL_REGRESSION=NOT_RUN
BUILD05_READY_FOR_REVIEW=false
BUILD05_INSTALLED=false
OLD_B1_HISTORY=BLOCKED
OLD_OWNER_LIVE_STATUS=NOT_OBSERVABLE
REAL_A=NOT_RUN
PUBLIC_RELEASE=NOT_AUTHORIZED
```

这不是“第二次原生 UNKNOWN”：本轮没有发起新的原生尝试，也没有创建 Job、fixture root process 或控制 Owner。新建的是受限文件目录和源码快照。普通诊断 Python、零进程 pytest 和 Ruff 命令不等于受管 native fixture；不能将本轮描述为完全没有运行任何程序。

## 1. 基线与 D1 实物核对

| 项目 | 开工事实 |
| --- | --- |
| GD-CAE | `main@69b144cea9aecc515e15cc830368972b09258af9`；5 个既有 tracked 修改；index 空；26 个非忽略 untracked 文件。 |
| AF Develop | `Develop@7f4b8d8f3a2c862ed8b244d495295f5d51ea0d88`；4 个既有 tracked 修改；index 空；59617 个非忽略 untracked 文件。 |
| 环境 | 按登记复用 LangChainEnv Python 3.12.10、pytest 9.1.0、pywin32 312；Ruff 0.12.0；无安装或升级。 |
| D1 正式报告 | 与 D1 最终安全回执中的 SHA-256 匹配；D1-01～D1-12 的限定结果经白名单字段核对。未转储历史报告正文。 |
| D1 测试回执 | 实际 `130 passed / 0 failed / 0 skipped / 0 errors`，其中 D1 新增 37；八份受测源码摘要逐一匹配。 |

新任务根以环境变量表达：`%LOCALAPPDATA%/GDCAE-G3-R1-D2-20261030-A01`，下文简称 `D2_ROOT`。没有复用旧 UNKNOWN 的运行目录、attempt marker、账本、进程、端口、凭据或执行预算。新 root 的源码仅来自经校验的 D1 独立副本；未假定 D1 已合入正式产品代码。

D2 将九份 D1 文件按原字节复制到 `D2_ROOT/source`。其中 controller、native backend、fixture、诊断模块以及原测试均保持不变。旧源码和旧报告只作摘要/安全投影核验；旧 Owner、Job 和历史进程未查询、未附加、未终止、未关闭、未改锁。

## 2. Gate A6 的实际阻断证据

对**当前诊断命令进程自身**进行了有限只读查询，没有创建或打开任何其他进程/Job：

| 白名单字段 | 实际结果 |
| --- | --- |
| Windows 版本 | major 10，build 26300 |
| `IsProcessInJob(GetCurrentProcess(), NULL)` | 成功，true |
| `QueryInformationJobObject(NULL, ExtendedLimits)` | 成功 |
| 当前直接宿主 LimitFlags | 12288，即 `0x3000` |
| 当前直接宿主 ActiveProcessLimit 字段 | 0；ACTIVE_PROCESS flag 未设置，不把字段 0 解释为零进程上限 |
| 当前直接宿主 UI restrictions | 查询成功，0 |
| 未来测试 Owner 的宿主状态 | 未观察 |
| 宿主/祖先链及句柄生命周期资格 | 未获证明 |

`0x3000` 是 `KILL_ON_JOB_CLOSE (0x2000)` 与 `SILENT_BREAKAWAY_OK (0x1000)`。前者使最后一个 Job handle 关闭具有终止影响；后者允许子进程脱离，并不证明它们脱离所有祖先。NULL 查询只指向调用进程的直接 Job。[Microsoft 标志定义](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_limit_information)、[QueryInformationJobObject 查询范围](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-queryinformationjobobject)

观察到这些 flags **不是**证明宿主已失控，也不是证明未来 Owner 一定会被终止。阻断原因是：当前证据无法建立未来 Owner 与其祖先 Job 的安全生命周期契约，不能保证需要保留原始句柄时宿主不会使这种能力失效。UI=0、未设置 active limit、Windows 支持 nested Job 或 silent breakaway 的存在，都不能填补这个证明缺口。

任务书 Gate A6 明确要求：第三方宿主影响 Job 归属且无法证明安全时 STOP。独立 Reviewer 依据上述实际投影作出 `BLOCKED_HOST_JOB_LIFECYCLE_UNPROVEN`，没有给出 `D2_PREFLIGHT_PASS`。本轮没有改变宿主 flags、申请 breakaway、切换执行宿主来试探、提高权限或绕开这一门槛。

这个新观察只涉及当前预检进程，**不能定位旧 B1 的失败原因，也不能推断旧 Owner 当前存活或退出**。安全回执：`D2_ROOT/evidence/host-preflight.safe.json`。

## 3. 已完成的独立安全准备

### 目录、权限与来源

- 创建了一个全新 root，创建时即传入受限且 protected 的 DACL；允许当前所有者、SYSTEM 和本地 Administrators，未先开放后修复。
- 逻辑父目录和实际解析后的九级祖先经过只读检查；当前令牌为非 AppContainer、无 restricted SID 的进程令牌，并执行当前令牌 AccessCheck。没有发现额外普通主体的适用删除/替换/WRITE_DAC/所有权权限。
- 四个任务目录及十二份 source 文件核查 owner、三主体 ACL 和非重解析点状态。既有目录 ACL 没有修改。新原生账本未创建，因此没有将目录准备等同于实际 native ledger 资格。
- 权限结论仅限当前所有者与 OS 管理员为可信主体的本地威胁模型；foreign-token 攻击测试未执行，不声称抵御同用户任意代码或管理员。能力 ACE 与普通写入者分开评估。
- D1 九份副本字节一致；新根中所有受测依赖由测试前后摘要绑定。没有读取生产模型或账户秘密。

回执：`root-qualification.safe.json`、`logical-parent.safe.json`、`source-snapshot.safe.json`、`source-security.safe.json`。摘要用于一致性审计，不是不可篡改证明。

### 持久阶段与句柄审查

原 D1 顺序是 `ATTEMPT_CREATED → backend.prepare/Job 创建 → SCOPE_PREPARED → SPAWN_INTENT → 创建时绑定且挂起的 root → ROOT_REGISTERED → RESUME_INTENT → resume`。它不等于已经完成 D2 的外层一次性 intent：未来 D2 包装器需在任何 Job 创建前另行持久化一次性尝试与完整来源。本轮没有构建或调用这个原生包装器，没有生成实际 native attempt ID，也没有消费一次性额度。

D1 的关闭顺序为已提交的 scope-empty/root-exit 观察和 `CLOSEOUT_REQUESTED`，随后 native close，再写 `CLOSEOUT_ACCEPTED`。Reviewer 指出，不能把 REQUESTED 偷换为任务书要求的 COMMITTED。未来需要显式复核“释放前持久终态观察”和“释放后最终接受”的对应关系；本轮未修改核心顺序，也未宣称该额外门槛已满足。

已审查代码没有把 Owner 加入自己新建的 Job；固定 fixture 没有父子消息/管道互等。原始 root/process/thread/Job handles 的保存路径仍存在，但本轮没有新原生 handle，也没有实际 binding、运行或释放证明。

## 4. 新鲜零进程测试与普通修正

新增的三个 task helper 文件：

| 文件 | 作用 / 限制 |
| --- | --- |
| `source/d2_boundary.py` | 必要的静止条件纯谓词：root signaled、exit 0、active 0、total 恰好 2、limit-termination 0。没有启动接口，也不能证明 child 的独立 exit code。 |
| `source/test_d2_boundaries.py` | 直接测试实际 D2 BoundedSink 的输出上限和溢出不回退；测试精确数量及失败计数拒绝。 |
| `source/d2_safe_checks.py` | D1 runner 的任务副本，固定四份纯测试模块并冻结完整受测依赖。 |

静止条件 helper **尚未接入原生 Owner**，不能以其 mock PASS 代替实际 family 的身份、child completion 或 closeout 证据。D1 的同时活跃进程上限 3，以及观察到的累计 total≤3 守卫，与 D2 预期 family 成员恰好 2 不是同一约束；累计守卫不是内核强制的生命周期创建上限。

实际执行：

| 检查 | 结果 |
| --- | --- |
| 最终一次固定集合 | **141 passed / 0 failed / 0 skipped / 0 errors** |
| 同次分组 | 原 controller 71 + native pure 22 + D1 37 + D2 新增 11 |
| 运行中禁止操作触发 | 0；native family 0 |
| 源码前后摘要 | 11 份受测文件一致；九份 D1 原副本保持不变 |
| Ruff | 十二份 source 文件，exit 0，0 diagnostics |
| B2 全回归 | NOT_RUN，未达到 Gate B 通过条件 |

测试模块是原三份 D1 模块加 `test_d2_boundaries.py`。pytest 在当前测试 Python 进程内执行；Popen、socket、system、native API 和 security 入口设禁止操作守卫，原始输出被抑制。结论针对这些已审查的代码路径，不是全机进程监控或通用安全沙盒。

真实修正记录：首轮 139 passed 后，Reviewer 指出补充谓词仍允许 terminated=1/2，且输出测试导入的是 D1 sink 副本。已将谓词明确命名为必要静止条件、拒绝所有非零限额终止，增加两个负例，并改为导入实际 D2 sink；最终完整同一源码集合重新执行为 141 passed。没有修改 D1 核心流程，也没有重跑原生实验。

最终回执：`evidence/b0-run02.safe.json`、`evidence/ruff-final.safe.json`。没有把历史 130 直接作为本轮成绩，也没有累加多次运行冒充不同节点数量。

## 5. D2-01～D2-15 验收矩阵

| ID | 结果 | 证据 / 限制 |
| --- | --- | --- |
| D2-01 | PASS | 两仓实际基线、dirty overlay、历史摘要及未跟踪清单建立。 |
| D2-02 | PASS | D1 正式报告、130 回执、新增 37 和依赖摘要/Review 核对。 |
| D2-03 | PARTIAL | 新 root/祖先/source 权限准备通过；新原生账本未创建，不能声称全运行权限验收。 |
| D2-04 | NOT_RUN | D1 顺序已静态审查；没有 D2 外层实际 durable intent 或外部作用。 |
| D2-05 | NOT_RUN | 创建时绑定代码保留；没有新 native binding。 |
| D2-06 | BLOCKED | 无 Owner 自加入路径的静态证据；未来宿主/祖先生命周期未获证明。 |
| D2-07 | PARTIAL / BLOCKED | 新鲜 141 项与权限检查通过；Reviewer 未签发 D2_PREFLIGHT_PASS。 |
| D2-08 | PASS，仅数量边界 | 新原生尝试 0；不宣称已执行一次 family。 |
| D2-09 | NOT_RUN | 没有新 Job accounting、child/root 收尾或 native 成功/失败账本。 |
| D2-10 | PASS | 旧 Owner/Job/build_04 未操作，旧事实未改写。 |
| D2-11 | PASS，预检停止 | 未开始首次新尝试，因而也没有第二次；B2/安装保持停止。 |
| D2-12 | NOT_RUN | Gate B 没有 PASS，B2 不符合启动条件。 |
| D2-13 | PASS | 无提交/推送、Stable/AF/正式产品源码修改或既有 ACL 变更。 |
| D2-14 | PASS，限定审查 | 白名单输出和独立 Reviewer 完成；不能解除 A6。 |
| D2-15 | NOT_ELIGIBLE | B1/B2 未通过，不提交 build_05 安装资格申请。 |

独立 Reviewer 重新检查了宿主回执、权限结果、九份 D1 副本、最终 141 回执及十一份受测摘要；确认源代码不扩大执行权。Reviewer 要求保留所有 NOT_RUN/BLOCKED，不将 pure PASS 写作 native 验收。

本轮仓库新增仅此报告。任务目录另有新 helper、复制文件、合成测试材料及安全回执。两仓既有修改和非目标未跟踪材料均保留；最终 diff、历史摘要和隐私检查记录在 `evidence/final-integrity.safe.json`。

## 6. 一页备选分发设计与唯一下一步建议

本轮没有再次原生 UNKNOWN，因此不能伪称触发了“第二次失败”的历史止损条件。以下是面对已存在的宿主准入缺口的**保守备选设计**，尚未执行、未验收：

1. **交付单位：** 继续采用既有文件白名单的 Wheel/Plugin 候选、SHA-256 manifest、依赖版本和许可证清单；复制闭包与敏感信息检查先行。不增加新的通用进程 Supervisor。
2. **安装边界：** 可选择明确人工安装步骤，或等待正式安装器独立合格。人工安装只能标记 MANUAL_INSTALL，不能冒充自动安装 PASS；本轮不发出可执行安装命令、不安装任何包。
3. **证据分离：** 静态包完整性、离线 import/契约验证、实际安装收尾、四个原生自定义角色加载、Desktop `@GDCAE` 和科学结果验证分别验收。缺失项目保持 NOT_RUN；Plugin 文件存在不能证明 Desktop 激活。
4. **主线优先级：** 新授权应优先处理受保护 Operator、动态 Standard 的合法派发和真实 DAT 来源。备选分发不能替代 HIL、真实 A→B、V2/V4 或真实 Solver 证据；本轮不顺带修改或执行这些支线。
5. **若未来恢复自动控制器：** 先取得可核验的宿主/祖先 Job 及原始句柄生命周期契约，完成一次性 intent、释放前终态持久化、释放后接受的明确映射和独立预检。不得通过 Full Access、改 Job flags、breakaway 或换宿主试跑绕过当前门槛。

**唯一下一步建议：架构评审临时采用“白名单候选包＋明确人工安装”的独立分发路线，将自动安装保留为未验收能力；或在具备上述宿主证明后另批恢复 D2 准入。此处不是 build_05 申请，也不是自动继续的授权。**

本轮需要用户执行的登录、复制文件、提供 ID/Token 或操作系统动作：**0 项**。只等待架构裁定；单次 native 额度虽未消费，当前回合结束后也不会自行恢复实验。
