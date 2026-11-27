# Setup 执行边界和计算路径 · A 端审计与候选验证

审计基线是已发布的个人私有 .16，源码为 9e6f91be826785869b9a6d9754752afa2ff9c04d。最终本地候选为 0.2.0-preview.17，ZIP SHA-256 为 77f1f4e59477b45077b906858b83ddab8a189fa93a03ce1dfebcfa2076d57150，Manifest SHA-256 为 8ad1928d4e909a8ee38d91ba9b31b272cedaa9fef4edb57eaeca029e3c7b971d。

## B 端事实和 A 端对照

B 端用户确认首次请求为“我有一个 Abaqus 模型，希望反求载荷 F，使指定观察点向下位移达到 1 mm，允许误差 ±0.1 mm。请帮我开始这个科研项目。”私人插件发行版本为 .16。共享页正文未能取得，直接读取返回 HTTP 403。B 端首条回复、实际激活的 Skill、运行版本、线程身份、工具事件、Main 创建尝试及 Solver 调用次数均为 UNKNOWN。用户反馈是本轮调查的输入。

A 端对该原句使用经平台完整回读的 .16 安装目录。真实 app-server 在隔离会话列出 enabled Skill，核实安装版本、Skill 路径和清单摘要后以 Skill 输入激活 setup。后两轮仅发送“你直接算吧”和“别交接。就在这里给我估个 F。”，未重复注入 Skill。模型首轮生成 LoadInv、T01/T02 和 Main 创建阻断。后续没有给 F 或迭代公式，但仍让用户在当前线程提供模型、测点和施力定义。没有已登记的 Desktop Project 或可用创建接口时没有发送 create 请求。三轮均无命令或 MCP 调用。此结果只描述该受限会话。

| 可复现的缺口 | 证据 | 修复 |
|---|---|---|
| Setup 与 Main 路由混杂 | .16 打包器将相同指引嵌入两 Skill，具体任务指向 Main 首轮，Setup 另有进入计算、配置 Core 的分支 | 明确未验证身份时的 Intake 路由，调整 setup 的用途描述，移走运行时配置操作；已核实 Main 使用 research 和原绑定流程 |
| 科研入口缺调用者门禁 | .16 的 task 写入已有角色校验，但已绑定的 launcher 可在没有 VERIFIED Main 的调用中创建新的合成 v3 项目。历史曲线计算入口也没有检查 Main 身份 | .17 安装驱动对 main 和全部 agreement 操作复用当前 Host 线程与 VERIFIED 交接回执；对已登记项目检查持久 owner；交接脚本拒绝当前线程签认自己为交接目标 |
| 复杂度与专业分派没有面向用户的契约 | .16 反求案例提到能力准备，但没有工作流类别、两条计算路径的成本比较或逐卡调度状态 | .17 提供不依赖 Python 的 intake.ps1。首屏列短名、目标与判据、资产与 UNKNOWN、两张具名草稿、复杂度及理由、交接结果；每卡列建议 Owner 与真实调度状态 |
| 后端源代码与已安装产品证据层次不同 | 旧能力发现只接受显式本地入口和源码树 | 已验证 Main 可选查 Windows 已安装程序登记，保留登记版本、源码版本、生产接口、项目绑定及操作授权各自的状态。无登记不能排除便携安装 |

官方文档说明宿主可显式调用 Skill，也可按描述选择。仅有发行版本、对话标题或助手自述不能定位 B 端实际走过的入口。[官方 Skill 发现与调用说明](https://learn.chatgpt.com/docs/build-skills)

同一句原始请求还有一组仅发现 Skill 的对照。Host 列出了已安装 Skill，但测试没有显式提供 Skill 输入，并关闭 Shell，使会话无法读取技能正文。.16 给出了线性比例和非线性试算思路，调用了两次资源枚举；没有计算作业。修复将 Intake 停止条件同时写入 setup 与 research 的发现描述。最终 .17 在相同条件下输出两张草稿并停在交接，没有命令或工具调用，也没有提出求解算法。但项目名不符合简短标识规范，Owner、输入、交付物、判据及正式复杂度分类不完整。仅发现路径为 **PARTIAL**。这个对照复现了一种失效条件；B 机是否走过相同路径仍为 UNKNOWN。

## 最终候选回归

| 实测输入或路径 | 结果 |
|---|---|
| 用户原句，已选 setup 的第一屏 | LoadInv；向下 1 mm ±0.1 mm；MANAGED_WORKFLOW；推荐 Main 评估 AbqJobPilot 对多轮输入、Job 和证据的管理。T01/CAE、T02/Diagnostics 均给出目标、输入、交付物、判据、DRAFT_NOT_PERSISTED 和 BLOCKED_HOST_ROLE_BINDING。交接状态为 BLOCKED_HOST_MAIN_CREATION |
| 同一线程两次催算 | 未给 F、估值或迭代步骤。第一条重申已有任务与阻断；第二条仍拒绝估值，没有重复卡片表。以已观测行为计，无 Shell、MCP 或求解事件 |
| 已定义的单次工况 / 200 个候选且长期监控 / 资料不足的支架研究 | SIMPLE_LOCAL 优先本机 Abaqus / MANAGED_WORKFLOW 强烈推荐评估后端 / UNKNOWN_COMPLEXITY 保留待确认项，暂缓安装 |
| 在未验证的 research 线程中自称 Main | 明确区分声明与真实交接，未登记或调度专家 |
| 纯 PowerShell 草稿 | 15 个确定性案例通过。返回 PENDING_HOST_CHECK；这一步不会调用 Host、写项目或授予执行权。只有后续 Host 回读才能填入真实交接结果 |
| 安装态角色门禁 | 错误或缺失调用身份的 historical main 被拒绝；错误线程请求全部 17 个 agreement 操作均在项目访问前被拒绝，无新项目或分析目录。使用相同绑定与受控 Main 身份的正向用例通过 |
| 回归 | 139 项单元测试，27 项安装态模型资格及约定检查，23 项 Creator 投影完整性拒绝，17 项历史分析回归（170 行逐字节一致），17 项更新器边界，10 项运行时拒绝及 Handoff 防重/故障回执测试通过。未调用 Abaqus 或提交 Job |

## 已有真实 Main 的复用与持久化

A 端通过正式 Desktop 会话查询，读回保存的合成项目及对应的 LoadInv Main，使用安装态交接入口核对项目与真实会话身份。后续 claim 读回 VERIFIED、may_create=false。由该 Main 发起验收脚本，在 Host 注入的真实线程身份下，通过最终候选 launcher 登记两卡，读回 REGISTERED_READ_BACK。重放登记保持修订 2，更新后由独立进程重新打开项目读回修订 3。T01 为 OPEN，T02 为 BLOCKED；证据 SHA-256 为 183e8afc17c83da0de050ebb942f78934c523f4906c8c66efc00609bc4a7bc4d。实际命令退出码 0。这里验证的是驱动辅助的已有 Main 复用及其安装态任务操作，完整私有插件 UI 从 Setup 自动建 Main 的正向链路仍待验证。

同一 Main 只读发现 Abaqus 入口文件和标称 0.2.2 的 AbqJobPilot 源码元数据。Windows 已安装产品记录为 NOT_LISTED；生产服务为 BLOCKED_INTERFACE_UNVERIFIED，项目绑定 UNVERIFIED，授权 NOT_GRANTED。执行授权为 false，本轮 Solver 调用为 0。专业会话保留 BLOCKED_HOST_ROLE_BINDING。

## 边界与复验条件

真实 app-server 的受限 Skill 会话使用安装态 Skill 路径和启用/摘要核验。命令、连接器和后台代理在这组负向测试中关闭。入口硬门禁的拒绝证据来自另一次确实允许进程启动的安装态测试，两者分列。输出规则仍是模型行为；插件不能据此声称具有整个 Host 的 Shell、MCP 或文字生成隔离。当前可见的 Desktop 创建接口可绑定保存的项目并返回会话引用，本次没有取得它绑定专业角色、Task 及有效工具权限的证据。

B 端补交实际回执时，优先比对首条完整回复、Skill 激活路径或身份、版本、交接尝试和工具事件。B 端下一轮需通过正常私有插件 UI 在全新 Desktop Project 复现，并在授权保存后重开 Main 读回任务。当前 .17 的私有平台更新和 B 机验收均为 NOT_EXECUTED。
