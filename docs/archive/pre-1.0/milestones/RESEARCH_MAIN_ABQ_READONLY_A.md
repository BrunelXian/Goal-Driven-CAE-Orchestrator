# Research Main 的 T02 工程接口 · A 端验收

## 被测对象

- 开发基准 `bd28669687689ec0d63654e8a79ec4f5b057dd89`。候选 `0.2.0-preview.19` 仅安装在 A 机隔离 Marketplace。候选 ZIP SHA-256 为 `18c30d1a7f4058f2ec71b4504243cfd439a95211ed9e2a2b51a301ebb56f8557`，Manifest 为 `e7ed5de9cc6f54f2d4edda7c9ac3ec70f56b8d3835969d0b67e40804a209554d`。安装目录与 ZIP 的 27 个文件逐一比对，全部字节一致，无额外文件。
- AbqJobPilot 0.2.2 正式上游提交 `7012133e7cc0176bb3e56fc24d7154ee3b90bb81`，受信部署所用服务代码归档 451435 字节，SHA-256 为 `34bb598048e24dbbe180ea1255227383012f1858579c2f8468cead1ac994d5df`。归档由独立部署步骤准备，未随插件分发。客户端与服务使用已绑定的 Windows CPython，外部部署环境提供 MCP SDK 2.3.0 及 Windows 依赖。首次候选在隔离解释器中找不到 pywintypes，真实 Main 返回 MCP_CLIENT_SDK_UNAVAILABLE，未产生后端观测；Main 另将失败登记到隔离 T02。最终候选仅从已绑定解释器加载所需 pywin32 目录，没有运行 .pth 或改动共享 Python。
- 使用真实存储的隔离后端项目，队列中仅有预置的惰性测试记录。观察服务握手、Project UUID、返回 schema、状态和摘要。当前测试范围不含真实科研模型、现场生产 Project 或 B 机。

## 入口及拒绝路径

研究 Skill 先读取 T02，使用已绑定安装的 `launch.ps1 -Action agreement`。新操作 `t02-plan` 展示 Windows 安装登记与受信源版本、目标后端和同意范围。服务尚未握手时保留 NOT_QUERIED。主线程需通过交接回执与现有任务所有者双重核验。人工同意后，原有 task-update 记录研究项目与后端 UUID 的绑定，以及包含配置摘要和查询范围的许可。新操作 `t02-read` 仅接受 queue_id、修订和幂等键。服务命令、根目录和证据输出路径不接受任务输入。

正式服务的五个发现工具之中，客户端实际只调 abq_list_jobs（queue、history）和 abq_job_status（可选 queue identifier）。只保留统计与响应摘要。响应中错误 UUID、错误 schema、错误状态及不完整返回均拒绝登记。内容寻址证据先核对实际字节，再通过原有 task-update 事务登记；相同请求重读已有证据，错误修订或证据修改均拒绝。后端项目文件在安装态自动测试前后逐一复核，内容相同。A 机单独保留原始本地回执。仓库只存可重跑代码和去标识结果。

## 八项历史架构断言

| 全仓检查 | 审计结论及处置 | 与安装态 T02 的关系 |
| --- | --- | --- |
| AF 只读边界 | 混合。codex_sessions 的 .call 转发 Desktop API；project.py 的 task_cards.apply 仅重放内存事件；sanity.py 的 getattr 仅读取四个固定字段。rod_expired_recovery 中还有真实后端生命周期调用。保留全仓失败。 | 已复核两个随包命中点。归档排除旧恢复与 Desktop 适配器。固定 MCP 调用名有 AST 测试和真实协议拒绝测试。 |
| 基线文档摘要 | Windows 检出换行导致四项冻结文档摘要不同。指定 docs/baseline Markdown 使用 LF，原文 Git blob 无变化。 | 基线完整性检查恢复 PASS。 |
| 层间依赖方向 | codex_sessions 从 research.scoped_sessions 导入线程引用校验，构成 interfaces → research 的实际反向依赖。保留待分层重构。 | 两个模块均不在已验证的安装归档。 |
| 禁止直接写入 | scoped_sessions 有实际独占写入/替换及一个字符串 replace 误报。旧恢复模块直接创建目录。保留失败。 | 检查部署端显式范围；T02 输入不能指定外部写入位置；登记只走 task_cards.record。后端目录前后字节一致。 |
| 遗留私有依赖 | rod_expired_recovery 导入 AbqJobPilot 产品和执行内部模块，违反当前适配边界。 | 产品 Core 成员精确枚举并检查导入。生产读端采用上游正式 stdio。 |
| 延期执行面 | 同一恢复模块引用 ProductRod 及 rod_local_hil。该缺陷与遗留依赖检查指向同一代码，但约束分别保留。 | 插件不提供这些入口。执行授权在任务回读中为 false。 |
| M01 文件骨架 | 冻结清单早于后续科研模块，亦检出旧恢复模块，无法整体放行。保留旧里程碑约束。 | 新测试单独限定当前发行 Core 的十个成员，独立检查实际 ZIP。 |
| 研究存储 SQL | 对每个源码文件执行同一 SQL 检查。六处清单外执行均在 rod_expired_recovery。已安装的 project.py（含 T02 账本路径）通过原字面量 SQL 与创建门禁。 | 新增回归在全部发行 Core 模块上复用原检查器。旧恢复模块仍需另行治理。 |

## 可复现的 A 端检查

- `tests/integration/installed_t02_checks.py` 使用合成 Main、真实安装和正式 stdio。验证缺少部署、额外命令字段、源代码篡改、首次未授权、错误后端 UUID、错误队列许可、旧修订和证据篡改。正向结果为 QUEUED、1 条队列、0 条历史，三个响应摘要齐全。重复请求返回 REPLAYED，新进程读回修订 4。T02 为 SUBMITTED / NOT_VERIFIED / NOT_ASSESSED / NOT_GRANTED。这个测试不承担 Desktop 身份验收。
- `tests/architecture/test_installed_t02_boundary.py` 和原有协议拒绝共 12 项通过。研究约定、ResearchProject、Task Card 共 92 项通过；安装态 Sanity Model 共 27 项通过；Setup 路由 15 案例通过。Main 门禁包含新增的两个操作。既有私有发行身份拒绝、更新器边界及交接恢复独立测试。
- 部署、授权范围和失败使用说明见 `product/research-preview/T02_READONLY.md`。安装态通过既有 Main 显式调用。日常私有插件自然触发、其他 Python 环境和 B 机体验仍待独立验收。

## 真实 Desktop Main 与最终判定

在 A 机已有且经 Host 验证的 Research Main 中，使用隔离 Marketplace 的正式安装，读取安装态 research Skill 并在新授权的隔离科研项目下操作。Marketplace 列表读回 enabled=true。独立核验同一轮的 Desktop commandExecution 输出、launcher 退出码及证据文件实际字节。新项目、Main 线程及后端 UUID 仅在本机核对。

| 同一 Main 的操作 | 实际结果 |
| --- | --- |
| doctor、Main 回执及 T01/T02 登记 | PACKAGE_AND_CORE_VERIFIED、VERIFIED、修订 2 |
| 查询前 | t02-plan 返回 READ_PROPOSAL；缺少账本同意记录时返回 T02_READ_CONSENT_REQUIRED，launcher 退出 2 |
| 登记限定同意、查询正式 stdio | 修订 3；随后 REGISTERED_READ_BACK，launcher 退出 0。AbqJobPilot 0.2.2，协议 2025-11-25。队列 1、历史 0、状态 QUEUED、active_execution_confirmed=false |
| 证据字节与回执 | 证据 SHA-256 `c3ee083b77d865492e61a4d8708d8eb426cb300ed246eb252d5bd73f935f68e9`。独立复算吻合，文件 JSON 全部字段与 Host 输出匹配。账本提交 digest `9d9c24b97cdac151c94a9a3499f9b6eadc63c51f822dbfe0a9355bbc53ff8943` |
| 相同请求及独立新进程读取 | REPLAYED，原摘要和修订 4 保持一致。task-list 读回同一 T02、两条同意范围引用及观测引用。T01 OPEN；T02 SUBMITTED、NOT_VERIFIED、NOT_ASSESSED、NOT_GRANTED。execution_authorized=false |

`tests/integration/desktop_t02_readback.mjs` 实际执行通过；它只接受正确线程中有序、可读回的工具输出。平台自然发现新版 Skill、生产后端部署和 B 机尚未验收。

**A 端正式插件只读链路 PASS。全仓架构治理 PARTIAL。** 原八项架构失败中一项修复，七项保留；架构目录与协议拒绝集运行得到 186 通过、7 失败，随后新增的两个安装边界用例通过。通用全仓 pytest 的一次运行记录为 1403 通过、94 跳过、48 失败、478 错误。其中临时根不在指定 TEMP、大量旧测试要求专有隔离 runner 或显式 Develop fixture。这次调用不能作为全仓通过证据。重设进程临时根的第二次非专项遍历仍出现旧 fixture 错误，主动停止；未取消任何专项验收。不修改旧测试安全门禁。生产运行还需独立部署 SDK、受信服务归档与后端项目绑定。
