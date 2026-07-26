# AegisCAE Runtime 项目计划书

## 1. 项目名称

### 正式工作名

**AegisCAE Runtime**

中文可称：

**受控 CAE 智能运行时**

其中：

- **Aegis** 表示防护、约束与可信边界；
    
- **CAE** 表明项目服务于计算机辅助工程工作流；
    
- **Runtime** 表明它不是 Prompt、脚本集合或聊天机器人，而是独立执行、验证和审计系统。
    

### 原 AbqPilot 的定位

`AbqPilot` 不再作为总项目名称。

它应调整为：

```text
AegisCAE Runtime
└── Abaqus Adapter
    └── abqpilot
```

即：

> `abqpilot` 是 AegisCAE Runtime 面向 Abaqus 的领域适配器和兼容包。

这样既保留现有代码、历史和用户认知，又避免整个系统被永久绑定到 Abaqus 或“Pilot”式助手定位。

---

# 2. 项目定位

## 2.1 核心定位

AegisCAE Runtime 是一个：

> **面向 CAE 仿真任务的受控、确定性、可恢复、可审计运行时。**

它负责把用户、固定流水线或上层智能模型提出的任务，转化为经过授权、验证和证据记录的 CAE 操作。

其核心职责包括：

- 管理项目、任务、运行和仿真上下文；
    
- 限制可读取、可修改和可执行的资源范围；
    
- 控制 CAE 模型、输入文件和结果文件的生命周期；
    
- 对高风险操作实施程序级授权；
    
- 调度求解器并监控运行状态；
    
- 验证结果文件的身份、完整性和物理合理性；
    
- 生成可追溯、可复核的证据包；
    
- 向 Codex、Grok、Claude 或其他客户端暴露稳定工具接口。
    

## 2.2 项目不是什么

AegisCAE Runtime 不是：

- 自由修改 CAE 模型的聊天机器人；
    
- 一组 Abaqus Prompt；
    
- Codex CLI 的包装器；
    
- 通用 Agent 框架；
    
- 自动替代工程师判断的系统；
    
- 允许 LLM 直接控制求解器的执行层；
    
- 无约束生成任意 CAE 模型的工具。
    

---

# 3. 核心设计原则

## 3.1 唯一执行权威

所有生产级文件修改和进程执行，必须经过 AegisCAE Runtime。

```text
No production subprocess outside Unified Executor.
No production write outside Controlled Workspace.
```

不得存在第二条公开的 subprocess、shell 或直接文件写入路径。

## 3.2 LLM 不是领域权威

LLM 可以：

- 理解用户意图；
    
- 提出候选计划；
    
- 解释错误；
    
- 选择下一项工具；
    
- 编写说明和报告；
    
- 辅助开发 Runtime。
    

LLM 不可以：

- 自行授权求解；
    
- 直接覆盖基准模型；
    
- 宣布 ODB 有效；
    
- 将验证失败改成通过；
    
- 决定最终物理结论；
    
- 冻结正式证据；
    
- 绕过 Workspace、Executor 或 Validator。
    

## 3.3 固定流水线必须独立运行

即使完全没有 Codex 或其他 LLM，系统仍必须能够：

- 创建任务；
    
- 准备仿真输入；
    
- 执行验证；
    
- 提交求解；
    
- 监控状态；
    
- 读取结果；
    
- 计算指标；
    
- 生成证据；
    
- 恢复中断任务。
    

LLM 是可选客户端，不是运行时依赖。

## 3.4 基准文件默认不可变

优先采用：

```text
immutable source
→ clone to staging
→ modify candidate
→ validate
→ execute
→ promote or quarantine
```

而不是：

```text
modify original
→ attempt rollback after failure
```

对于失败任务，优先隔离失败运行，而不是试图把结果文件恢复成旧版本。

## 3.5 领域结论必须由程序产生

以下状态只能由 Runtime 的确定性逻辑生成：

```text
AUTHORIZED
EXECUTION_STARTED
EXECUTION_COMPLETED
SOLVER_FAILED
ARTIFACT_STALE
ODB_READABLE
ODB_VALID
REQUIRED_FIELDS_PRESENT
PHYSICS_WARNING
PHYSICS_REJECTED
EVIDENCE_FROZEN
```

自然语言报告只能解释这些状态，不得创建或覆盖这些状态。

---

# 4. 总体架构

```text
┌──────────────────────────────────────────────┐
│ User / Fixed Pipeline / Intelligent Client   │
│ Codex / Grok / Claude / Local Model          │
└──────────────────────┬───────────────────────┘
                       │
                       │ Structured Request
                       ▼
┌──────────────────────────────────────────────┐
│              AegisCAE Interface              │
│ Python SDK / JSON CLI / MCP Adapter          │
└──────────────────────┬───────────────────────┘
                       ▼
┌──────────────────────────────────────────────┐
│             AegisCAE Runtime Core            │
│                                              │
│  Context                                     │
│  Session Manager                             │
│  Plan and State Machine                      │
│  Tool Registry                               │
│  Risk Policy and Authorization               │
│  Controlled Workspace                        │
│  Unified Executor                            │
│  Checkpoint and Staging                      │
│  Validator                                   │
│  Evidence Recorder                           │
└──────────────────────┬───────────────────────┘
                       ▼
┌──────────────────────────────────────────────┐
│               CAE Adapters                   │
│                                              │
│  Abaqus Adapter / abqpilot                   │
│  Future Ansys Adapter                        │
│  Future CalculiX Adapter                     │
└──────────────────────┬───────────────────────┘
                       ▼
┌──────────────────────────────────────────────┐
│        Solver / CAE / ODB / Result Files     │
└──────────────────────────────────────────────┘
```

---

# 5. 核心模块

## 5.1 AegisContext

`AegisContext` 是整个 Runtime 的唯一上下文来源。

建议最小字段：

```python
@dataclass(frozen=True)
class AegisContext:
    schema_version: str

    session_id: str
    task_id: str
    run_id: str

    project_root: Path
    source_root: Path
    staging_root: Path
    output_root: Path
    evidence_root: Path

    adapter_name: str
    solver_command: Path
    expected_solver_version: str

    execution_mode: str
    policy_id: str
    allowed_tools: tuple[str, ...]

    cpu_limit: int
    timeout_limit_s: int

    active_plan_id: str | None
```

要求：

- 可序列化；
    
- 可版本化；
    
- 可持久化；
    
- 可恢复；
    
- 不依赖隐式当前目录；
    
- 不依赖散乱环境变量；
    
- 所有工具共享同一 context ID。
    

## 5.2 Session Manager

负责：

- 创建任务目录；
    
- 生成 session、task 和 run ID；
    
- 保存运行状态；
    
- 恢复中断任务；
    
- 区分完成、失败、隔离和等待人工处理状态；
    
- 管理多次迭代；
    
- 防止不同 run 的 artifact 混用。
    

## 5.3 Controlled Workspace

负责：

- 统一解析路径；
    
- 控制读写范围；
    
- 阻止目录逃逸；
    
- 阻止符号链接逃逸；
    
- 保护 immutable source；
    
- 限制 staging、output 和 evidence 的写入职责；
    
- 拒绝外部绝对路径；
    
- 拒绝基准 CAE、INP、ODB 覆盖；
    
- 隔离失败运行。
    

最小接口：

```python
resolve_read()
resolve_staging_write()
resolve_output_write()
resolve_evidence_write()
assert_immutable()
assert_no_symlink_escape()
assert_allowed_execution_cwd()
```

## 5.4 Unified Executor

所有外部进程必须由统一 Executor 启动。

覆盖：

- Abaqus solver；
    
- Abaqus CAE noGUI；
    
- ODB extraction；
    
- CAE export；
    
- adapter-specific subprocess；
    
- 未来其他 CAE 求解器。
    

Executor 负责：

- 验证 context；
    
- 验证 plan step；
    
- 验证 tool identity；
    
- 验证 authorization；
    
- 验证工作目录；
    
- 验证命令来源；
    
- 限制 CPU 和 timeout；
    
- 启动前记录事件；
    
- 捕获 exit code、stdout、stderr；
    
- 结束后记录 artifact；
    
- 禁止任意 shell 字符串执行。
    

原始 process launcher 必须是私有实现，不得直接暴露给 Agent、CLI、GUI 或 adapter。

## 5.5 Tool Registry

Tool Registry 是受控能力目录，而不是任意插件系统。

每项工具需要定义：

```python
@dataclass(frozen=True)
class ToolDefinition:
    name: str
    version: str
    risk_level: str
    input_schema: type
    output_schema: type
    handler: Callable
    requires_authorization: bool
    idempotent: bool
    default_timeout_s: int
    read_scopes: tuple[str, ...]
    write_scopes: tuple[str, ...]
```

第一阶段仅采用静态注册。

未知工具、未知版本和不匹配 schema 必须拒绝。

## 5.6 Risk Policy and Authorization

建议风险分级：

```text
L0：只读检查
L1：可逆、本地、staging 范围修改
L2：消耗计算资源、运行求解器
L3：发布、覆盖、删除或影响基准资产
L4：外部系统、共享状态或正式证据冻结
```

默认策略：

- L0 自动允许；
    
- L1 允许，但必须写入 staging 并记录事件；
    
- L2 必须具有与请求绑定的授权；
    
- L3 默认禁止，特殊流程单独批准；
    
- L4 必须显式人工授权。
    

授权必须包含：

- authorization ID；
    
- task ID；
    
- run ID；
    
- plan step ID；
    
- tool name；
    
- 输入 hash；
    
- job name；
    
- resource limits；
    
- 创建时间；
    
- 过期时间；
    
- actor；
    
- single-use 状态；
    
- revoke 状态。
    

## 5.7 Plan and State Machine

结构化计划至少包含：

```text
inspect
plan
authorize
prepare
execute
monitor
validate
report
freeze
close / quarantine
```

每个步骤记录：

- step ID；
    
- tool；
    
- inputs；
    
- expected outputs；
    
- risk level；
    
- prerequisites；
    
- authorization requirement；
    
- validation contract；
    
- timeout；
    
- retry policy；
    
- failure state；
    
- compensation or quarantine policy。
    

禁止执行未出现在当前批准计划中的生产步骤。

## 5.8 Validator

Validator 与 Executor 必须职责独立。

验证分为三层：

### 执行完整性

- process exit code；
    
- `.sta` 完成状态；
    
- `.msg`、`.dat` 错误；
    
- `.lck` 状态；
    
- timeout；
    
- solver termination reason。
    

### Artifact provenance

- 输入 hash；
    
- job identity；
    
- run identity；
    
- artifact 创建时间；
    
- stale artifact 检查；
    
- ODB 可读取；
    
- source/candidate/run manifest 匹配；
    
- required steps、frames、fields。
    

### 物理与工程合理性

- 数值范围；
    
- 守恒关系；
    
- 边界条件保持；
    
- 模型条件保持；
    
- 收敛性；
    
- 工程阈值；
    
- 需要人工复核的异常。
    

物理层结果应允许：

```text
PASS
WARNING
OUT_OF_EXPECTED_RANGE
MANUAL_REVIEW
REJECTED
```

不得把所有异常自动解释为无效结果。

## 5.9 Checkpoint and Staging

第一优先级不是通用 rollback，而是：

- source immutable；
    
- clone-before-edit；
    
- staging；
    
- manifest；
    
- atomic promotion；
    
- failed-run quarantine；
    
- partial execution detection。
    

Checkpoint 应记录：

- context ID；
    
- source artifact hash；
    
- candidate artifact hash；
    
- staging manifest；
    
- plan step；
    
- 时间；
    
- adapter；
    
- Runtime 版本。
    

## 5.10 Evidence Recorder

Evidence Recorder 采用 append-only event ledger。

事件示例：

```json
{"event": "context_resolved"}
{"event": "plan_created"}
{"event": "authorization_created"}
{"event": "tool_started"}
{"event": "artifact_created"}
{"event": "process_started"}
{"event": "process_completed"}
{"event": "validation_completed"}
{"event": "artifact_promoted"}
{"event": "evidence_frozen"}
```

最终证据包应包含：

- resolved context；
    
- plan；
    
- authorization；
    
- tool calls；
    
- tool results；
    
- input files；
    
- scripts；
    
- logs；
    
- validation results；
    
- metrics；
    
- warnings；
    
- Git commit；
    
- working-tree state；
    
- Runtime 和 adapter 版本；
    
- SHA-256 manifest；
    
- exclusions；
    
- failure records；
    
- final machine verdict。
    

Markdown 或 PDF 报告只是 ledger 的展示形式，不是证据的唯一来源。

---

# 6. Abaqus Adapter：原 AbqPilot 的迁移定位

原 AbqPilot 中应保留的能力：

- Abaqus command builder；
    
- CAE export；
    
- INP inspection；
    
- controlled INP patch；
    
- StaticValidator；
    
- DiffGuard；
    
- PhysicsGuard；
    
- solver approval；
    
- solver monitor；
    
- `.sta/.msg/.dat/.lck` diagnosis；
    
- ODB extraction；
    
- metric evaluation；
    
- repair plan；
    
- evidence report；
    
- fixed pipeline。
    

这些模块逐步迁入：

```text
adapters/abaqus/
```

建议结构：

```text
aegiscae/
├── runtime/
│   ├── context.py
│   ├── session.py
│   ├── workspace.py
│   ├── executor.py
│   ├── authorization.py
│   ├── registry.py
│   ├── workflow.py
│   ├── checkpoint.py
│   └── evidence.py
│
├── validation/
│   ├── execution.py
│   ├── provenance.py
│   └── physics.py
│
├── interfaces/
│   ├── python_api.py
│   ├── json_cli.py
│   └── mcp.py
│
└── adapters/
    └── abaqus/
        ├── commands.py
        ├── cae.py
        ├── inp.py
        ├── solver.py
        ├── diagnosis.py
        ├── odb.py
        ├── metrics.py
        └── guards.py
```

兼容期内保留：

```text
abqpilot/
```

但其内容逐步变为兼容导入层：

```python
from aegiscae.adapters.abaqus import ...
```

---

# 7. 开发阶段

## Milestone 0：重命名与架构冻结

目标：

- 确认新名称；
    
- 建立新仓库或新顶层包；
    
- 写入架构决策记录；
    
- 冻结核心不变量；
    
- 确定旧 AbqPilot 迁移边界。
    

产物：

- `ARCHITECTURE.md`
    
- `RUNTIME_INVARIANTS.md`
    
- `MIGRATION_FROM_ABQPILOT.md`
    
- `ADR-001-runtime-first.md`
    
- 新包结构骨架。
    

本阶段不运行 Abaqus，不改变现有生产流水线。

## Milestone 1：统一执行控制面

完成：

- AegisContext；
    
- ControlledWorkspace；
    
- Unified Executor；
    
- 私有 raw process launcher；
    
- 现有 solver runner 迁移；
    
- 消除隐式 CWD；
    
- 架构静态检查。
    

验收：

- 所有生产 subprocess 只有一个入口；
    
- 所有生产写入必须经过 Workspace；
    
- source artifact 不可写；
    
- traversal、external path、symlink escape 被拒绝；
    
- 未授权 L2 操作在 spawn 前被拒绝；
    
- 无 LLM 条件下固定 pipeline 正常运行。
    

## Milestone 2：Artifact provenance 与强 ODB 验收

完成：

- prelaunch manifest；
    
- candidate INP SHA-256；
    
- job/run identity；
    
- stale artifact 检查；
    
- ODB readability；
    
- required step/frame/field；
    
- output quarantine；
    
- staging 与 atomic promotion。
    

验收：

- 旧 ODB 拒绝；
    
- 错 job ODB 拒绝；
    
- corrupt ODB 拒绝；
    
- required field 缺失拒绝；
    
- 失败 run 不污染有效 output；
    
- source hash 保持不变。
    

## Milestone 3：工具、计划与证据闭环

完成：

- Tool Registry；
    
- risk policy；
    
- single-use authorization；
    
- structured plan；
    
- state machine；
    
- Evidence Recorder；
    
- SHA-256 freeze manifest；
    
- JSON CLI。
    

验收：

- 未登记工具拒绝；
    
- out-of-plan execution 拒绝；
    
- authorization 复用拒绝；
    
- evidence freeze 后修改可被发现；
    
- 完整 dry-run 可通过 JSON CLI 执行；
    
- 每个 machine verdict 可追溯到具体规则和证据。
    

## Milestone 4：智能客户端接入

完成：

- Codex Skill；
    
- Codex JSON CLI 调用；
    
- MCP adapter；
    
- 其他模型客户端验证；
    
- 可选只读 UI。
    

验收：

- Codex 无法直接修改 source；
    
- Codex 无法绕过 Executor；
    
- Codex 无法覆盖 Validator verdict；
    
- 相同结构化请求在相同 Runtime 下产生相同领域 verdict；
    
- 移除 Codex 后固定 pipeline 仍然完整可用。
    

---

# 8. 测试战略

## 单元测试

覆盖：

- Context round-trip；
    
- path resolution；
    
- source immutability；
    
- authorization；
    
- command construction；
    
- tool schema；
    
- evidence hash；
    
- state transitions；
    
- ODB contract。
    

## 架构测试

CI 必须检查：

- 禁止新增公共 subprocess 入口；
    
- 禁止 adapter 直接调用 subprocess；
    
- 禁止生产模块直接写 source；
    
- 禁止未知执行目录；
    
- 禁止 LLM 模块导入底层 process launcher；
    
- 禁止报告生成器直接创建 PASS verdict。
    

## 集成测试

采用 fixture 和 mock solver：

- 正常完成；
    
- timeout；
    
- stale ODB；
    
- corrupt ODB；
    
- wrong-job ODB；
    
- missing field；
    
- lock 残留；
    
- hash mismatch；
    
- interrupted run；
    
- repeated authorization；
    
- symlink escape。
    

## Abaqus 环境测试

只在明确授权环境执行：

- CAE export；  
    -真实 solver；
    
- ODB read；
    
- version probe；
    
- artifact manifest；
    
- end-to-end evidence freeze。
    

---

# 9. 项目治理

## 核心不可违反规则

1. 不允许生产 subprocess 绕过 Executor。
    
2. 不允许生产写入绕过 Workspace。
    
3. 不允许接受无 provenance 的 artifact。
    
4. 不允许 LLM 生成领域 PASS。
    
5. 不允许固定 pipeline 依赖 LLM。
    
6. 不允许授权自动扩展到其他动作。
    
7. 不允许修改 immutable source。
    
8. 不允许测试 fixture 被声明为真实物理证据。
    
9. 不允许报告文本替代底层 evidence。
    
10. 不允许 UI 或 Skill 成为安全边界。
    

## 变更要求

涉及以下内容必须增加 ADR：

- 新风险等级；
    
- 新生产工具；
    
- 新外部 subprocess；
    
- 新 source write 权限；
    
- 新最终 verdict；
    
- 新 evidence freeze 规则；
    
- 新 adapter；
    
- 新自动授权机制。
    

---

# 10. 项目成功标准

AegisCAE Runtime 成功的标准不是“模型能自动跑 Abaqus”，而是：

- 每项动作都有明确工具和 schema；
    
- 每个高风险动作都有授权；
    
- 每次执行都有唯一上下文；
    
- 每个 artifact 都有身份与来源；
    
- 每个结果都有完整性验证；
    
- 每个领域 verdict 都能被复核；
    
- 每次失败都不会污染基准；
    
- 每次运行都可恢复或明确隔离；
    
- 上层模型可替换；
    
- 没有 LLM 时系统仍然成立。
    

---

# 11. 最终决策

项目不再以 `AbqPilot` 作为总名称。

建议采用：

```text
AegisCAE Runtime
```

原项目调整为：

```text
AegisCAE Runtime
├── Runtime Core
├── Validation and Evidence Engine
├── Interfaces
└── Abaqus Adapter
    └── abqpilot compatibility package
```

总体路线确定为：

> 先建立独立、确定性、不可绕过的 Controlled CAE Runtime，再通过 JSON CLI、MCP 和 Skill 接入 Codex 等可替换上层智能客户端。

任何 LLM 都只是 AegisCAE Runtime 的调用者，不是执行权威、验证权威或证据权威。