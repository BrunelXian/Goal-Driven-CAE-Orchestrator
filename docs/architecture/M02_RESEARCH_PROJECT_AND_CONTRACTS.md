# M02-A — ResearchProject 与冻结合同

实现范围：本地、独立的科研状态与声明合同。沿用 ADR-003/004 的权威分离；Codex 是 Agent Harness，GD-CAE 持有科研声明，AbqJobPilot 才是未来获得授权后的执行所有者。本模块不导入 AF、MCP、Agent SDK，不执行 Solver，也不签发批准。

## 模块及公开行为

| 模块 | 已实现职责 |
|---|---|
| `aegiscae.contracts.research_contracts` | 冻结 dataclass DTO、严格字段/类型检查、Decimal 字符串、规范 JSON、分段与 Bundle SHA-256 |
| `aegiscae.research.project` | 独立根目录创建、显式只读/写打开、SQLite 原子冻结、重读校验、审计分页、合成文件身份核对 |
| `aegiscae.research.__init__` | 包边界，无启动副作用 |

API：`create_research_project(explicit_new_root, descriptive_name, declared_af_binding=None)` 返回只读句柄；`open_existing_readonly(root)` 不创建、迁移或修复；`open_existing_for_explicit_write(root)` 才允许 `freeze_contract_bundle(bundle, expected_revision, idempotency_key)` 与调用方失败观察记录。模块级 `freeze_contract_bundle(root, ...)` 是同一明确写入路径。句柄还提供 `inspect()`、`read_frozen_bundle(digest)`、`audit_events(after_sequence, limit)`。

必须传入绝对根目录，不查找 CWD/Recent。新根目录不得存在；祖先不得是仓库、AF Project 或另一 ResearchProject。检查路径穿越、Windows 特殊路径、symlink/reparse、文件硬链接、数据库大小及文件身份。创建失败留下隔离目录，不清理或自动复用。路径守卫不构成操作系统沙箱，不能阻止同权限恶意替换竞态。

## 持久化数据与身份

单一 `research.sqlite3`，四张表：

- `project`：唯一元数据规范 JSON 和摘要。包含 schema=1、`rp_` ID、revision、UTC 创建时间、`sg_` storage generation、根路径摘要、根及数据库 file identity、名称、phase、声明绑定，以及创建/最近 revision 的 `tx_` 事务 ID 和最近 revision 时间。
- `parts`：`(kind, contract_id, version)` 主键，三类合同的规范 JSON 与摘要。
- `bundles`：Bundle ID/version、内容摘要及字节、唯一 revision、幂等键、冻结 UTC、唯一事务 ID、元数据摘要。
- `audit`：连续 sequence、规范事件字节、事件摘要；事件含 previous digest、kind、revision、UTC、事务 ID、Bundle/元数据摘要、code 和 provenance。

根路径仅存摘要，不存完整私有路径。移动、复制目录或替换数据库文件将导致身份失配；没有迁移/恢复身份的隐式后门。声明 AF 绑定只接受 project ID、instance ID、context digest、协议和 capability version，状态始终为 `BOUND_DECLARED`，不保存连接凭据、进程身份或执行记录。

创建和冻结各生成一个 UTC 与事务 ID，在所属 Project revision、冻结记录和审计事件之间共享。冻结元数据摘要覆盖 Project ID、Bundle 内容摘要、revision、幂等键、UTC 和事务 ID。重读检查字段集合、真实日历时间、事务 ID 格式/唯一性、连续 revision、各表对应关系、审计顺序/摘要链及 provenance。不会仅凭某个摘要相等就跳过其他关系检查。

审计序号与 revision 表示先后关系；UTC 来自本机普通时钟，可能回拨，不是可信时间源。SHA-256 和摘要链用于检测不一致，不是签名、身份认证或不可篡改证明。有数据库写权限的人仍可协调重写所有关联记录和摘要。

## 合同结构

所有 DTO 以 `ContractBundle.from_dict` 严格构造；拒绝未知/缺失字段、重复 JSON key、错误类型（包括 bool 冒充 int）、浮点及非有限数。规范 JSON 排序 key、ASCII 编码、紧凑分隔，不对数组重新排序。输入有深度、节点数、字符串、集合及 64 KiB 合同限制。

| 合同 | 主要字段及约束 |
|---|---|
| GoalContract | Project/goal/version；目标 metric/component、instance/entity kind/entity ID、step、frame、可选匹配时间；comparator、target/tolerance；hard constraints；允许/禁止变更类别；证据类别；UNKNOWN=BLOCK；solver/candidate 上限；可选未来 auto-Turn 上限及 NOT_ENFORCED；不可信 approval_source 标签 |
| ModelContract | baseline/version、artifact 清单（ID、角色、SHA-256、size、来源标签、来源类型、依赖 ID）；单位；实体与 step/frame/time；各类语义假设、适用范围、允许变更；closure=DECLARED_ONLY/INCOMPLETE、semantic_status=DECLARED_ONLY |
| VerificationContract | verification/version；V0–V3 必选、V4 显式布尔；精确证据 selector/单位；目标 tolerance；逐项硬约束规则；V0–V4 validator ID/version/digest；可选物理参考和适用域；UNKNOWN=BLOCK |
| ContractBundle | schema、bundle/version、Project ID、三份合同；三份分段摘要和整体摘要 |

Quantity 是 `{value: 十进制字符串, dimension, unit}`；通过 Decimal 验证，不转换成 float。拒绝指数写法、前导零、尾随小数零、负零、NaN/Infinity、负 tolerance、隐式单位转换。当前只接受一致的 N-mm-MPa-s 或 N-m-Pa-s 组合；目标量支持 displacement/stress/reaction_force/strain 的有限组件集合。未来扩展需增加显式合同版本设计。

硬约束采用**必须完整覆盖才能冻结**的策略。每个 `ScientificConstraint.constraint_id` 必须恰有一个 `HardConstraintCheck`，`level="V3"`，并携带与原约束完全相同的 `rule`（包含 selector、comparator、threshold、tolerance）。其 evidence 必须出现在 `required_evidence`。遗漏、重复、未知 ID、降级 level、改规则或漏证据均拒绝；不完整草案不会进入冻结库。读取的 `COMPLETE_DECLARED` 只表示声明覆盖完整，不是验证通过。

以下为合同片段，完整可执行合成示例见 `tests/unit/test_research_project.py::proposal`；片段不能独立冻结：

```json
{
  "constraint_id": "tip_limit",
  "level": "V3",
  "rule": {
    "constraint_id": "tip_limit",
    "evidence": {
      "metric_id": "displacement", "component": "U1", "dimension": "length", "unit": "mm",
      "selector": {"instance": "Beam", "entity_kind": "NODE_SET", "entity_id": "Tip",
                   "step": "Load", "frame": 1, "time": null}
    },
    "comparator": "LE",
    "threshold": {"value": "1", "dimension": "length", "unit": "mm"},
    "tolerance": {"value": "0.01", "dimension": "length", "unit": "mm"}
  }
}
```

示例使用合成七字节 `fixture` 的摘要、声明的 Beam/Tip/Load、零 solver 预算、两次候选提议上限和缺失物理参考；它没有真实模型或验证器执行能力。新建 Project 后，示例的四个 Project ID 必须使用实际创建的 ID。

## 事务、幂等及中断

冻结在 `BEGIN IMMEDIATE` 下重新读取/校验状态，然后检查幂等键，再比较 expected revision。相同键和内容返回原摘要/revision（`replayed=true`），即使调用方 expected revision 已旧；同键不同内容显式冲突。新冻结原子写入 Bundle、三份 parts、Project revision 和审计记录。已存在合同 ID/version 只能复用相同字节；变更必须提升对应合同及 Bundle 版本，不能原位覆盖。

两个通过文件预检的并发 SQLite 连接由写锁串行化，一个提交，另一个得到 `REVISION_CONFLICT`。如果后来的调用在预检时看到 journal，则更早返回 `STORE_BUSY`；调用方在前一提交完成后明确重试才得到 revision 冲突。此里程碑没有自动重试、等待队列或通用恢复服务。

注入异常会回滚整个事务；提交后的异常代表响应丢失，必须以幂等键重放确认结果。硬退出可能留下 journal，产品保守拒绝打开且不更改文件。测试另用受控 SQLite 检查完整旧状态；这不是产品恢复功能，也不保证崩溃后立即可读。创建中断目录同样隔离。未来恢复设计必须单独授权。

失败的只读打开不会向原库写入。调用者可在另一份有效、显式写打开的 Project 上记录固定错误码 `REOPEN_FAILURE_OBSERVED`；provenance 是 `CALLER_REPORTED`，不能冒充系统已证实的异常原因或批准。普通校验失败使用固定错误码；部分路径检查的原生 OS 权限/IO 异常目前可能外溢，不应对外直接传播原始异常。

## 文件、摘要和权限边界

`check_pinned_artifact_identity` 只接受显式列出的 `SYNTHETIC_TEST_ONLY` `.txt` 文件，不跟随 INP include、不解析 CAE、不搜索磁盘。比较大小、SHA-256 与前后文件状态：变更→STALE，缺失/未声明依赖→INCOMPLETE，字节相同→BYTES_MATCH_DECLARED。字节相同仍不证明依赖闭包、语义或物理有效。

`inspect` 只返回白名单状态，不返回自由文本名称/approval_source/模型声明或完整路径。完整合同读取标明 `UNTRUSTED_DECLARATIONS`；消费方必须把其中提示语当数据。字符串过滤是最小防误传措施，不是通用秘密检测或 DLP。

冻结后始终 `CONTRACT_FROZEN_PENDING_APPROVAL`、human approval=`NOT_ESTABLISHED`、numerical=`NOT_RUN`、physics/V4=`NOT_ASSESSED`、execution authorized=false、budget enforcement=`NOT_IMPLEMENTED`。即使提供物理参考或填写批准标签也不升级这些状态。

未实现：真实人工批准、Solver Grant、VerificationRecord 执行、Goal verdict、Model mutation、BudgetLedger、Candidate 工作流、MCP 写工具、AF submit、Skills 扩展、事件桥/SDK 恢复 Turn。现有七个 MCP 工具及 M01 导入方向保持只读。
