# M03-E2B — Disposable Desktop interoperability: G0 safety stop

日期：2026-10-29，Asia/Shanghai。
结果：**M03E2B_BLOCKED_UNSAFE_TEST_CONFIGURATION**。
这是实际 G0 配置证据门未通过后的停止报告，不是 Desktop 互操作 PASS，
也不是已观察到 writer conflict 的 `M03E2B_PARTIAL_WRITER_BLOCKED`。

## 1. 分开的实际结果

| 结果维度 | 本轮结果 |
|---|---|
| E2B_READONLY_DESKTOP_BINDING_PASS | NOT_TESTED：用户提供唯一目标链接，已私有保存；运行时身份及历史未核验 |
| E2B_EXTERNAL_TURN_PROTOCOL_PASS | NOT_TESTED：外部 turn/start 调用数为 0 |
| E2B_PERSISTENCE_RECONNECT_PASS | NOT_TESTED：没有运行线程客户端或独立重连 |
| E2B_DESKTOP_LIVE_VISIBLE | NOT_TESTED |
| E2B_DESKTOP_REOPEN_VISIBLE | NOT_TESTED |
| DESKTOP_RESTART_VISIBILITY | NOT_TESTED：没有自动或人工重启实测 |
| E2B_SAFE_COOWNERSHIP | NOT_PROVEN；没有 runtime ownership 检查 |
| ORIGINAL_DESKTOP_MAIN_AUTO_RESUME | NOT_TESTED，明确禁止 |
| PRODUCTION_UNATTENDED_CONTINUATION | NOT_VERIFIED |
| ABAQUS_EXECUTION_VERIFIED | false |
| SCIENTIFIC_VERIFICATION_AVAILABLE | false |

外部提交与可归因文本 Turn 副作用：**0**。thread/read、thread/turns/list、
thread/resume、turn/start、turn/steer、thread/queue/add 调用均为 0。
测试线程持久 pre/post 历史数量为 **UNKNOWN / UNKNOWN**，不能填写 0→0：
用户后续确认 UI 恰好一问一答、回复为 TEST THREAD ONLY、无工具且空闲；这是人工
UI 基线，不是已读取的持久 Turn 身份。最初限定检查时指定链接文件不存在，未读取
其内容。随后用户通过当前对话提供唯一测试链接，已保存到受限私有 manifest，
没有将原始链接或 ID 写入本报告、仓库文件或摘要输出。当前对话及含绑定值的工具
调用记录已包含测试标识，不能声称它只存在私有 manifest；未删除或修改会话记录。

## 2. G0 已完成的取证与停止理由

起始分支 `main`，HEAD `538bfae9a3a5fcea97970b9effc4f1f168490650`；
tracked clean、index empty。原有两个 untracked 文件是
`docs/milestones/M01-C_SOURCE_DIFF.patch` 和
`docs/milestones/M03-E2A_DESKTOP_COMPATIBILITY_AUDIT.md`。
已完整阅读本轮任务书、E2A 报告、全局 AGENTS、环境登记及现有 E1 测试 adapter 源码。
没有将 E1 adapter 直接用于 Desktop：它的全量 config/account 读取与线程创建等能力
不符合本轮限定范围，且它绑定旧的自有测试目录与生命周期。

| 对象 | 本轮实际取证 |
|---|---|
| Desktop | 官方 app 版本工具自报 `26.1023.51421` / build `22530` / prod；About UI 仍未验证，未更新或重启 |
| CLI | 当前绝对路径 exe 的 `--version` 返回 `codex-cli 0.165.0-alpha.1.2`，exit 0 |
| App Server | 同一 exe 的 `app-server --help`；稳定 schema 离线导出 exit 0。没有运行 RPC server 或 initialize 握手 |
| Transport | help 支持并默认 STDIO；本轮没有建立 STDIO RPC 会话，不能称为传输实测 PASS |
| Python | 已有 `D:\XianLab\envs\LangChainEnv\Scripts\python.exe`；3.12.10、SQLite 3.49.1、pytest 9.1.0；仅标准库审计代码，无安装/环境修改 |
| CODEX_HOME / CODEX_SQLITE_HOME | 未读取或打印实际值，未覆盖或更改。官方文档说明后者还可能受 sqlite_home 配置优先级影响；相同账户/CLI不证明目标共享状态 |

公开背景重新阅读了 [App Server 文档](https://learn.chatgpt.com/docs/app-server)、
[环境变量](https://learn.chatgpt.com/docs/config-file/environment-variables) 和
[CLI 参考](https://learn.chatgpt.com/docs/cli/reference)。本机 schema 控制实际判断；
当前文档不是当前安装版本的运行成功证据。

### 2.1 唯一的无服务启动配置检查

使用 help 明确支持的 `app-server --print-startup-config`，在新空测试 cwd 中进行
一次短时配置检查。进程级参数请求只读 sandbox、approval=never、web_search disabled、
notify 空、已知 node_repl 禁用，以及以下 feature=false：shell_tool、unified_exec、
apps、plugins、multi_agent、shell_snapshot、hooks、computer_use、skill_search、
tool_suggest。未传 `--ignore-user-config`，未使用 profile hack，未写全局配置。

真实结果：exit 0；stdout 121 bytes；stderr 0 bytes；没有启动 App Server 服务。
原始 stdout 仅进入短时子进程结果内存缓冲。程序解析 JSON 并检查预定义安全键，
没有输出或保存非白名单值，原始输出也未落盘。保存的摘要只有退出码、长度、
键是否存在及检查布尔值，不含原始配置内容或身份。

**这不是选择性服务端配置查询，也不构成安全证明。** 返回数据没有预定义的顶层
config/requirements/features/sandbox_mode/approval_policy/web_search/notify/mcp_servers
键；feature 检查均为“未能确认 false”，不能解释为实际启用，也不能解释为实际禁用。
没有为诊断而再次输出原始数据、深入未知字段或直接打开 provider/credential/config 文件。

因此，这次命令仅证明该静态入口接受参数并返回，不能证明目标线程的有效工具、
MCP/hooks、sandbox 或权限已受限；不能用 prompt 中“不要使用工具”补足证据。

### 2.2 为什么没有继续用其他接口绕过门槛

主审与独立 Reviewer 阅读本轮生成的静态 schema，未调用这些运行时接口：

| 窄查询候选 | 静态发现 | 不能据此通过 G0 的原因 |
|---|---|---|
| config/read | 参数只有 cwd/includeLayers；没有字段投影；Config 含 model_provider 等非本轮准许配置信息 | 全量读取后客户端过滤不等于避免读取被禁止内容；未调用 |
| configRequirements/read | 返回 requirements 等约束 | 要求不等于目标线程当前有效权限；未调用 |
| experimentalFeature/list | 可带 threadId/cursor/limit | 无目标身份的结果不证明这个 Desktop 线程；部分 feature 状态也不证明全部工具权限；未调用 |
| mcpServerStatus/list | 可带 threadId/serverName/detail/分页 | 一个已知服务器禁用不证明所有潜在 MCP 或其他工具禁用；不为获取库存而提前加载未知线程 |

任务书 G0 明确要求无法限定测试 Turn 的权限时停在
`BLOCKED_UNSAFE_TEST_CONFIGURATION`。据此停止，未启动 runtime client，未把 G0
降格成“只做读取所以可忽略有效权限”。这是本轮证据和权限边界的阻断，**不是断言
该产品永远没有可行的安全接口**。下一次尝试需要新的明确权限/证据方案，不能偷偷
扩大读取范围、改全局配置或换 HOME 绕过。

## 3. G1 人工准备的实际状态

已按授权在仓库之外建立全新测试根，内含空 `workspace` 和独立 `private-audit`。
先设置显式 ACL，仅当前用户与 SYSTEM 有继承 FullControl，关闭继承并验证规则数。
未创建 Git 仓库、AF Project、科研模型或生产配置。ACL 不是恶意同用户防护。
真实测试根路径仅留在本地操作记录，不写入公开交付文档。

向用户发出了 G1 手动创建、无工具 seed、支持的单线程复制链接和 idle 确认请求，
该请求与剩余 G0 静态预检并行；这不是 G0 已通过的声明。发现上述 G0 阻断后，
已明确撤回继续人工准备的要求。随后收到用户延迟送达的 G1 完成确认及新的明确
指令：继续身份核验和 G2 静态预检，全部门槛通过前不得外部 turn/start。

用户确认：在指定独立 workspace 创建了新测试线程，标题为
`GDCAE-E2B-DISPOSABLE-TEST`，UI 恰好一问一答，回复 TEST THREAD ONLY，
无工具/文件/命令活动，当前空闲且无其他客户端写入；通过官方功能保存了目标链接。
这些为用户报告，未冒充程序读取到的身份、历史或 writer lease。

后续只对指定根目录、private-audit 和精确 target-link.txt 路径做限定检查。
父目录 ACL/非 reparse 检查未报错；目标文件 Get-Item 明确返回不存在，因而没有
完成目标文件 ACL、格式或内容核验。主 Agent 另行存在性检查确认 g1-binding.json 不存在。
已请求用户核对精确保存路径，没有枚举目录、寻找相近文件名或猜测 ID。
该时点附加状态为 `BLOCKED_NO_SAFE_THREAD_BINDING`；原 G0 配置证据阻断仍有效。

后续用户直接回复了一个测试线程 deep link。主 Agent 仅校验其为单一、格式合法的
目标链接，没有打开链接或查询线程。核对测试根和 private-audit 的非 reparse 属性
及仅当前用户/SYSTEM 的允许 ACL 后，以 CreateNew 独占创建 g1-binding.json，
Flush(true) 后重新读取并内部比对目标值；新文件 ACL 检查也通过。未改写或伪造
target-link.txt，manifest 明记来源 explicit_user_reply，而非此前缺失的文件。
新建受控文件中的原始目标值保存在仓库外的受限 manifest，不在交付报告复述；工具结果仅输出布尔
核验结论。manifest 明记 runtime_identity_verified=false、runtime_writer_verified=false、
external_turn_start_allowed=false。现在“未取得目标标识”的缺口已解决，完整 G1
身份与持久基线仍未核验；G0 阻断未解除，也没有从格式正确推定链接对应指定 UI。

没有扫描线程索引、rollout、会话目录，没有 thread/list、原 Main 读取、UI 自动化
或广域截图。G3 的最终外部写入 go-ahead 没有请求，也没有以阶段批准替代它。

## 4. 所有权与可见性：风险成立，运行事实未测

本机稳定 ThreadReadResponse 的 Thread.status 不是 writer lease/排他所有权证明。
TurnStartParams 描述允许输入加入活跃 Turn；schema 没有给本实验一个可依赖的
expected-idle 原子门。即使未来用户说 idle 且读取也为 idle，仍须证明 writer 安全。
没有证据时应 `WRITER_BUSY_OR_UNKNOWN`，不能为了观察拒绝而试 thread/resume。

收到人工确认后已再次核对本轮生成的稳定 schema，完成 G2 **静态预检**：
Thread 对象没有 writer lease 字段；TurnStartParams 仅要求 input/threadId，
没有 expected-idle 或等价 CAS 参数；parentTurnId/rootTurnId/turnTrigger 的说明
明确提及向 active Turn 加入输入或 steer。TurnSteerParams 的 expectedTurnId
只适用于该活跃 Turn 接口，不能借用为 turn/start 的排他锁或重放保证。
clientUserMessageId 仅有可空字符串类型，不能据此推定幂等语义。
config/read 仍只有 cwd/includeLayers，feature/MCP 查询可指定 threadId 但不构成
完整有效权限证明。没有因此启动服务或调用任何上述 RPC；G2 runtime 尚未开始。

新指定 [公开 issue 47193](https://github.com/openai/codex/issues/47193) 本轮读到 open，
updated 2026-10-13。作者报告在较早 Windows/CLI 版本上历史已完成但 Desktop
仍保留 writer，外部 resume 被拒绝。这是风险背景，不是本机已复现的拒绝、产品
bug 诊断或可以尝试抢占的授权。本轮没有真实 writer conflict 证据。

Protocol、历史、Desktop live、navigation/reopen、restart、普通 UI follow-up
全部保持 NOT_TESTED。没有用某个静态 JSON、mock、E1 历史结果或模型自报填充这些结果。
尤其没有把空闲线程写入解释成并发安全，因为本轮根本没有写入。

## 5. E2B-01～E2B-18 完整矩阵

| ID | 实际结果 | 证据及未完成原因 |
|---|---|---|
| E2B-01 | PARTIAL | 工具版本与本机稳定 schema 已核验；About UI/服务握手/目标有效配置未验证 |
| E2B-02 | PASS | 无 unsupported flag、全局修改或 unsafe fallback；无服务配置检查不作为权限 PASS |
| E2B-03 | PASS（人工确认） | 全新测试目录及私有ACL已准备；采纳用户关于Desktop新建线程、无工具seed的陈述，不代表身份绑定已核验 |
| E2B-04 | PARTIAL | 后续用户提供单一目标链接并私有绑定；运行时身份未核验，未访问原Main或其他私有线程 |
| E2B-05 | PASS（仓库/报告范围） | 受控文件保存位置为仓库外私有manifest；报告与摘要无原始ID；对话/工具调用记录的额外留存风险明确记录 |
| E2B-06 | PARTIAL | 用户确认UI一问一答且空闲；持久首Turn身份未读，历史数量UNKNOWN |
| E2B-07 | NOT_TESTED | 未运行targeted runtime读取；未修改科研状态 |
| E2B-08 | PARTIAL（静态） | schema预检完成；G0及身份门未过，实际writer未查，没有用resume试探 |
| E2B-09 | NOT_TESTED（gate closed） | 无write go-ahead、无TURN_START_INTENT、0外部start |
| E2B-10 | NOT_TESTED | 无真实新增Turn、terminal或无工具执行验收 |
| E2B-11 | NOT_TESTED | 未运行独立重连，不冒称持久历史恢复成功 |
| E2B-12 | NOT_TESTED | 未人工观察外部Turn的实时显示 |
| E2B-13 | NOT_TESTED | 未进行navigation/reopen显示实验 |
| E2B-14 | NOT_TESTED | 明确没有Desktop重启，更没有程序化重启 |
| E2B-15 | NOT_TESTED | 无本轮harness或mock/fault-injection执行；E1历史去重测试不是本轮证据 |
| E2B-16 | NOT_TESTED | 未制造或观察runtime冲突，未queue/steer/解锁/抢占；没有并发安全结论 |
| E2B-17 | PASS（无服务启动） | 无App Server RPC进程待清理；短时CLI命令均已退出，未终止其他进程 |
| E2B-18 | PASS（停止报告审查） | 独立Reviewer、18项标签、隐私/空白/Git检查通过；不是互操作实验PASS |

不设置总实验 PASS。安全停止不是目标线程互操作、去重或故障注入测试的替代品。

## 6. 测试、文件和清理

本轮没有修改生产路径、既有测试或 MCP 接口；没有新增实验运行客户端，未将
Desktop 控制器加入仓库。临时 Python 只用已验证解释器和标准库执行一次无服务
配置入口及摘要投影，后续做文件存在性、静态schema检查及 PowerShell 私有绑定保存，
没有 pytest/mock 执行。
故不重跑源码回归或 Ruff；不能引用
703 历史通过作为本轮结果。交付检查限新增 Markdown 的空白/链接/隐私与 Git 保全。

仓库只新增本报告：`docs/milestones/M03-E2B_DESKTOP_INTEROP_DELIVERY_REPORT.md`。
E2A 报告保留 SHA-256
`1254420fae360ec75211034aee0fbf4397d41abce8049ef93e28b631d391303c`。
旧审阅补丁只核对 metadata：100674 bytes，LastWriteTimeUtc
`2026-10-28T04:02:46.0959302Z`，未读/哈希/修改/清理。
HEAD、tracked files 和 index 保持冻结基线；无暂存、提交、推送、fetch 或 CI。
没有访问 AbqJobPilot、真实CAE模型、旧加密凭据或历史 journal。

独立 Reviewer：`/root/m03e2b_review`。初审独立确认配置查询不具字段投影、requirements
与feature清单不等于目标有效能力、idle不等于writer释放。最终全文复核无阻断性文档
问题，支持 G0 停止报告，未把它升级为实验 PASS。Reviewer 独立核对 main/HEAD、
tracked/index diff、三个 untracked 路径及 E2A 摘要；未读取私有 manifest 或原始配置。
stdout 长度/退出等是主 Agent 的实际操作证据，不能说成 Reviewer 重跑测得。
确认范围为可见操作、静态描述、Git和报告；不是全系统法证或其他进程状态保证。

人工确认后的更新稿也由同一 Reviewer 独立复核：人工 UI 基线、文件缺失、静态
schema 与运行时未测的区分成立，没有错误授予互操作 PASS。已按其意见澄清私有
manifest 存在性检查由主 Agent 执行。目标文件缺失时的前一版身份状态为 BLOCKED；
用户后续提供链接后，更新为本地绑定已保存、运行时未核验，矩阵 E2B-04 为 PARTIAL。
Reviewer 未访问目标链接或 manifest，也未独立观察用户 UI。

后续链接绑定更新亦经同一 Reviewer 只读复核：E2B-04 PARTIAL 与 E2B-05 限定
仓库/报告范围的 PASS 恰当，无新权限或运行时 PASS；已消除旧版 BLOCKED 叙述
与当前状态的歧义，保留对话/工具调用记录的标识留存风险。

实际交付检查：18 项矩阵齐全，4 个 HTTPS 引用；UUID、具体用户路径、实际 scratch
路径和高置信凭据模式均为 0。新增文档 no-index whitespace 检查无错误，仅 LF/CRLF
提示；Git tracked/index diff 为空，HEAD 不变。未运行 pytest、mock/fault injection
或 Ruff，不把文档检查冒充这些测试。既有补丁和 E2A 文档原样保留。

## 7. 下一阶段建议

维持 **GD-CAE-owned persistent CLI/App Server Main** 为默认架构方向，Desktop
只承担明确人工界面或独立只读观察入口；这仍不是生产无人值守能力验收。
若要再次尝试 Desktop 分支，应先单独审查一个受支持、字段受限且不读取被禁止
provider/凭据信息的有效能力证明方案，再确定可观测的writer许可/拒绝边界。
只有这些条件与用户的唯一测试身份、最终go-ahead都满足后，才讨论一次外部文本Turn。
不要为继续实验要求修改全局配置、释放Desktop writer或更换线程。

本轮停止。没有进入 G2 runtime/G3/G4，也不继续下一阶段、Git Checkpoint 或科研执行。
