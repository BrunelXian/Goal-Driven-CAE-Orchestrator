# D7-R2F — Integration Repair Report

日期：2026-11-01。最终结论：**D7_R2F_BLOCKED**。

原因：本轮误选的既有 AF 控制测试调用了未替换的生产 Grant issuer，违反“不得签发真实 Grant”的限定。发现后停止所有施工、测试、打包、安装及生命周期操作，仅只读核查本轮隔离数据并写本报告。不能将 pytest PASS 当成授权边界 PASS。

## 1. 边界事件与实际影响

我将 `tests/test_product_standard_control.py` 加入了 AF 回归。该文件的 fixture 拦截 subprocess/原生启动，替换运行配置校验与宿主观察，但**未替换 `execution.standard_contract._issue`**。`ProductStandardControl.invoke(action='authorize')` 因而实际写入生产类型 Grant。该选择错误由本轮执行负责，不归因于用户授权。

只读检查范围严格限定为：

`C:\Users\wuxia\AppData\Local\GDCAE-G3-D3-OFFLINE-20261030-A01\D6-20261031-A01\gdcae-m03f1p1-g2long-d6\af-d7r2f-selection-01-temp`

使用 SQLite `mode=ro&immutable=1`，读取前后数据库摘要不变。没有扫描生产 Project、其他历史数据库或未知进程，没有输出令牌、私钥或原始 SID。

| 实际观察 | 数量/状态 |
|---|---|
| 本轮隔离 execution.sqlite3 | 32 |
| `REAL_FIXED_STANDARD` / `TrustedStandardOperator` Grant | **27** |
| `TEST_ONLY` / `FakeGrantFixture` Grant | 1 |
| 测试 Run 记录 | 19 |
| Plan 的 runtime_binding.fixture_only=true | 32/32 |
| Plan 缺少生产固定校验必需 backend_id/backend_version/entry/cmd/materials | 32/32 |
| 本轮该目录 owner.json | 0 |
| 原生/网络审计守卫记录的尝试 | 0 |

这些是隔离替身配置下的持久记录，未观察到实际 Owner 或 Solver 启动；全部 Plan 缺失生产固定运行配置必需字段，未经替换的 `StandardConfig.verify` 不会接纳这些配置。这限定了可执行性风险，**不撤销调用真实 issuer、生成生产类型 Grant 记录这一越界事实**。没有将它们重标为 TEST_ONLY，也没有删除、撤销、改写或补造收尾证据。它们及测试生成的 Project-scoped 凭据保持原状，不得迁入真实任务或传播。

未启动 Abaqus、Datacheck、ODB/noGUI、AF Owner；未访问 Stable，未修改系统账户/ACL、共享环境或正式 Plugin 缓存，未提交或推送 Git。停止后没有继续安装资格或真实入口测试。

## 2. 已写入但尚未完成验收的修复

### Plugin

新增独立源码候选 `plugins/gdcae-d7`，声明名称 `gdcae-d7`、版本 `0.1.0-alpha.6-d7r2f`、Core/AF 候选版本 `0.0.0+d7r2f`。原 `gdcae` alpha.5 的安装缓存和 v1/Synthetic 命令保留。

新 helper 复用已有 ResearchProject、LocalReadPort、RodProduct，提供 `doctor`、`package-digest`、`init-v2`、`status-v2`、`prepare-a`、`preflight-a`、`approval-preview`、`decline-preview`。没有 authorize/submit/dispatch/Owner 启动命令。明确的 `decline-preview` 仅关闭产品预览，不伪装成人类 AF Decision、不释放预算。新入口拒绝旧安装版本/非安装 Core，不静默迁移旧 Project。

共享打包 helper 新增一个精确版本参数及新 Plugin 资源路径，旧默认版本保持不变；共享安装验证 helper 增加显式 expected_version 参数，旧默认仍为 `0.0.0+g3d6`。GD 业务闭包摘要排除新嵌入 Plugin 目录，Plugin 自己仍单独冻结摘要。

**尚未生成/安装 R2F Wheel、未形成最终 Runtime Candidate Manifest、未进行新 Plugin 官方安装/激活、未从实际 Main 调用安装后的新 v2 入口。** 不能把 source helper 单元测试当成这些验收。新 Plugin 中打包 helper 副本还需在后续冻结前做完整闭包一致性复核。

官方本地安装会由客户端管理缓存，并可能保存用户级启用设置；本轮未执行注册/安装命令，也未手改缓存。后续应使用独立 marketplace/name，经用户批准后走官方 UI，再验证新对话实际加载版本。不能通过复制缓存伪造激活。[官方 Plugin 打包与本地安装说明](https://developers.openai.com/plugins/build/plugins)

### Owner 解释器选择

优先方案有源码支持，尚无必要改成任意/新的动态解释器 pin：

- `service_owner.py` 既有 bootstrap 在 `-I -S` 下将自身包父目录放入搜索路径，可由原固定 Python 加载隔离位置的精确 AF 副本，无须向共享环境安装 AF。
- `service_discovery.discover` 验证 endpoint 的真实进程身份与原 IPC 认证，不要求客户端 Python 与 Owner Python 相同。
- `service_lifecycle.start` 原冲突来自应用解释器与 Standard 固定解释器强制相等。新增仅对 `product-trusted-local-rod-v2` 生效的 `owner_interpreter` 选择，仍返回唯一既有固定路径 `D:\XianLab\envs\LangChainEnv\Scripts\python.exe`。
- 新 `owner_runtime_preview` 核对精确 Route C Profile、原 StandardConfig、运行材料、源码/Plugin/依赖，返回原 `service_owner.py` 的摘要和固定解释器，无启动行为。
- 原 lifecycle 唯一 Popen 使用该选择；原 Owner 在实际初始化时再次校验自身解释器。固定/protected/TEST_ONLY 的原选择保持不变，没有新增 dispatcher、launcher 或 Solver shell 路径。

这些改动已写入并通过部分纯选择测试，**尚未在安装候选或真实 IPC 中验证**。没有调用 start 来证明它们，也没有伪造 Owner 收尾。

## 3. 本轮修改文件

| 仓库 | 文件 |
|---|---|
| GD 修改 | `plugins/gdcae/scripts/gdcae.py`、`plugins/gdcae/scripts/candidate.py`、`src/aegiscae/research/rod_local_project.py` |
| GD 新增 Plugin 11 文件 | `plugins/gdcae-d7/plugin.json`；`scripts/gdcae.py`、`scripts/candidate.py`；`skills/setup/SKILL.md`、`skills/research/SKILL.md`；`references/runtime-contract.json`、`references/handoff.md`；`agents/gdcae-cae.toml`、`gdcae-results.toml`、`gdcae-inverse.toml`、`gdcae-reviewer.toml` |
| GD 新增测试/报告 | `tests/unit/test_d7r2f_plugin.py`；本报告 |
| AF 修改 | `abqjobpilot/execution/rod_local_hil.py`、`abqjobpilot/service_lifecycle.py`、`abqjobpilot/service_owner.py`、`abqjobpilot/product_rod.py` |
| AF 新增测试 | `tests/test_d7r2f_owner_selection.py` |

之前 R1/R2 的全部源码、候选、报告与隔离材料保留；没有回滚用户修改。HEAD 未改：GD `a75a614f9738af8f257fd490ceec2df4c012ea19`，AF Develop `7f4b8d8f3a2c862ed8b244d495295f5d51ea0d88`。

以下仅标识停止时的工作区字节，**不是已批准发布/安装闭包**。按排序相对路径及带前缀文件 SHA-256 的紧凑 JSON 汇总：

| 工作区源码 | SHA-256 |
|---|---|
| GD Python（排除嵌入 Plugin） | 7857b4bdf3aa89093bb5f4d8c2fb19c04fbe878af8861d0a024acc59042c02dc |
| AF Python | b4bb09432c678b097977afe162070862564931f6b58545d4ea670e70b3257722 |
| 新 D7 Plugin 11 文件 | 9a608e791f2274cb7e615746f6147d21e0c6f4289a5f42a7b99af24a4c5a4696 |

复用解释器 `D:\XianLab\envs\LangChainEnv\Scripts\python.exe` 3.12.10；pytest 9.1.0、mcp 2.3.0、pydantic 2.13.4、pywin32 312。没有安装依赖或修改它们。

## 4. 实际测试记录，不扩大结论

safe 回执位于上述临时目录的父目录。

| label | 实际 pytest 结果 | 边界结论 |
|---|---|---|
| d7r2f-product-01 | 56 passed / 1 failed | 既有双安装 fixture 尝试原生调用，被 guard 拒绝，未执行；保留失败 |
| d7r2f-product-02 | 56 passed / 1 deselected | 排除该原生安装 fixture 后选定产品测试通过；0 原生/网络尝试 |
| af-d7r2f-selection-01 | 40 passed | 含 8 项新纯选择测试、32 项既有控制测试；**因实际 issuer 越界，整批不能判作授权合规 PASS** |

三份 safe JSON SHA-256 分别为：

- `06c3ef30993cdecbd4e81ae98ab169109902d0c8c4f3c0da43c94af09a2c0265`
- `96ba92bfc039b3fd5d175e383dfd089e17708e973910c9836d8290a0e0a060cf`
- `700a27f6ed29dac08549e5b4800c0e3e383a3458ee722ddf78d211cc5250f9ce`

停止前执行过 Ruff：新 Plugin helper、新测试及所选改动文件通过；GD tracked diff 检查通过。不是全仓回归或全文件 lint 通过。停止后未运行新测试。R2F 的安装正向链、A 初始化/预检/预算/预览的安装副本验收、版本重开、真实 Main Plugin 证据均 **PENDING**；R2 旧版本证据不能代替。

## 5. 后续门槛及 Owner 单独申请状态

先由用户评审这次测试边界事件。恢复后最小工作是：精确审查测试白名单，在任何 fixture 准备前拦截生产 `_issue`/authorize，显式区分 TEST_ONLY 证据写入；既有控制测试不得原样纳入“无真实 Grant”集合。不得清理或重标本轮 27 条生产类型记录来取得 PASS。

之后才能完成 R2F 两仓代码审查、无发行权限的独立版本候选、隔离安装及官方 Plugin 入口验收。任何正式 Plugin 用户配置变更仍需先单独批准。当前没有合格候选可供申请运行。

未来 TEST_ONLY Owner 申请必须另列：全新空白 Project、精确安装 AF/原固定 Python/Owner 入口摘要、单次 start→health→idle stop、禁止所有 Plan/Grant/Run 和 Solver 后端启用、原始进程身份与持久停止回执、UNKNOWN 不重试及有界观察。**本轮尚不具备填写该申请全部精确身份的资格，也不执行试验。** 不将 Route C 源码选择测试伪装为这种生命周期证明。

当前唯一交付结论为 **D7_R2F_BLOCKED**。代码与证据已保留，停止等待评审；不请求真实 A/B 或 Owner 启动授权。
