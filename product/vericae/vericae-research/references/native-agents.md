# VeriCAE 0.5.6 — Codex原生Subagent配置

交付三个完整TOML，默认继承宿主当前模型，不固定模型或改写用户设置：
0.5.4标准协作优先 [四个长期角色对话](persistent-role-threads.md)；此处TOML是可选临时
Subagent能力，不能用来冒充长期Thread或跨对话通信。普通角色Thread不会因同名自动加载TOML。

- [vericae-cae](../native-agents/vericae-cae.toml)：模型静态检查及限定产物。
- [vericae-results](../native-agents/vericae-results.toml)：指定既有结果分析与来源保留。
- [vericae-validation](../native-agents/vericae-validation.toml)：独立方法/证据复核。

每份含 `name`、`description`、`developer_instructions` 及受支持feature禁用项。
共享纪律已嵌入每份配置，不依赖额外脚本。模式详见 [双模式协议](subagent-modes.md)。

## 项目级使用

Codex原生发现位置是项目 `.codex/agents/*.toml` 或个人 `~/.codex/agents/*.toml`。
本包的 `native-agents/` 是交付源，不能假定插件manifest会自动注册它们。
在用户确认的新测试项目中，使用原生文件操作把这三份复制到项目 `.codex/agents/`；
已有同名文件先比较，不覆盖。不要修改用户级配置、沙箱、Trust或正式插件。
新会话检查实际可用agent_type；文件存在、TOML解析通过不代表宿主已加载。
本开发仓库同时有对应项目级副本，原历史配置保留不变。

## 功能禁用与隔离限制

配置关闭 `features.apps`、`features.plugins`、`features.memories`、
`features.request_permissions_tool`。这些原生能力项旨在缩小表面，实际是否加载、
工具是否可见与调用是否允许必须分别实测；不得据此承诺执行MCP已隐藏。
保留原生文件工具以支持受限产物编辑；Consultation只读约束是行为协议。

`HOST_ISOLATION_NOT_SUPPORTED`：自定义Subagent仍继承父会话MCP及权限，
不配置伪造的 `allowed_tools`/`disallowed_tools` 或子代理MCP删改来宣称Main独占。
如宿主不能可靠区分人类消息与Main派发来源，保持Consultation并报告BLOCKED。
执行权限仍依赖AbqJobPilot Grant；本切片不调用该执行链路。

依据：[Codex官方Subagents说明](https://developers.openai.com/codex/subagents)
（2026-11-22查阅）。配置发现和继承行为以当前宿主实测为准，不用文档截图替代UI证据。
