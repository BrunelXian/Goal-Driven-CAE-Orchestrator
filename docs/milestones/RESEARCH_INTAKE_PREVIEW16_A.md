# Research Intake & Task Cards · A 端验证

基线为 GitHub main 的 3e891fc2578951e3faa6280cb71d1882a716a9c9，候选为私有 Research Preview 0.2.0-preview.16。此候选用于科研立项与任务卡。A 端使用 Windows x64、CPython 3.12.10、本地隔离 Marketplace、Codex Desktop 26.1111.2228.0 和 CLI 0.169.0-alpha.11.1。候选 ZIP 的 SHA-256 为 f636eea1d03e6e3543c9fc8b1883622a80dd754e93a008bbe63dc749c0e9fa71，package-manifest.json 为 ee535eb0f0a26cd09d74d9dfaa3e93f9b875d21a102f22d6a9c3e6a675491e60。

## 实际路径与结果

| 场景 | 状态 | 可核查的观察 |
|---|---|---|
| 首次 setup，用户已有模型，希望反求 F 使测点竖向位移达到 1 mm，容差 ±0.1 mm | PASS | 真实 app-server 选中隔离安装目录下的 setup Skill。回复给出 LoadInv、可变量 F、测点与方向 UNKNOWN、CANDIDATE、T01/T02 和 DRAFT_NOT_PERSISTED。该会话没有 Desktop 创建接口，报告 BLOCKED_HOST_MAIN_CREATION |
| 用户在同一会话再次要求直接求 F | PASS | 回复保留草稿与阻断。两轮均无命令或服务工具执行，未给出载荷、求解公式或参数迭代 |
| Main 首屏 | PASS | 受限 research Skill 单独读入交接；另外一个真实 Desktop Main 复述目标、容差、资格、两张卡、UNKNOWN 与授权。在没有模型文件时保持候选 |
| 真实 Main 创建、身份与复用 | PASS，A 端接口集成 | 测试驱动使用已安装的 main-handoff、官方 create_thread 和 Host 回读，在 A 端既有可丢弃 Desktop Project 创建 LoadInv Main。核对同一 host、保存的项目、标题、线程和首屏。最终候选复核并复用同一 Main，第二次 claim 返回 VERIFIED、may_create=false |
| 最终包在真实 Main 下持久登记 | PASS | 正常注入的当前线程身份匹配 VERIFIED 回执。最终包将两卡在项目修订 2 登记。task-init 与独立 task-list 退出码均为 0。T01 保留测点、符号、边界及单位和独立依据的具体判据。T02 保留软件、服务、绑定与授权的独立检查要求 |
| Main 更新与进程重启后读回 | PASS | 同一 Main 执行 task-update、task-list 均返回 0。重新启动 launcher 从 SQLite 重放，修订 3、T01 OPEN、T02 BLOCKED。证据文件 SHA-256 与 T02 引用一致，两卡 NOT_VERIFIED / NOT_ASSESSED，execution_authorized=false |
| 正式 Plugin Creator 成功路径的一次性自动交接 | NOT_TESTED | 此次正向创建调用由 A 端测试驱动发起。未将候选上传私有插件，也未将独立测试分支拼接成 B 端产品 E2E |
| 动态角色与受约束的独立会话 | 契约 PASS；实际会话 BLOCKED_HOST_ROLE_BINDING | 任务按契约匹配角色，支持额外角色的定义与摘要检查。在当前证据下不能签发 Project、Role、Task、有效工具授权绑定 |
| AbqJobPilot 能力发现 | 只读发现 PASS；生产接口 BLOCKED_INTERFACE_UNVERIFIED | A 端找到 Abaqus 启动文件，读取 AbqJobPilot 0.2.2 源码版本和公开 MCP 的五项只读/预览工具声明。未取得服务连接或服务端项目回执，操作授权 NOT_GRANTED。未执行 Abaqus 或访问后端私有数据库 |

实际 Skill 回归使用官方 skills/extraRoots/set 在单次已认证的隔离 app-server 中选取隔离 Marketplace 的安装态 Skills，再按安装清单复核 Skill 文件。它覆盖模型的真实响应；同时验证本机已安装产物。两种测试环境的边界在上表分列。初步验收发现初版登记会丢失个别草稿判据，最终候选改为逐卡保留，并在新的合成数据库复验。

## 可复现测试

- 工作区合成 Core、科研约定、SessionHub 和立项测试共 135 项。包含两卡原子登记、依赖门禁、修订冲突、并发重放、提交成功后回执丢失、错误线程/项目/请求键、旧库开始立项、立项后冻结约定及扩展角色契约。运行 pytest 对应的 test_intake_task_cards、test_research_project、test_research_agreement、test_scoped_sessions 四个模块。
- 在安装态执行 tests/integration/intake_handoff_checks.ps1。丢失创建响应后重试、标题冲突、尚待回读的线程、线程冲突、错误项目和重开后复用均符合门禁。合成回执与上表真实 Host 回执分别保留。
- installed_sanity_checks 的 27 项安装态检查通过。plugin_creator_metadata_checks 使用已有 .15 的真实规范化布局投影至 .16，bind / doctor / new / overview 通过，21 项篡改被拒绝。此项未声称 .16 已经平台回读。
- 更新器的 17 项既有边界检查通过；未进行新的对外发布或在线升级。Runtime 的 10 项拒绝测试覆盖磁盘、摘要、路径、重复及额外文件、下载失败、重定向和截断。测试驱动识别本机 .NET WebException 的 ConnectFailure 状态，产品运行时策略未改动。

## B 端待验收

当前私有插件仍为 .15。候选获准更新后，使用正常插件 UI 输入上述案例。没有 Desktop Main 能力时应收到完整草稿和明确阻断；若有能力，应打开且仅打开一个符合项目身份的 Main，由 Main 承接两张原卡。在授权保存后关闭并重新进入，核对卡片、判据与更新历史；检查缺少授权时无法提交 Job。B 机本轮 NOT_EXECUTED。
