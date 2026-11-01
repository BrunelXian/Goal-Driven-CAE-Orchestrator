# M03-E2A — Desktop interoperability and thread-ownership feasibility audit

审计日期：2026-10-29，Asia/Shanghai。版本与 schema 取证窗口：19:40–19:49。
范围：只读可行性研究及人工可执行的后续实验设计；不是 M03-E2B 实验授权。

## 1. 结论和证据等级

当前架构判断：**DESKTOP_INTEGRATION_UNVERIFIED**。尚无本机证据证明独立
App Server 的写入会同步到已经打开的 Desktop 会话，也没有证明两个客户端之间
存在可靠的排他写入契约。近期产品方向推荐 **Option B：GD-CAE-owned persistent
CLI/App Server Main**，配独立只读科研状态/人工决策入口；Desktop 保持人工界面。
这是后续架构建议，不是当前无人值守生产能力或执行授权。

| 状态 | 本轮值 |
|---|---|
| 审计验收 | M03E2A_READONLY_FEASIBILITY_PASS |
| DESKTOP_THREAD_WRITE_TESTED | false |
| DESKTOP_LIVE_VISIBILITY_VERIFIED | false |
| ORIGINAL_DESKTOP_MAIN_UNTOUCHED | true；独立复核限本轮可见操作/取证清单和 Git 文档审查，不是系统级法证保证 |
| E1_EVENT_TO_CLI_TURN_PASS | 历史限定结果；本轮未重跑，不能转作 Desktop 证据 |
| 真实 V2/V4、AF/Abaqus 资格 | 本轮未验证、未执行 |

证据分层：L=本轮本机官方 CLI help/静态 schema；M=官方 Desktop 工具版本自报；
O=当前官方文档；I=公开 issue 作者的报告；H=本地已验收历史报告；
U=未验证。静态字段存在仅证明描述能力，不能证明运行时所有权、权限或 UI 行为。

## 2. 冻结基线与实际操作边界

仓库：`D:\Projects\Goal-Driven-CAE-Orchestrator`。
分支 `main`；起始 HEAD 为 `538bfae9a3a5fcea97970b9effc4f1f168490650`，
直接父提交 `6c549dc98c25a12dcb9c93baa4fbf8d629c80ec1`。
起始 tracked clean、index empty，仅 `docs/milestones/M01-C_SOURCE_DIFF.patch`
未跟踪。补丁只核对文件元数据，不读取、复制、哈希或清理；其长度 100674 bytes，
LastWriteTimeUtc 为 `2026-10-28T04:02:46.0959302Z`。

`git check-ignore -v` 对不存在的探针确认 `/Kickoff_Docs/`、`/CAE models/`、
`/.codex/config.toml` 的根目录排除规则；`git ls-files` 确认这些区域无已跟踪路径。
未遍历这些私有目录，只按用户给定路径阅读本轮任务书。

已阅读全局 AGENTS 和环境登记；未调用 Python、安装包或更改环境。既有项目指令
搜索没有找到额外 AGENTS。读取本地 M03-E1 报告时，输出前在内存中把 UUID 形状
和用户目录替换为 REDACTED；没有打开报告引用的私有 thread、rollout、凭据或日志。
M03-G-R1 TEMP 审计与一页 E2 建议均仍存在，按已知精确路径读取，未搜索历史私有目录。

本轮仅新增本报告。唯一附带生成物是新 TEMP 审计目录中的静态协议 schema：
无线程身份、无会话文本、无 RPC 请求。没有运行 App Server 服务、daemon/proxy、
UI 自动化、线程列表/读取/恢复/续 Turn，亦没有读取配置内容、凭据或更改 CODEX_HOME。
版本取证调用了官方 Desktop `check_app_update`，返回安装版本元数据；没有下载、
安装或重启。公开文档与 GitHub issue 通过只读工具获取。

历史基线 H：M03-E1 报告记录一条自有 CLI 测试线程，seed 后一次事件 ACK，
历史 1→2，四次重复投递未新增 Turn，intent-before-effect、UNKNOWN no-retry；
E1-15 仍为 LIMITED synthetic ACK。M03-G-R1 的 703 passed / 21 skipped、
843.42 秒属于上轮真实回归，不是本轮重跑结果。其 Checkpoint 包含 46 个文件。

## 3. 当前版本、进程形态及不确定性

| 对象 | 本轮事实 | 来源与限制 |
|---|---|---|
| Desktop release/build | `26.1023.51421` / `22530`，channel `prod` | M：官方 app 工具自报；没有打开 About UI，UI-confirmed version = UNKNOWN。没有将工具返回冒称截图或 UI 核验 |
| Desktop 安装包 | 路径显示 `OpenAI.Codex_26.1023.6621.0_x64`，主映像 `ChatGPT.exe` | 只读进程映像元数据；MSIX 包版本与产品 release/build 是不同编号 |
| 当前 PATH CLI | `codex-cli 0.165.0-alpha.1.2` | L：对 Get-Command 解析出的绝对 exe 执行 `--version`，exit 0 |
| App Server 工具版本 | 同一 exe 的 `app-server --help` 与 schema 导出 | 不是新服务的 initialize 握手版本；独立服务运行时版本未探测 |
| Windows | Windows 11 家庭版中文版，`10.0.26300` / build `26300`，64 位 | 只读 `Win32_OperatingSystem`；不是旧报告推断 |
| 当前执行环境 | Windows PowerShell，本 shell 无 WSL 上下文 | 本机 OS/shell 查询；不能据此排除机器上其他 WSL 环境 |
| 已运行后端形态 | 观察到 native Windows `codex.exe app-server`，父进程 `ChatGPT.exe`，与当前 CLI 是同一安装映像路径 | 仅输出名称/映像与参数布尔值，未输出完整 CommandLine、PID、窗口标题或线程 ID；没有连接这个进程 |
| 传输 | 观察到的命令行没有 listen/stdio/code-mode-host 显式选项；help 默认 `stdio://` | 默认 STDIO 是基于 help 的推断，未检查管道或建立连接；不能声称探测了活动传输 |
| 共享后端/共享存储 | U：未证明独立 CLI 客户端与 Desktop 共用一个 live server，也未证明其有效 session home 一致 | 相同 exe/账户不等于同一 server、session store 或跨客户端订阅 |

用户目录仅在本地取证命令使用，报告用安装位置模板
`%LOCALAPPDATA%\OpenAI\Codex\bin\<installation-slot>\codex.exe` 表示。
当前 exe SHA-256：`0c09e45bc76433756eb2d492f6db0ce6f269967e6618f4a6ae73e2fa239694b8`。
M03-E1 报告的安装 slot 与当前不同；版本字符串相同不能证明 exe、参数或能力相同。

实际命令记录：

| 命令（CLI 表示已解析的绝对 exe） | 结果 |
|---|---|
| `CLI --version`、`CLI --help` | exit 0；读取支持命令，不调用列线程等子命令 |
| `CLI app-server --help` | exit 0；服务默认 STDIO，另列 daemon/proxy/schema 工具；均未作为服务运行 |
| `CLI app-server generate-json-schema --help` | exit 0；支持 `--out` 与可选 `--experimental` |
| `CLI --ignore-user-config app-server generate-json-schema --out <fresh-temp>/schema` | exit 2：未知顶层参数，解析阶段退出；没有服务启动或未知 RPC 结果 |
| `CLI app-server generate-json-schema --out <fresh-temp>/schema` | exit 0；离线静态导出，不加 `--experimental`，未发送 initialize 或线程请求 |

没有用更改配置、切换 HOME、登录、升级或绕过安全选项来解决参数差异。
也没有调用 `--print-startup-config`，以免打印私有配置。未来 E2B 必须在写入前重新
证明当前二进制支持所需禁工具/禁 MCP/hooks 的进程级设置；若不能证明则停止。

## 4. 官方契约与本机 schema 的对照

官方当前页面说明 metadata/history 读取、resume/start 与通知生命周期；这些接口
描述没有为本实验提供 Desktop UI 更新或跨进程排他写入的验收保证。
这是对已查阅文档范围的判断，不是断言所有产品版本均不支持。
[官方 App Server 文档](https://learn.chatgpt.com/docs/app-server)。

以下细节主要取自本轮本机生成的稳定 `ClientRequest.json` 和 `v2/*.json`：

| 接口/操作 | 本机描述及可检查的事实 | 分类与不可推断之事 |
|---|---|---|
| `thread/read` | 必填 threadId；includeTurns 默认不需打开全文；返回 Thread 含 status、preview、name、cwd、path、sessionId 等 | 语义只读，不 resume/订阅（O）；metadata 仍可能泄露私有内容，不能称安全匿名查询。本轮未调用 |
| `thread/turns/list` | threadId；cursor/limit/sortDirection/itemsView；itemsView 为 notLoaded/summary/full，默认 summary；data/nextCursor/backwardsCursor | 读取指定线程分页历史。future 用 notLoaded 先计数/核对状态；完整游标结束才可计数，重读 anchor 要去重。不是一致性快照、排他锁或 UI 状态 |
| `thread/items/list` | threadId；可限 turnId、cursor、limit、sortDirection；默认升序 | future 仅核对已批准测试 Turn 的合成输入/输出、工具项和内容摘要；不可用全局扫描找目标；摘要不是作者认证 |
| `thread/resume` | 必填 threadId；excludeTurns；可覆盖 model、cwd、config、sandbox、approvalPolicy、instructions 等；响应给有效配置和 history cursors | 潜在状态改变：加载 live session/配置和后续执行上下文；excludeTurns 不使它只读。可能涉及 MCP 初始化，不可作为探针。本轮没有调用 |
| `turn/start` | 必填 threadId/input；返回 Turn；有 clientUserMessageId、outputSchema、配置覆盖等 | 明确写操作及模型推理。parentTurnId/rootTurnId/turnTrigger 的本地说明明确提及请求可能加入或 steer 已 active Turn；ACK 不保证新增一个 Turn |
| `turn/started`、`turn/completed` | 本地通知描述含 threadId、Turn；还可有 item 流 | future 检查匹配身份、terminal status、真实输入与持久历史；completed 只是生命周期，不能推断 UI 已显示、科学 PASS 或执行许可 |
| `turn/steer` | required expectedTurnId/input/threadId | 写操作；有 active Turn 前提，但不是 `turn/start` 的 expected-idle CAS，不得作为 E2B fallback |
| `thread/inject_items`、revert、fork/start、archive/delete、metadata/name 更新、interrupt | 改历史、元数据、订阅/会话或执行状态 | E2A 全部不调用；E2B 主实验也不使用 inject/revert/修复 API |
| `thread/unsubscribe` | 改订阅/加载生命周期 | 不是纯读取；不能拿来“解锁”别人的线程 |
| `thread/attachmentOwner/list` | attachmentType/identityKey 反查附件所属线程；archived 明确不是执行状态 | 名称中的 Owner 不代表 Turn 写者租约，不能用于认领 Main；本轮未调用 |
| thread/list、loaded/list 等 | 可能列出线程身份/元数据 | 即便只读也超出本轮隐私范围；不得用于最近线程猜测或全局目标发现 |
| daemon/proxy、command/exec、shellCommand、process 类操作 | 服务/代理/执行面 | 不属于本次可行性探针；不存在借这些接口绕过同意或强制刷新 Desktop 的授权 |

本机 `ThreadStatus` 有 notLoaded/idle/systemError/active，但未实测其跨进程范围或
时效；一个客户端的 idle 不是另一个客户端不可写的证明。未发现本次稳定参数描述
提供 expected-idle、writer lease/fencing token 或 durable idempotency 的承诺。
`clientUserMessageId` 只有字段存在，不能推导服务端持久去重。此处结论是
**UNVERIFIED**，不是“源码保证不存在锁”。

版本差异：当前官方页面描述的 ReadOnlyAccess/restricted readableRoots 不在本机
稳定 SandboxPolicy 中；本机 readOnly 分支只有 type/networkAccess。文档的部分
permissions/historyMode 是实验能力，本轮没有导出或启用实验 schema。
本机 ThreadResumeResponse 对 disabledPluginIds 的描述还指出它不等于能力过滤；
仅设置该列表、approval=never 或在 prompt 写“不要用工具”都不能证明禁工具成功。
只读沙箱不阻止读取全部同用户可访问内容，也不意味着 Codex 推理服务无网络访问。

可复核的本机描述摘要（仅文件一致性，不是安全签名）：

| 静态文件 | SHA-256 |
|---|---|
| ClientRequest.json | `9b89e2459362d20cec67a429ef9430fe6b0e9fb8bd87d445d4c9a6acccd87450` |
| v2/ThreadReadParams.json | `dfe040c6ac71d30795b8be3f3ff232e66f362a37f883b491e5d1ea367f470db4` |
| v2/ThreadResumeParams.json | `8dceca415b2c16693b55658ea629cba5ffc82ac300dcd403db0ba7455e491496` |
| v2/TurnStartParams.json | `835e0d4ca1a0ddc4fb6db1e2b3249dd67f07c50ac2506092ba81543efc92829b` |
| v2/ThreadTurnsListParams.json | `2a8b93d7d4437cc25e16a1dde16d8db3c338d39e16c5eece2a56e943a21577d7` |
| v2/ThreadItemsListParams.json | `d5cf9784413f1d1abba756e04e48b273a9d12ab2c5675442e91b6a4ee55e19f0` |

## 5. Desktop 同步和所有权风险

四个指定 issue 及其评论本轮通过 GitHub 只读连接器重新读取，均显示 open。
它们是作者报告，不是 OpenAI 的支持承诺，也不是当前 Windows/build 的复现实测。
没有把公开帖中的会话 ID、日志或可执行复现代码复制进本报告。

| 公开证据 | 核对到的范围 | 本机含义 |
|---|---|---|
| [33650](https://github.com/openai/codex/issues/33650)，updated 2026-07-29 | CLI 0.144.5/Windows：外部 Turn 完成却未显示；后续作者澄清某些结果能被后续上下文或 mobile 看见 | 持久化、上下文、Desktop 渲染应分开验收，不能等同“会话数据丢失” |
| [21743](https://github.com/openai/codex/issues/21743)，updated 2026-06-15 | Windows Desktop+WSL、0.128 alpha；其他客户端评论涉及 remote 0.139/0.140，开放视图不刷新 | 本机 native Windows 并非同环境；不能照搬 WSL/socket 方案或假定 focus 必会刷新 |
| [30916](https://github.com/openai/codex/issues/30916)，updated 2026-07-02 | Desktop 26.623.81905：外部新建线程在已启动 Desktop 中可搜索却不打开；作者撤回早先 threadSource/CLI版本因果解释 | 新外部线程的登记/打开问题，和已有 Desktop 线程的 live refresh 是不同实验；本轮不重启 Desktop 验证 |
| [45194](https://github.com/openai/codex/issues/45194)，updated 2026-10-27 | 重叠 start、服务端返回已有 Turn 与 UI provisional Turn 失配；后续 Windows/macOS 报告有更近构建，部分是离线模拟或未捕获原触发条件 | 同一 Turn 的多个 ACK 不能当成多个独立完成；不能据 open 状态断言本机仍有 bug，也不能据版本更高断言已修复 |

主要风险：

1. **存储与通知分离**：共享有效 HOME 可能让两客户端读到同一历史，却不提供 live
   event fanout、renderer invalidation、sidebar 索引或 stream ownership 同步。
2. **所有权竞态**：人工停止输入与 idle 检查降低风险，但两次检查间存在 TOCTOU；
   自动化、mobile、第二客户端仍可能启动。无 fencing 的顺序实验不证明并发安全。
3. **状态看似成功**：ACK、terminal、历史、当前 UI、重开后 UI、composer 可用性可能
   不一致；模型称“我已看到”也不是 UI 证据。
4. **权限和保密**：shared HOME 可能带入指令、MCP、hooks、授权与默认工具；隔离 HOME
   是独立 CLI 对照，却不测试 Desktop 同步，且可能没有认证。不得复制凭据来补齐。
5. **恢复风险**：UNKNOWN 不证明未执行；禁止重发、替换线程或编辑 session 索引。
   退出测试客户端也不能证明远端已经取消；只关闭本轮自有句柄，保留不确定结果。
6. **版本漂移**：同版本字符串、更新状态或 process 名称不能证明协议/部署/配置等价；
   核验 exe 摘要、稳定 schema、有效安全设置后才讨论 E2B。

## 6. M03-E2B：单个可丢弃 Desktop 线程实验设计

**DESIGN ONLY；以下操作本轮均未执行。** E2B 首先是人工观察的顺序互操作实验，
不接 GD-CAE 真实事件、不创建自动调度器、不执行 B、不修改 ResearchProject 或预算。

### 6.1 必须写入下一轮审批的内容

审批分三道，不能以本审计 PASS 自动获得：

1. **准备/只读身份门**：用户手动在全新、非敏感空目录建立一次性 Desktop Project
   和新线程，写一条合成 seed 并等待完成。允许一个明确定义、短时的自有 STDIO
   App Server 测试客户端；明确使用与测试 Desktop 相同的有效 session 环境，但
   不改变全局配置、HOME、认证和现有线程。只访问用户确认的那一个测试线程。
2. **resume 门（如协议需要）**：单独允许至多一次对这个测试线程的 thread/resume，
   限定 per-process/该线程安全设置。说明它不是读取；若会激活无法禁用的插件、
   MCP、hooks 或其他能力，停止，不执行 start。不能把 resume 夹在 baseline 查询里。
3. **唯一写入门**：在 baseline 一致、有效工具权限已证明、用户再次确认无并行输入后，
   才允许一次纯文本 Codex LLM ACK 推理和所需模型服务通信。taskbook 的“no model
   execution”若也包括 LLM 推理，则与 turn/start 实验矛盾，必须 BLOCKED；下一轮
   审批应明确“仅允许这一次 Codex 文本推理，禁止 CAE/研究模型与所有工具执行”。
   正常重开、可选 composer 消息和任何中止 RPC 也必须分别授权，不能默认获得。

基础实验的显式 LLM 额度是人工 seed 一次、外部 ACK 一次；若另行批准 composer
复验才再允许一次人工消息。不是 seed/ACK 无限重试，也不是发现失败后换线程重做。

不提供未经当前 schema/配置验证的可直接运行脚本。先确定受支持的配置方法能使
shell、执行、文件写入、web、MCP、apps/plugins、skills/hooks 和其他工具不可用；
prompt 约束和只读沙箱不足以替代这一检查。若必须更改全局设置或当前二进制不支持
安全配置，记录 `BLOCKED_SAFE_PROFILE`，停在写入前，不做降级试验。

### 6.2 身份、隐私和基线

- 用户通过受支持的单线程 UI 身份导出/复制方式确认测试线程；若无安全方法，则
  `BLOCKED_TARGET_IDENTITY`。禁止 thread/list、读取 session 文件、按最近时间或
  名字猜测。操作者也明确区分原开发 Main 与这个新测试线程。
- 在新 TEMP 中用限制 ACL 或加密的 manifest 保存真实测试 thread/Turn 映射、审批、
  exe/schema/config 摘要和有效期；先验证权限再写身份。报告只写 `REDACTED` 或
  独立随机审计引用，绝不输出完整/部分 ID、带 ID URL 或用 ID 本身的 hash 作替身。
  不能把同用户 ACL/加密描述成防恶意同用户的 OS 隔离。
- 人工确认 Desktop 无 active Turn、无 typing/queued 输入；确认已知 mobile/其他
  客户端和自动化不操作此测试线程。不能建立操作者排他约定时停止；不声称有技术锁。
- 先观察 UI seed、Turn 数和合成文本、时间，再经支持的只读 API 对唯一已确认线程
  分页核对。限制两页、每页至多 10 项，数据/历史超界即停止；itemsView=notLoaded
  先检查数量/状态，仅针对 seed/新 ACK 取有界 items。baseline 应只有已批准的 seed。
- 两侧历史不一致、含非合成内容、target/source/store/cwd 不确定、active/systemError、
  missing history 或任何身份歧义，都不允许进入 resume/start。notLoaded 也不是
  “别处没有 active Turn”的证明。

### 6.3 一次性提交与观察

1. 记录不可自动重放的本地 `TURN_START_INTENT`：审批引用、测试线程绑定、基线
   Turn 集合、合成请求摘要、exe/schema/config 摘要、到期时间、一次调用额度。
   时间与 hash 用于审计，不是可信签名。把检查与调用间竞态列为残余风险。
2. 在已批准的工具禁用配置下，以独立随机、非身份派生的测试标记发一个简单纯文本
   ACK 请求，使用受限 outputSchema；不发送 toolOutput、不引用文件、不要求工具。
   同时将实际 request/response/notification 留在受保护 TEMP，仅对外输出脱敏摘要。
3. 至多调用一次 turn/start。若返回旧 baseline Turn ID、出现重叠输入/自动 steer，
   记 `CONFLICT`，不能把 ACK 当新 Turn 成功。超时、连接断开、容量失败或应答丢失
   一律 UNKNOWN；无第二次 start、无随机替代线程、无自动恢复当前 Main。
4. 建议单次观察上限 180 秒；超限标 UNKNOWN。只允许在原测试身份上有界只读核对
   notification 与持久历史。缺失不是未执行证明；只有唯一匹配的已完成新 Turn、
   输入/输出与无工具证据可使 B 通过。
5. 人工观察已打开 Desktop 视图 30 秒（C），再做一次安全 focus 切换并单独记录结果；
   不把 focus 后可见算成自动实时可见。若会话出现 stale/歧义，主实验停止；仅在
   预先单独批准时正常重开一次测试线程观察 D。禁止强制 reload、重启/杀 Desktop、
   私有管道、raw JSONL/DB 修复、inject/revert 或反复 start。
6. E 的无额外写观察只检查 UI 非 busy/无错误、composer 控件状态，标为 OBSERVED_ONLY。
   若要证明可发消息，另行批准一条人工纯文本消息，明确它额外调用一次 LLM，计入
   单独额度；不占用/重放外部唯一 start，不得把“没有点击”记成 composer 成功。
7. 关闭并 await 自有测试客户端；不触碰 Desktop 后端或其他进程。不确定请求继续保留
   UNKNOWN。放弃可丢弃线程是恢复边界，不删除/回滚其历史，更不影响原开发 Main。

### 6.4 六个独立验收维度

| 维度 | 未来 E2B 证据 | 不能替代的证据 | 本轮 |
|---|---|---|---|
| A Protocol acceptance | 一次 RPC 的明确响应、匹配测试身份/Turn；丢失则 UNKNOWN | 不能证明新建、持久化或 UI | NOT_TESTED |
| B Persistence | 完整有界分页，baseline+恰好一个新 completed Turn，合成标记/内容吻合，无工具项 | 单一 ACK/模型自报不足；不能证明 C | NOT_TESTED |
| C Live visibility | 人工在原已打开视图看到对应新 Turn，未 focus/reload；记录延迟 | focus 后可见单列，不算 C | NOT_TESTED |
| D Reopen consistency | 单独获准正常重开后，UI 内容与 B 对齐 | 不替代 C，不以重启 App 代替 | NOT_TESTED |
| E Thread usability | 无孤立 pending/busy/错误；可选获准人工消息完成才标 MESSAGE_TESTED | composer 看似可用仅 OBSERVED_ONLY | NOT_TESTED |
| F Concurrent safety | 需另行批准有界冲突测试、可观察所有权契约及故障证据 | 顺序单次成功和 idle precheck 均不足 | UNVERIFIED |

禁止将 A–F 合并成 `DESKTOP_RESUME_PASS`。A/B 成功但 C 失败应明确标注
“外部执行/持久化通过，Desktop live visibility 未通过”。任何 E2B 顺序实验
都不能把 F 改为 PASS，也不能授予真实科研或生产 Main 的自动续 Turn 权限。

## 7. 两种 Main 架构的独立比较

| 维度 | A：Desktop-owned Main | B：GD-CAE-owned persistent CLI/App Server Main |
|---|---|---|
| 用户体验 | 理想情况下一个连续可见的对话 | 明确自有研究 Main，另设只读状态/决策 inbox；不承诺自动进 Desktop sidebar |
| 所有权 | 依赖 Desktop 与外部客户端支持的写者/同步契约，目前 U | 可设计一个明确自有 adapter 作为唯一提交者，其他客户端只读；仍需工程实现和故障测试 |
| 已有证据 | 当前只验证版本/静态描述，没有 Desktop 写入实测 | H：E1 一次自有测试线程事件 ACK，不是多轮生产服务 |
| 风险 | renderer stale、sidebar 注册、双客户端 active/start 冲突、隐式能力与 UI 歧义 | 用户干预交接、inbox、留存/隐私、长连接生命周期、容量中断、UNKNOWN 阻塞 |
| 准入条件 | disposable 线程 B/C/D/E 独立验证；并发/同步契约另证；再申请真实事件集成 | 另立里程碑评审单写者生命周期、人工停机/接管、受控权限、预算及审计；现有 E1 不自动扩权 |
| 当期决策 | DESKTOP_INTEGRATION_UNVERIFIED，仅保留后续实验路线 | 推荐近期产品方向，面向未来无人值守场景；当前不实施/不宣称可生产运行 |

改变推荐所需证据：本机精确版本上可重复的 B/C/D/E；明确受支持的跨客户端同步及
所有权/冲突语义，足以避免两个写者争用；另行批准后才连接 GD-CAE 事件。
即使测试线程成功，也不能推定原开发 Main 可安全接入。

未来事件桥仍可沿用 committed-event → durable intent → narrow Codex port →
只读证据核对的权限分离。不得因 UI 互操作而授予 AF Grant、Solver、Candidate B、
预算写入或科学验证权；不建立第二套 Agent harness。保持 E1 UNKNOWN 保守策略、
STORE_BUSY 不自动修复、无跨系统 exactly-once 的限定。

## 8. E2A 验收与独立复核

| ID | 审计结果 | 证据/限定 |
|---|---|---|
| E2A-01 | PASS | 指定 main/HEAD/parent、tracked clean/index empty；无提交 |
| E2A-02 | PASS_WITH_UNKNOWN | CLI/Windows实测；Desktop tool-reported，About UI UNKNOWN；实际会话 backend/transport未握手 |
| E2A-03 | PASS | 本机稳定 schema 对照当前官方文档；记录参数拒绝、read-root 与实验字段差异 |
| E2A-04 | PASS | 逐方法分类，resume/start/inject/订阅变更不当作只读 |
| E2A-05 | PASS | 独立复核可见操作：无线程枚举/现存 Main API/私有会话文件访问；报告不含真实会话身份 |
| E2A-06 | PASS | 独立复核操作清单：无 Desktop write/resume/session edit/UI automation；仅官方静态导出 |
| E2A-07 | PASS | 人工创建全新 disposable Desktop 线程，不能选择原 Main |
| E2A-08 | PASS | 同有效环境待单独批准；隔离 HOME 仅 CLI 对照，不等于 Desktop 同步 |
| E2A-09 | PASS | 三道批准门、身份/能力/idle/并发歧义停止、UNKNOWN不重发 |
| E2A-10 | PASS | A–F 独立，focus 与 live、观察与composer写验证分别记录 |
| E2A-11 | PASS | 四公开 issue/评论按版本和报告来源解释，无本机bug断言 |
| E2A-12 | PASS | 明确暂选B方向；A所需新证据与B当前成熟度限制已列明 |
| E2A-13 | PASS | 既有源码/测试/接口/权限不改，E1限定保留；无AF/Abaqus |
| E2A-14 | PASS | 独立全文/schema摘要复核及文档隐私/空白检查通过；tracked/index无变化，仅新增本报告 |

独立 Reviewer：`/root/m03e2a_review`，仅只读评审，不操作 index、不运行服务。
初审已提出并纳入：LLM执行措辞冲突、resume需独立许可、idle检查TOCTOU、
版本工具自报与UI核验区别、metadata仍有隐私、B不等于现成生产自主系统。
最终审阅无 BLOCKING，支持限定 `M03E2A_READONLY_FEASIBILITY_PASS`。Reviewer
独立核对了六份 schema 文件摘要与关键字段、完整 14 项矩阵、Git 基线和隐私模式。
NON_BLOCKING：Desktop 仅 tool-reported、当前操作范围无法提供系统级法证；这些限制
已显式列明。RESIDUAL_RISK：并发锁/UI同步/有效禁工具配置仍需未来实证；共享HOME、
UNKNOWN、同用户隔离及E1生产成熟度限制没有因本次文档验收而消失。

实际文档检查：14 项验收行、5 个 HTTPS 来源链接；UUID 形状、具体用户私有路径、
高置信凭据模式匹配均为 0。`git diff --exit-code` 和 cached diff 均为空；新增
文档 `git diff --no-index --check` 无空白诊断（只有 text=auto 的 LF/CRLF 提示）。
未跟踪文件恰为旧审阅补丁与本报告，HEAD 仍为冻结 Checkpoint。补丁元数据保持
上述长度/时间，未读取其内容。未生成新的长期服务，静态 CLI 命令均已退出；原有
Desktop 后端没有被连接、关闭或重启。本轮不重跑 pytest/Ruff，因为无源码或测试
改动；历史回归结果不冒称本轮测试结果。无暂存、提交、推送、fetch 或 CI。

独立确认的边界应限于本轮可见操作清单、静态证据及 Git/文档复核，不能冒称全系统
法证或证明其他进程从未改变状态。旧证据与私有材料均保留，不清理。

**停止：不开展 E2B 线程创建、读取、resume、Turn 写入或任何 Desktop 联调。**
