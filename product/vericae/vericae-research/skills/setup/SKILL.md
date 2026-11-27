---
name: setup
description: 当用户要检查VeriCAE、Codex原生能力、科研文件或执行连接状态时使用。只读报告实际能力与缺项；不要求额外语言运行时，不创建科研状态、安装组件、签发Grant或启动Solver。
---

# Set Up Research Environment — VeriCAE 0.5.6

先读取 [共同契约](../../references/three-skills-contract.md) 与
[Workspace Format v1](../../docs/vericae/WORKSPACE_FORMAT.md)。本Skill只检查，不自动安装、
改用户配置、展开Runtime、写Profile或初始化研究文件。

## 只读检查

1. **Codex**：核对当前宿主、实际可用的原生文件/调度工具与插件入口；版本不能核实时写NOT_VERIFIED。
   区分工具声明、实际可调用、真实操作已验收；ID或提示词不证明Desktop可见。
2. **VeriCAE**：manifest版本0.5.6，恰好三个Skill、原生Subagent TOML、Markdown/YAML模板
   及静态协议。插件不包含CLI或语言运行时；不以Python、Node、EXE安装作为前置条件。
3. **研究工作区**：有明确路径就用Codex原生文件查看/搜索，读取Handoff、Card、Tasks、模型及日志，
   核对必需文件、字段、六模块与实际引用。无项目写NOT_CREATED，不替Initiate创建。
   明确标 `NATIVE_FILE_REVIEW`，列出未检查字段/摘要；不等同确定性校验，不自动修复。
4. **长期角色与可选Subagent**：先读 [长期角色规范](../../references/persistent-role-threads.md) 和
   [跨对话协议](../../references/cross-thread-protocol.md)，分别检查：创建长期普通Thread、
   绑定同一Codex项目、左侧项目栏可见、向已有Thread发送、目标接收/执行、Main读取原回复。
   六项逐一记录工具声明、已实际验证、NOT_RUN/BLOCKED，不从spawn可用推断跨对话能力。
   Setup仅只读，不实际建线程、改绑定或发送探针；这些实际操作另在明确授权的初始化/UAT中执行。
   缺发送为 `BLOCKED / CROSS_THREAD_SEND_UNAVAILABLE`，缺读取为 `BLOCKED / CROSS_THREAD_READ_UNAVAILABLE`。
   可选Subagent另核对项目 `.codex/agents/` 中原生配置是否实际发现；模板存在不代表已注册。
   按 [原生配置说明](../../references/native-agents.md) 和 [双模式协议](../../references/subagent-modes.md)
   检查Consultation默认、Main原生派发、真实ID、独立Desktop入口与短回执。
   原生Thread引用未暴露写NOT_EXPOSED；四角色左侧可见及重启恢复需要人工核验。
   原生缺失为 `BLOCKED / HOST_CAPABILITY_UNAVAILABLE`，UI缺失或无法核验为 `BLOCKED / UI_NOT_VISIBLE`。
5. **MCP隔离**：默认继承父会话，不能用子代理TOML的MCP工具列表证明硬隔离。
   当前 `HOST_ISOLATION_NOT_SUPPORTED`；Main-Only仅为行为协议。
   feature禁用项的实际可见性/调用权限分别报告；未实测为NOT_VERIFIED，不做危险调用验证。
6. **执行环境**：本插件不自带AbqJobPilot MCP；没有经核验的外部连接时显示
   `AbqJobPilot MCP: UNAVAILABLE`、`connection: NOT_CONNECTED`。已另行注册的MCP按下节核验，
   不因插件未打包连接而忽略它，也不把旧插件残留工具当作目标服务器。
   不探测Core端口、不使用空MCP配置。
   未检查的Abaqus入口/许可证写NOT_VERIFIED，不运行Abaqus或许可证测试。
7. **模型配置**：只读核对当前目录的完整模型ID与推理强度、创建工具model/thinking参数及实际配置
   回读能力；按 [自适应模型协议](../../references/adaptive-model-assignment.md) 区分目录支持、请求支持、
   实际生效和跨对话保持。缺设置/回读能力时MODEL_ASSIGNMENT_UNAVAILABLE并指出最小人工操作。
   Setup不创建测试线程或发送配置探针；无实际前后测试不能宣称消息会保留目标模型。

开发者可另外运行仓库的 `vericae check`，这是可选开发测试工具，不是正式插件运行链路。
缺少它不把纯科研规划或只读分析标BLOCKED；不得要求安装Python/Node来通过Setup。
检查结论写实际来源、验证范围、失败与未验证项，不把文件存在说成权限或执行就绪。

## MCP Registration & Runtime Verification

新增、重新注册、重建或修改MCP Server后，按 [MCP运行时核验与恢复](../../references/mcp-runtime-verification.md)
从当前Desktop Main实际验证可发现性和可调用性。`codex mcp list`、`codex mcp get` 或独立CLI测试
仅能作为配置/独立进程证据，不能代替Desktop Main的实际调用验收。

注册成功但Main发现失败时，检查实际配置加载、项目路径/Trust与会话状态；Setup只读诊断，
不自行改配置、重启Desktop或写科研状态。需要重启刷新时，转交Conduct中的Main先保存研究状态、
任务卡、角色身份和恢复入口，再按该协议显示 **MCP Environment Refresh Required**。
重启是Runtime Discovery失败后的恢复措施，不是每次MCP重建的必选步骤。

用户重启后回原Main发送 `Resume`，Main恢复文件并重新核验服务器身份、版本、工具目录、
权限边界及实际回包；验证通过后才可恢复受该MCP阻断的工作。环境恢复不授予执行权限，
也不改变历史结果完整性或科研执行资格。其他不依赖该MCP的研究仍按原范围进行。

## 转交

新问题转 [Initiate](../initiate/SKILL.md)，已有项目转 [Conduct](../conduct/SKILL.md)。
环境报告仅在对话交付，不创建Card、Task、Handoff、日志、后端绑定或权限，不授予Grant。
不伪造真实操作；纯科研规划、Consultation及只读Conduct可在无MCP/AbqJobPilot/Abaqus环境继续。
