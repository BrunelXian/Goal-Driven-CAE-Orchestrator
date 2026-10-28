# M01-C — Codex Read-Only Research Interface

日期：2026-10-28。授权范围：M01-C 任务书；仅 GD-CAE 本地实现、离线测试及全新 TEST_ONLY/Fake 场景。

## 结论与验收标签

**PASS — 在已验证的 Codex CLI 表面完成 M01-C。** 原 Desktop Main 热加载及自动继续不在此结论内。

| 独立标签 | 结果 |
| --- | --- |
| MCP_CONTRACT_PASS | true |
| CODEX_MCP_READ_SMOKE_PASS | true |
| CODEX_NATIVE_DELEGATION_PASS | true |
| SCIENTIFIC_VERIFICATION_AVAILABLE | false |
| AUTO_CONTINUE_ORIGINAL_DESKTOP_MAIN | NOT_TESTED |

最终离线测试 231 passed、2 skipped；三个显式 live 场景各 1 passed，前两次的 UX
限制另行记账，不能将测试函数退出码视为完整 UX 成功。最后一次有可核查的原生
专业角色元数据、独立 MCP 读取、结构化返回及 Main 汇总，且全部测试 Owner/transport
已通过持有的 Windows 进程句柄证明退出。没有进入 M02。

## C0 环境、基线与权限

- GD-CAE：`main`，HEAD `af3cfd90821cddf65ef93827a20fc2b26d98f0fc`；没有切换分支、暂存、提交或推送。
- AF Develop：HEAD `7f4b8d8f3a2c862ed8b244d495295f5d51ea0d88`；前后仅检查 tracked status，均无改动。未扫描历史未跟踪资料。Stable 未访问。
- 按全局登记使用绝对解释器 `D:\XianLab\envs\LangChainEnv\Scripts\python.exe`，Python 3.12.10 x64；MCP 2.3.0、AnyIO 4.13.0、Pydantic 2.13.4、pytest 9.1.0。没有安装、升级、降级或修改环境。
- Ruff 使用现有独立工具 `D:\ProgramData\anaconda3\Scripts\ruff.exe`。Codex CLI 为 `0.165.0-alpha.1.2`。
- SDK 2.3 的 `FastMCP` 旧入口明确拒绝导入；采用其官方 `mcp.server.lowlevel.Server` 与 `stdio_server`，没有自行实现 JSON-RPC/MCP 协议。
- 已阅读全局/AF AGENTS、环境登记、M01-A/B 报告、ADR-003/004、现有契约和桥、完整 M01-C 任务书。使用 openai-docs、skill-creator 技能；专业角色和安全测试由职责分离的原生开发子 Agent 完成。
- ADR-001/002、冻结基线、ADR-003/004、README 和原有桥/契约均未改写；新接口的权限依据是本次任务书，未把历史 ADR 的阶段限制悄悄改成全产品授权。

保留的 SHA256：

| 文件 | SHA256 |
| --- | --- |
| README.md | `EBE31922B1AC9914880DFCF4E2D99CAA36AEBB322300F74606D4A5171B8661CE` |
| adapters/abaqus/af_evidence.py | `8B7A1CDD57DD0D4A067BC32037AC8893AA1662348F9D94BAEC01B34E670A88B0` |
| contracts/af_evidence.py | `401ECB551591376F854247B7E64CC4D13F82CD54C17C098BDBA2B26943D5F012` |

## 实现与变更路径

| 路径 | 变更 |
| --- | --- |
| `src/aegiscae/interfaces/mcp_read.py` | 一个官方 SDK STDIO Server，七个固定工具、严格参数、启动绑定、TEST 门禁、脱敏和聚合限长 |
| `.agents/skills/gdcae-evidence-review/SKILL.md` | 一个只读证据审查 Skill，禁止证据到科学结论的越权转换与 shell/database fallback |
| `.codex/agents/gdcae_evidence_analyst.toml` | 专业证据分析角色；仅三项规定字段，继承 Main 模型和权限 |
| `.codex/agents/gdcae_independent_reviewer.toml` | 独立质疑角色、来源核对及结构化返回；不充当确定性数值 oracle |
| `docs/architecture/M01-C_READ_INTERFACE.md` | 可移植配置模板、研究者使用流程、边界及实际 CLI 限制 |
| `tests/unit/test_mcp_read.py` | 66 项 MCP/SDK/schema/安全与角色文档测试 |
| `tests/unit/test_mcp_cleanup.py` | 5 项清理失败注入测试 |
| `tests/integration/test_mcp_read_live.py` | 默认跳过的全新 Fake fixture、STDIO/CLI 验收与收尾证据 |
| `tests/architecture/test_package_skeleton.py` | 仅开放确切 MCP 源文件；第二 Server 负例保留 |
| `tests/architecture/test_dependency_direction.py` | 仅该文件可导入公开 EvidenceBridge；私有 helper/旁路负例 |
| `tests/architecture/test_forbidden_surfaces.py` | 仅列明的官方 SDK 类型；禁止任意客户端、第二框架和其他位置导入 |
| `.gitignore` | 唯一新增 `/.codex/config.toml` |
| `docs/milestones/M01-C_DELIVERY_REPORT.md` | 本报告 |
| `docs/milestones/M01-C_SOURCE_DIFF.patch` | 上述本轮变更的审阅补丁，排除本机配置与既有 M01-B 文件；未执行 git add |

本轮开始前已有的 `docs/milestones/M01-B_DELIVERY_REPORT.md` 与
`tests/integration/test_af_read_live.py` 仍未跟踪且未修改。后者仅作为可信 fixture
辅助函数的源码复用，未执行其 M01-B 场景或访问其旧临时目录。

本机 `.codex/config.toml` 为本轮创建并被精确忽略的活绑定配置，不含凭据；不作为
可移植源文件交付。现有全局配置未改写。各场景只在本轮创建的配置字节 SHA256
完全匹配时允许切换至新的显式测试绑定，不覆盖未知用户配置。

`git check-ignore -v` 确认原有 `/Kickoff_Docs/`、`/CAE models/` 仍分别在第 32、33
行生效，新规则位于第 34 行。未读取 CAE models 内容，未解除其他路径跟踪。

## MCP 契约与权威边界

仅暴露 `gdcae_capabilities`、`gdcae_list_runs`、`gdcae_get_run`、
`gdcae_get_receipt`、`gdcae_list_events`、`gdcae_get_validations`、
`gdcae_get_diagnostic`。官方 SDK 实际枚举也精确等于该集合。

启动输入为绝对路径的、最多 8 KiB 的 JSON，包含 operator 的 `test_only=true`
声明和冻结 ProjectBinding。工具不能接收 root/server/owner/credential 切换参数；
多余字段和类型强制转换均拒绝。启动与每次请求要求 simulation=true；实际读取
再次经过现有桥的 Project/instance/context/owner 核验。没有缓存未经验证的新 Owner。

接口只调用现有七方法；没有原始 `call` 转发、AF Store 直连、发现备用项目、启动
Owner、提交、Grant、恢复、导出或执行写接口。返回保留 `gd-af-read-v1`、read_at、
source_read_at、source、consistency、completeness、原始游标和 typed error。
文本与 structured content 两份数据一起计量，261120 字节上限预留 1 KiB SDK
JSON-RPC 包装；桥原有原始消息、节点、深度上限仍有效。

官方 SDK 拥有协议/STDIO 并发；GD-CAE 未实现后台线程、轮询、网络监听或第二套
Agent loop。默认 OTel middleware 被显式关闭。诊断、参数错误、序列化失败不回显
凭据、异常字符串或私有文件路径。未知/缺失不是空成功；COMPLETE/FINISHED 不是
科学 PASS；诊断中的 digest_verified/artifacts_revalidated 仍为 false。

## 测试方法与失败记录

最终离线命令（PowerShell，设置 PYTHONDONTWRITEBYTECODE=1、PYTHONPATH 为本仓库 src）：

```powershell
& 'D:\XianLab\envs\LangChainEnv\Scripts\python.exe' -B -m pytest -q --tb=short --basetemp=<全新UUID临时路径>
& 'D:\ProgramData\anaconda3\Scripts\ruff.exe' check src tests
git diff --check
```

**231 passed、2 skipped，4.10 秒；Ruff PASS。** 两项跳过为默认禁止启动的
M01-B 和 M01-C live 测试。架构测试 98 项；原桥测试与 package import 测试保持有效。
Skill 的 quick_validate.py 通过，两份 Agent TOML 解析通过。

离线不仅调用 Python 方法，还通过官方 SDK 内存传输执行 initialize/tools/list/
tools/call。包含七工具映射、来源重验、逐次 TEST 标志变化、门禁后 Owner 变化、
未知项目/旧格式/离线、错误游标/限额、最终双份输出超限、恶意嵌套数据、原始协议
参数不回显、纯导入/失败启动无副作用、真实失败启动 stdout 为空且 stderr 固定。
识别的冲突 FINISHED + NOT_RUN + simulation recorded FAIL 分别保留，不合成科学结论。
清理测试证明凭据删除、harness.close、退出观察、ref.close 失败仍尝试剩余收尾，
记录 PARTIAL 和固定错误标签。

开发中曾出现：默认 pytest 临时目录权限错误（改用新 UUID basetemp，未清理旧目录）；
测试对 PROJECT_IDENTITY_MISMATCH 的期望集合遗漏；新增逐次 TEST 门禁后的 discovery
计数尚未迁移。均修正后全套通过；没有通过删减安全断言规避问题。

每次 live 命令单独运行 `tests/integration/test_mcp_read_live.py -q -s --tb=short`，
显式设置 `GDCAE_M01C_LIVE=APPROVED_TEST_ONLY`、新的 `GDCAE_M01C_ROOT`、
审计过的 `GDCAE_AF_SOURCE`、绝对 `GDCAE_CODEX_EXE`，已有本轮本机配置则传其确切
SHA256。无安装，无生产连接。源代码中记录安全预检与每场景最多一次 Owner 启动。
结束时本轮创建的本机 MCP 配置被置为 `enabled=false`，保留停止后的绑定作审计，
避免后续会话自动尝试该失效测试连接；未改全局配置。

## 真实场景与 Codex 调用证据

所有场景均使用全新 TEMP 子目录、可信 ProcessHarness 的 fake-v1 后端，
native health 确认 TEST_ONLY、simulation=true、无 process fixture/Standard 扩展。
空 Run 阶段经官方 STDIO 客户端调用全部七接口；四种目标缺失响应为 NOT_FOUND。
随后只有 fixture 准备阶段提交 3 个合成 Run，自动生成 3 个 simulation Validation、
12 条事件；这些准备写入不属于 Evidence Bridge/MCP 读取。

读阶段比较 16 张业务表的行数/内容哈希、Run revision、event sequence、gate、slot。
Run 分页 2+1；事件过滤空页仍返回 more_possible=true、position=2，继续得到余下
10 条事件至 sequence=12。没有 validate_run、管理 Grant 或真实求解器调用。

| 场景 | 结果与说明 |
| --- | --- |
| `gdcae-m01c-live-c46aca6a7d364ebc9965ba93ce05c750` | 真实 STDIO/AF 通过，CLI 配置路径失败；40.94s，pytest 1 passed 仅代表测试流程与收尾，UX 为 PARTIAL |
| `gdcae-m01c-trusted-de71deedf09a4197bd6b76e621043ae1` | 正常项目配置后 Main 七工具成功；220.984s 场景，222.80s pytest；临时会话初次 native fork 失败，重试后 Main 报告 Reviewer 返回，但不单凭此声明最终委派 PASS |
| `gdcae-m01c-persistent-b22a7d22428c47f3a9ba46c93ccff35a` | 全链路与原生委派通过；426.563s 场景，428.54s pytest；证据见下文 |

第一场景 `exec --ignore-user-config` 未暴露项目 MCP；只读诊断正常配置路径明确加载
gdcae_read 并对已退出 Owner 的旧绑定 fail closed。第二场景 `--ephemeral` 导致
`no rollout found` 的首次 context fork 错误。最终脚本采用正常可信项目配置和正常
会话持久化，继承用户配置的 Main 模型；不以修改全局设置解决问题。

session-local `mcp_servers.node_repl.enabled=false` 仅限制该次调用。配置清单中另有
cua_repl 等用户/内置连接；没有声称删除它们。实际证据调用只使用 gdcae_read。
Main 唯一 shell 证据是读取 Skill 文本，不用 shell 读取 AF 数据。

第二场景 Main 有 17 次 MCP 调用：16 次成功，1 次超限 `list_events(limit=100)`
被服务拒绝 INVALID_REQUEST；Main 随后改用合法限额。它实际完成 2+1 Run 分页、
带筛选的空事件页续读至 more_possible=false，明确拒绝“Fake FINISHED 证明物理
模型和科研目标”的断言。输出中的记录均带 source/读取时间，非原子性未被隐藏。

最终 Main ID：`01a1809f-3f95-7051-a3ae-ec3cf69c2897`。
原生 spawn call：`call_84a9d1eef714417dbc9b4f5df495e16f`；
`agent_type=gdcae_independent_reviewer`，`task_name=m01c_independent_review`。
子会话 ID：`01a1809f-e961-7d53-9a5d-8da90a034449`；其 session metadata
明确记录上述 parent_thread_id、depth=1、agent_role 和 `/root/m01c_independent_review`。
这些字段直接来自本轮新建的原生 rollout，不是 Main 的口头声称。

最终 Main 调用 12 次 MCP：11 次成功，1 次非法事件限额被拒绝。七种工具均有成功
调用：capabilities `item_2`、list_runs `item_3/5`、get_receipt `item_4`、
get_run `item_6`、get_diagnostic `item_7/11/12`、get_validations `item_8`、
list_events `item_10/13`。Native Reviewer 自己成功调用 10 次，覆盖同样七种工具，
Run 分页 2+1、事件 1–12。独立读取发生在子会话自身 item_completed 事件中，
没有把继承的父会话历史计为其工作。

Reviewer 的最终 `AgentMessage`：
`msg_09b5371d7bc2a5a3016ae171f136b48199bffb31927501f688`，phase=final_answer；
结构化结果包含角色、task_id、Project/instance、observed_run_ids、evidence_refs、
findings、conflicting_facts、unknowns、proposed_next_read、status=REVIEW_COMPLETE。
三条 Run：`r_4ee93b2e56904a08a26dd73d93d07792`、
`r_3df6680e55894b27a892d9a952c5eb86`、`r_9ca4b1652cea48a4a5bd3259af11c025`。
其 diagnostic read_at 分别为 1793159658081、1793159658249、1793159658365；
source_read_at=1793159658。Main 的最终汇总实际引用了这些独立读取。

Reviewer 拒绝物理验证断言，指出 simulation 范围、NOT_RUN、未重验 artifact/digest、
缺失时间与非原子读取，并保留其不知道的变化原因。它提出诊断 digest 改变的疑问。
只读源码复核进一步确认 AF `execution/diagnostics.py:396` 把 view.read_at 纳入 body，
`:406` 对整个 body 求 digest，因此读时刻变化就足以改变该报告 digest；这不证明
业务数据被修改，也不证明 artifact 完整性。16 表前后哈希相同提供另一个独立的
业务状态不变证据。没有据此设置 digest_verified=true。

Evidence Analyst 文件只验收了配置解析/角色定义；本轮实际专业委派使用 Independent
Reviewer，未声称两名专业角色均进行过实测。创建代码和审查安全的开发子 Agent
也不作为该产品 UX 验收的替代。

最终场景 `audit-summary.json` 的独立复核断言：Main 成功工具集合精确等于七工具；
Reviewer 自身成功集合也相同；parent/agent_role/instance/owner 匹配；结构化返回
REVIEW_COMPLETE 且 scientific=false；两个读阶段无业务变化；清理无错误且退出码均 0。
原始测试 evidence.json 保留 PENDING_AUDIT 阶段标签，后续审计结果单独保存，不改写
原始运行证据。该文件仅在本轮新临时目录内，不是 MCP 读取的导出副作用。

| 最终证据文件 | SHA256 |
| --- | --- |
| evidence.json | `2d11a6955553f8e45710a054b9d2c2d4a1616af0160833d653fa7714ebe461b6` |
| codex-main.jsonl | `d3ea8eeebeb7aa129bdd4c21b84cf7d1cdf8479577a903d1c05f6fd0e5cb31b5` |
| Main 原生 rollout | `615596371665cb82cd9772acce61aa67a1d13dc7336ec92cd5d2eb2a893e6950` |
| Reviewer 原生 rollout | `33fc6d8695a20b1b8307d8bad270fdb2270681bbc93e7e2fb67302fbc13fb7bc` |

原生 rollout 位于本机 Codex sessions 的 2026/10/28 目录，按上述会话 ID 精确定位。
仅检查本轮新会话；未将不相关聊天或原生加密 prompt 复制到交付文件。网络 idle timeout 曾由 Codex
自身重连一次；这不是 AF Owner/任务执行重试。原 Desktop Main 自动继续仍未测试。

## 业务状态、进程与凭据收尾

最终场景空/非空读阶段均无变化；非空基线：runs/plans/grants/receipts/validations/
observations/consumption 各 3，events=12，Run revisions=[4,4,4]，gate=[OPEN,2]，
slot=None，management_grants/management_receipts/control_events/reconciliations 均 0。
这些计数及全部 16 表内容哈希在 Main 与 Reviewer 读取后完全相同。

| 场景 | Owner PID / creation_time_100ns | Transport PID / creation_time_100ns | 退出 |
| --- | --- | --- | --- |
| 配置诊断 | 19476 / 134376323233808032 | 34588 / 134376323233329160 | 两者 exit_code=0 |
| 可信配置临时会话 | 10932 / 134376325534710339 | 36280 / 134376325534069775 | 两者 exit_code=0 |
| 正常持久会话 | 13700 / 134376328753015343 | 6500 / 134376328752677686 | 两者 exit_code=0 |

六条证明均来自 retained_windows_handle；三次 lifecycle 均 actual_process_handle_signaled，
未使用 PID 名称清理、接管、强制终止或未知启动重试。每个场景在前一场景退出已确认后，
使用全新目录启动一次 Owner。新场景的创建不复用 M01-B 资料或前一场景凭据。

每次 fixture handoff 的 connection.json 在 harness 凭据清理审计前移除；bootstrap
和 private-process 文件由可信 harness 清除，剩余 fixture 文件中凭据字节不存在。
第二、三场景还在凭据尚在内存时核对 Codex JSONL/stderr、empty/seeded MCP stderr
无凭据。MCP 成功输出保留 safe DTO，错误无私有路径/原始异常。合成业务记录和
不含凭据的 binding、测试报告、Codex 会话记录留存，不擅自清理用户资料。

零 Solver 的依据：native health 仅 fake-v1；process_config=None；fixture owner
的 launch_and_legacy_traps=true、fixed_process_launch_whitelist=false、
all_confined=true、all_data_accesses_confined=true；harness 末尾确认无 INP/CAE/ODB/JNL
产物，且桥/接口无执行入口。没有使用 Abaqus 2024/CAE/noGUI/ODB 命令。

## C-01～C-14 验收矩阵

| ID | 结果 | 证据与限定 |
| --- | --- | --- |
| C-01 | PASS | SDK 内存及真实 STDIO tools/list 精确七工具，严格 schema，固定桥方法 |
| C-02 | PASS | 启动冻结绑定；extra 字段拒绝；同身份 TEST 状态变化与陈旧游标负例 |
| C-03 | PASS | 公开 seam 单一路径；私有 Store/生命周期/任意执行静态负例；fixture 独立准备 |
| C-04 | PASS | 保留 DTO 来源/时间/游标/unknown，原始与双份输出上限，空过滤分页实测 |
| C-05 | PASS | 三场景空/非空读取前后 16 表及 revision/sequence/gate/slot 不变 |
| C-06 | PASS（测试范围） | 投影/错误 sentinel、真实凭据比较、MCP stderr、CLI 日志与 fixture 留存审计 |
| C-07 | PASS | 导入及失败启动无 AF 进程/文件写入；成功启动只附着现有 Fake Owner |
| C-08 | PASS（CLI） | Main 实际读取项目 Skill，遵守来源、分页与科学不确定性规则 |
| C-09 | PASS（CLI） | 原生 spawn 指定专业角色，父子 metadata、10 次独立 MCP 读取、结构化返回与 Main 汇总 |
| C-10 | PASS | Main/Reviewer 均否定 Fake FINISHED→物理/Goal；scientific=false |
| C-11 | PASS（限定） | 未知/缺失/冲突/注入离线测试，真实非法限额被拒绝并保留 UNKNOWN 语义；不是通用 LLM 安全证明 |
| C-12 | PASS | 三 Owner 与三 transport 均持有句柄退出码 0；本轮凭据清理证据，未动旧资料 |
| C-13 | PASS | 231 offline pass/2默认 skip、三 live 流程、Ruff、diff-check、冻结与原桥守卫 |
| C-14 | PASS | 无真实 Solver/ODB/生产 Project、AF 修改、环境变更、Git 提交/推送或 CI |

## 风险登记

| 风险 | 本轮处理与限制 |
| --- | --- |
| 同一 Windows 用户 | 七工具/角色指令不构成恶意同用户 OS 隔离；AF 凭据本身并非只读凭据 |
| TEST 资格投影有限 | startup 的 test_only 为 operator 声明；桥只公开 simulation。TEST_ONLY/fake-only 通过可信 fixture native health 另行验证，未将此冒充一般部署的强制隔离 |
| Fake 非物理证据 | 无 Abaqus/CAE/ODB、无独立数值/物理/Goal 验证；LLM Reviewer 不是数值 oracle |
| 非原子分页 | 每次读取核验身份，分页仍非全局快照；事件筛选空页不等于结束 |
| Prompt injection | 原始任意字符串被投影移除，恶意嵌套/未知状态/矛盾状态测试通过；模型层仍需遵守不可信数据规则 |
| SDK/CLI 版本差异 | 已核对实际 2.3 API；不兼容 flag 行为及 native ephemeral 问题已记录；不能推定所有客户端热加载相同 |
| 输出与输入边界 | 约束工具输入及聚合结果；任意畸形传输帧/超大 JSON-RPC id 仍属官方 SDK 协议边界，不宣称网络暴露安全 |
| 临时凭据与记录 | 本轮 handoff/bootstrap/process 凭据仅按本轮生命周期清理；合成业务证据、配置、CLI/原生记录留存，包含研究上下文 metadata，需后续用户决定保留策略 |
| M01-B 留存 | 仅从 M01-B 报告记录旧 G1 加密生命周期/operator/connection 文件保留风险；未打开、复用、传播或删除其临时资料 |
| 超时和后代进程 | 测试 CLI 超时分支只能终止直接持有的 CLI；不能据此证明所有 MCP/native 后代退出。AF Owner/transport 另用持有的 Windows handles 核验 |

## M02-A 建议（未实现）

下一阶段建议先形成独立审查的 ResearchProject 最小持久状态及冻结契约，再考虑
任何执行写入口：Project identity/version、冻结 Goal/Model contract hash、
ExecutionBinding、EvidenceRef、VerificationRecord、DecisionRecord、预算账目。
预算至少分开研究计算预算与 Codex 工具/分析预算；不能以 LLM 成功声明替代客观验收。

验收重点：初始化/重复打开一致性、冻结哈希和 schema migration、陈旧绑定拒绝、
未知证据不得满足目标、记录可追溯且修改有明确 Decision、离线崩溃恢复/事务边界、
独立 Reviewer 挑战记录与确定性 Verification 分离。先只读取和保存研究状态，
执行写接口、真实 Abaqus/ODB、Event Bridge 与原 Desktop Main 自动恢复另行授权。

M01-C 完成后停止，等待评审；没有启动 M02。
