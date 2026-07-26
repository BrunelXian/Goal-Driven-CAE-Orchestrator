# LEGACY_MIGRATION_DECISIONS

## 1. Document Metadata

```text
document: LEGACY_MIGRATION_DECISIONS.md
decision date: 2026-07-26
target project: AegisCAE Runtime
decision type: legacy migration architecture decision
source project 1: Abaqus Job Pilot / AbqJobPilot
source project 2: AbqPilot / AbqPilot-v2
source basis:
  - AegisCAE Runtime 项目计划书.md
  - LEGACY_ABQJOBPILOT_SUMMARY.md
  - LEGACY_ABQPILOT_SUMMARY.md
decision status: APPROVED_FOR_MILESTONE_0
migration mode: selective extraction and refactor
whole-repository copy: PROHIBITED
legacy direct dependency: NOT RECOMMENDED
```

---

# 2. Executive Decision

AegisCAE Runtime 将建立为一个新的、独立的 **Controlled CAE Runtime**。它不在 AbqJobPilot 或 AbqPilot 旧仓库中继续叠加新 Stage，也不通过简单重命名旧 package 获得。

最终迁移裁决如下：

1. **AbqJobPilot** 定位为 `Abaqus Job Lifecycle Adapter` 的 legacy reference，保留其 Abaqus command construction、日志分类、顺序作业语义和部分监控逻辑，但不迁移其 GUI 驱动执行、本地无锁 JSON queue、硬编码路径和直接 `Popen` 运行方式。
2. **AbqPilot** 定位为 `Abaqus Domain Adapter` 的主要 legacy source，保留其窄范围 INP patch、StaticValidator、DiffGuard、PhysicsGuard、Abaqus diagnosis、solver preflight/approval、ODB extraction contract 和部分 pipeline 测试，但不迁移其 Stage-driven architecture、分散的执行走廊、public raw launcher、placeholder rollback、Stage-only workspace guard 和非防篡改 evidence freeze。
3. **AegisCAE Runtime Core** 必须重新实现。旧项目中的 `RunContext`、`TaskWorkspace`、`workspace_guard`、runner loop、authorization lifecycle、rollback 和 evidence authority 都不能直接成为新 Runtime 的控制平面。
4. 新项目不直接依赖旧仓库。迁移采用 **copy-by-selection, refactor-behind-new-contracts**：先在新仓库定义 Runtime contract，再提取纯函数、解析器、验证规则和 adapter-specific 代码。
5. `agent/runtime-foundation-v01` 不合并为旧 AbqPilot 的下一 Stage。其 `Context / ControlledWorkspace / Executor` 思路可作为新项目设计参考，但代码需要在新命名、新目录和新 contract 下重新审查后迁入。
6. Codex、Grok、Claude 或其他模型只作为可替换的 Planner/Client。任何 LLM 都不拥有执行、授权、ODB acceptance、物理 verdict 或 evidence freeze 权限。
7. AegisCAE Runtime 的首个正式 adapter 是 Abaqus。Ansys、CalculiX 等只保留未来扩展点，不进入第一阶段实现范围。

最终判定：

```text
LEGACY_MIGRATION_APPROVED:
  selective extraction only
  no direct legacy dependency
  no whole-repository rename
  no Stage-driven continuation
  Runtime Core rebuilt from new invariants
  Abaqus capabilities migrated behind adapter contracts
```


---

# 3. Source Project Verdicts

## 3.1 AbqJobPilot

```text
legacy maturity: USEFUL_LEGACY_ASSET
recommended new role: Abaqus Job Lifecycle Adapter
continue legacy development: maintenance only
direct dependency: NO
migration method: selective extraction + schema refactor
```

AbqJobPilot 的真实价值集中在本地 Abaqus `.inp` 批量作业生命周期：

- command list construction；
- datacheck/full-run 区分；
- latest-attempt log parsing；
- fatal/success classification；
- 基本 queue/job 字段；
- 顺序执行语义；
- `.sta/.log/.msg/.dat` 读取；
- 简单 tail 和报告输出。

其主要问题是：

- GUI 直接控制 runner；
- `run_next_job()` 可直接触发 Abaqus；
- 本地 JSON queue 无 schema、锁、lease、retry 和 crash recovery；
- 无 timeout；
- ODB 仅检查存在和大小；
- 无 artifact provenance；
- 默认路径和 runtime 目录硬编码；
- 无正式 CLI/API。

因此，AbqJobPilot 不迁移为 Runtime，也不迁移为独立 queue subsystem。它只提供 Abaqus job adapter 的领域经验与少量可重构代码。

## 3.2 AbqPilot

```text
legacy maturity: STAGE_DRIVEN_PROTOTYPE
recommended new role: Abaqus Domain Adapter source
continue legacy development: NO
direct dependency: NO
migration method: extract pure modules, refactor behind new Runtime contracts
```

AbqPilot 已经超越“LLM + arbitrary scripts”，因为它存在：

- narrow controlled heat-flux patch；
- StaticValidator；
- DiffGuard；
- PhysicsGuard；
- sanity-base traceability；
- hash-bound approval；
- fixed solver command；
- job/log diagnosis；
- gated ODB metrics extraction；
- resumable fixed pipeline；
- 大量 mock/fixture/contract tests。

但它不是统一 Controlled CAE Runtime，原因是：

- Context 分裂；
- Workspace guard 只覆盖局部 Stage；
- 多个 subprocess 入口；
- public raw launcher；
- 无 central Tool Registry；
- 无统一 risk policy；
- rollback 只是 placeholder；
- ODB freshness/identity/required-field acceptance 不完整；
- evidence freeze 非 tamper-evident；
- Stage 5 大量 preview、draft、fixture、GUI card 和文档型进展；
- GUI、CLI、solver、DFLUX、ODB、demo 各自形成执行走廊。

因此，AbqPilot 应冻结为 legacy reference，不再继续追加新 Stage。


---

# 4. Migration Principles

## 4.1 Runtime-first

新项目先建立：

```text
AegisContext
ControlledWorkspace
Unified Executor
Authorization
Session / Workflow
Artifact Provenance
Validator
Evidence Recorder
```

然后才迁移 Abaqus 领域能力。

不得先复制旧 adapter，再补安全边界。

## 4.2 New contracts before old code

每个旧模块迁移前必须先定义：

- input schema；
- output schema；
- risk level；
- allowed read/write scopes；
- authorization requirement；
- idempotency semantics；
- timeout；
- failure model；
- evidence events；
- acceptance tests。

旧代码只能作为实现参考，不能作为 contract 来源。

## 4.3 No whole-repository migration

禁止以下做法：

```text
copy AbqPilot repository
→ rename package to aegiscae
→ continue adding stages
```

也禁止：

```text
add AbqJobPilot as dependency
→ call legacy runner directly
```

新项目必须是独立 repository、独立 package 和独立 test suite。

## 4.4 Immutable source first

AegisCAE Runtime 的 baseline protection 采用：

```text
immutable source
→ clone to staging
→ modify candidate
→ validate
→ execute
→ promote or quarantine
```

不以通用 rollback 作为首要保护方式。

## 4.5 Domain verdicts remain deterministic

以下 verdict 只能由 Runtime/Validator 产生：

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

旧报告中的固定 PASS、Markdown verdict、GUI preview PASS 和 smoke PASS 不迁移为 machine truth。

## 4.6 Legacy tests are evidence, not authority

旧测试可用于确认原始行为，但迁移后的模块必须重新建立新 contract 测试。

尤其不得把以下测试当成生产证据：

- fixture INP；
- mock subprocess；
- preview-only gate；
- documentation assertion；
- GUI card smoke；
- no-execution smoke；
- mock ODB extraction。


---

# 5. Target Ownership Boundary

## 5.1 Runtime Core ownership

以下能力必须由 AegisCAE Runtime Core 独占：

| Capability | New owner |
|---|---|
| context and identity | `aegiscae.runtime.context` |
| project/session/run lifecycle | `aegiscae.runtime.session` |
| workspace and path authorization | `aegiscae.runtime.workspace` |
| external process execution | `aegiscae.runtime.executor` |
| risk policy | `aegiscae.runtime.policy` |
| authorization lifecycle | `aegiscae.runtime.authorization` |
| tool registration | `aegiscae.runtime.registry` |
| plan/state machine | `aegiscae.runtime.workflow` |
| checkpoint/staging/promotion/quarantine | `aegiscae.runtime.checkpoint` |
| artifact provenance | `aegiscae.runtime.artifacts` |
| event ledger and evidence freeze | `aegiscae.runtime.evidence` |
| final machine verdict | Runtime Validator / Evidence authority |

任何 adapter、GUI、CLI 或 LLM client 都不得重新实现这些能力。

## 5.2 Abaqus Adapter ownership

以下能力属于 Abaqus Adapter：

| Capability | New owner |
|---|---|
| Abaqus executable/command semantics | `aegiscae.adapters.abaqus.commands` |
| datacheck/full-run command plans | `aegiscae.adapters.abaqus.jobs` |
| CAE noGUI export adapter | `aegiscae.adapters.abaqus.cae` |
| INP inspection and controlled patch | `aegiscae.adapters.abaqus.inp` |
| `.sta/.msg/.dat/.log/.lck` parsing | `aegiscae.adapters.abaqus.diagnostics` |
| ODB read-only bridge | `aegiscae.adapters.abaqus.odb` |
| field/step/frame contracts | `aegiscae.adapters.abaqus.contracts` |
| Abaqus-specific validators | `aegiscae.adapters.abaqus.validation` |
| Abaqus metrics | `aegiscae.adapters.abaqus.metrics` |

Adapter 只能返回结构化 plan/result，不得直接执行 subprocess 或写入未授权路径。

## 5.3 Interface ownership

| Interface | Decision |
|---|---|
| Python SDK | REQUIRED |
| JSON CLI | REQUIRED after Runtime contracts stabilize |
| MCP adapter | DEFER until JSON CLI/schema stabilizes |
| Codex Skill | DEFER until Runtime is independently functional |
| GUI/TUI | DO NOT MIGRATE; design later as read-only client first |
| legacy command console | optional compatibility layer only |


---

# 6. Master Migration Matrix

## 6.1 AbqJobPilot Decisions

| Legacy component | Legacy path | Decision | Rationale | Proposed target | Required migration tests |
|---|---|---|---|---|---|
| Abaqus command prefix handling | `abqjobpilot/runner_core.py` | REFACTOR | `.bat/.cmd` handling and list construction are useful; legacy function is coupled to runner/settings | `adapters/abaqus/commands.py` | no shell string; executable policy; `.bat` plan; missing executable; version probe |
| datacheck command builder | `runner_core.py` | KEEP LOGIC / REWRITE API | datacheck excludes GPU parameter and has tests | `adapters/abaqus/jobs.py` | datacheck has no `gpus`; CPU range; exact command plan |
| full-run command builder | `runner_core.py` | KEEP LOGIC / REWRITE API | core Abaqus lifecycle knowledge | `adapters/abaqus/jobs.py` | job/input/cpu/interactive fields; no arbitrary args |
| latest-attempt log extraction | `parsers.py` | KEEP / REFACTOR | solves old-log contamination | `adapters/abaqus/diagnostics.py` | multiple attempts; stale log; encoding; evidence spans |
| fatal/success classifier | `parsers.py` | REFACTOR | useful taxonomy but must return structured evidence and reason codes | `adapters/abaqus/diagnostics.py` | fatal patterns; exclusions; missing files; contradictory evidence |
| monitor tail helpers | `monitor.py` | KEEP / REFACTOR | pure read-only helpers | `adapters/abaqus/diagnostics.py` | missing file; encoding; bounded tail |
| queue item field model | `queue_store.py` | REFACTOR | fields are useful domain vocabulary but ordinary dict is unsafe | `adapters/abaqus/contracts.py` | versioned schema; migration fixtures; validation |
| local JSON queue | `queue_store.py` | REPLACE | no lock/lease/retry/idempotency | Runtime workflow/session store | concurrent claim; stale lease; retry; idempotency |
| QueueRunner loop | `runner_core.py` | REPLACE | direct `Popen`, no timeout, no Runtime authorization | Runtime workflow + Unified Executor | timeout; cancellation; restart; authorization; evidence |
| `run_next_job()` | `runner_core.py` | DO NOT MIGRATE | direct public execution bypass | none | architecture test forbids direct adapter execution |
| GUI | `gui_app.py` | DO NOT MIGRATE | tightly coupled, Windows-specific side effects, direct execution | archive only | none |
| shutdown/taskmgr/resource UI | `gui_app.py` | DO NOT MIGRATE | outside Runtime scope | none | none |
| internal Agent Command parser | `command_parser.py` | LEGACY COMPAT ONLY | whitelist parser is useful only for old operator compatibility | `legacy_compat/abqjobpilot_command.py` | parse/reject; must only create request objects |
| settings store | `settings_store.py` | REPLACE | GUI-local JSON config is not Context | `runtime/config.py` | precedence; schema; no hidden globals |
| JSON atomic write helper | `utils.py` | REASSESS / REIMPLEMENT | temp replace pattern useful, but new store needs locking/hash/events | Runtime storage utility | crash simulation; atomicity; hash |
| legacy report JSON | `runner_core.py` | REPLACE | no provenance/hash/evidence authority | `runtime/evidence.py` | manifest hash; event linkage |

## 6.2 AbqPilot Decisions

| Legacy component | Legacy path | Decision | Rationale | Proposed target | Required migration tests |
|---|---|---|---|---|---|
| `RunContext` | `abqpilot/core/run_context.py` | REPLACE | only five path fields; not runtime authority | `runtime/context.py` | serialization; versioning; root identity; restore |
| `TaskWorkspace` | `core/task_workspace.py` | REPLACE / SALVAGE CONCEPTS | persistence/resume ideas useful, but roots and state ownership fragmented | `runtime/session.py` | resume; partial state; run isolation |
| `PipelineRunner` | `core/pipeline_runner.py` | REPLACE / COMPAT ADAPTER | fixed step/resume behavior useful, but Stage-bound | `runtime/workflow.py` + `legacy_compat` | authorized plan; restart; skip/fail/manual review |
| `StateMachine` | `core/state_machine.py` | REFACTOR CONCEPTS | explicit transitions useful, but incomplete lifecycle | `runtime/workflow.py` | illegal transition; quarantine; recovery |
| `workspace_guard` | `abqpilot/workspace_guard.py` | REPLACE | hard-coded roots and local Stage integration | `runtime/workspace.py` | traversal; symlink; source immutability; external paths |
| Runtime Foundation `AbqPilotContext` | remote PR | REFACTOR SEED | correct direction, incomplete identities and compatibility root aliasing | `runtime/context.py` | new project contract tests |
| Runtime Foundation `ControlledWorkspace` | remote PR | REFACTOR SEED | useful API direction, but compatibility mode aliases roots | `runtime/workspace.py` | separated scopes; immutable source |
| Runtime Foundation `ControlledExecutor` | remote PR | REFACTOR SEED | correct unified-entry direction; authorization is not consumed/validated generically | `runtime/executor.py` | plan/tool/auth binding; version probe; event ledger |
| public raw solver launcher | `solver/controlled_abaqus_runner.py` | DO NOT MIGRATE | CRITICAL bypass | none | architecture scan forbids public raw launcher |
| solver command/preflight | `solver/solver_preflight.py` | REFACTOR | fixed command, CPU and hash checks useful | `adapters/abaqus/jobs.py` | command plan; hash; CPU; executable/version |
| solver approval hash binding | `solver/solver_approval.py`, `core/approval.py` | REFACTOR | useful binding, weak lifecycle | `runtime/authorization.py` | unique ID; single-use; revoke; expiry; plan/tool binding |
| solver monitor | `solver/solver_monitor.py` | KEEP / REFACTOR | useful status classification | `adapters/abaqus/diagnostics.py` | completion/failure/lock/timeout |
| job/ODB diagnosis | `diagnostics/job_odb_diagnosis.py` | KEEP / REFACTOR | strong pure parser asset | `adapters/abaqus/diagnostics.py` | stale/wrong-job/readability separation |
| CAE exporter | `cae/cae_inp_exporter.py` | REFACTOR | useful noGUI adapter; direct paths/subprocess must be removed | `adapters/abaqus/cae.py` | Context/Workspace/Executor integration |
| ODB script writer | `odb/abaqus_odb_script_writer.py` | KEEP / REFACTOR | read-only ODB bridge knowledge | `adapters/abaqus/odb.py` | corrupt ODB; step/frame/field identity |
| ODB metrics extractor | `odb/odb_metrics_extractor.py` | REFACTOR | useful contract; missing-fields PASS risk | `adapters/abaqus/odb.py` | mandatory field rejection; freshness; provenance |
| INP InventoryTool | `tools/inventory*` | KEEP / REFACTOR | pure inspection asset | `adapters/abaqus/inp.py` | malformed INP; read scope |
| HeatFluxPatchBuilder | `builders/heat_flux_patch_builder.py` | REFACTOR | narrow controlled mutation valuable | `adapters/abaqus/inp.py` | declared edit; unchanged source; staging only |
| StaticValidator | `tools/static_validator_tool.py` | KEEP / REFACTOR | deterministic validator | `adapters/abaqus/validation.py` | schema/path integration |
| DiffGuard | `tools/diff_guard_tool.py` | KEEP / REFACTOR | declared-edit isolation is core domain asset | `adapters/abaqus/validation.py` | unrelated changes; normalized diff |
| PhysicsGuard | `tools/physics_guard_tool.py` | KEEP / REFACTOR | useful fail-closed composition | `adapters/abaqus/validation.py` | policy source; warning/manual review |
| MCPGuard / condition preservation | `guards/*` | REFACTOR | important but narrow and schema-specific | `adapters/abaqus/validation.py` | lifecycle preservation corpus |
| arbitrary Python/INP builder placeholders | `builders/abaqus_python_builder.py`, `generative_inp_builder.py` | DO NOT MIGRATE | unsupported capability and confusing surface | none | none |
| repair planner | `analysis/*` | REFACTOR | deterministic advisory logic useful | `adapters/abaqus/metrics.py` or domain package | no direct mutation; traceable inputs |
| ArtifactRegistry | `core/artifact_registry.py` | REPLACE / SALVAGE FIELDS | path inventory is not provenance | `runtime/artifacts.py` | hashes; identities; roles; lifecycle |
| evidence freeze | `analysis/evidence_freeze.py` | REPLACE | constant verdict, byte/path manifest, no tamper evidence | `runtime/evidence.py` | SHA-256; append-only ledger; mutation detection |
| RollbackManager | `core/rollback_manager.py` | DO NOT MIGRATE | placeholder only | new staging/checkpoint design | source unchanged; quarantine |
| ACOM | `acom/*` | DO NOT MIGRATE INTO CORE | useful historical governance, but Markdown choreography is not runtime | archive / optional legacy_compat | none initially |
| NARM | docs only | DO NOT MIGRATE | not verified implementation | none | none |
| optional LLM provider | `llm/*` | DEFER / CLIENT LAYER ONLY | not core Runtime | future client integration | Runtime independent of model |
| GUI Stage modules | `gui/*` | DO NOT MIGRATE | Stage-heavy, duplicate execution clients | archive | none |
| Stage docs/RUN/HANDOFF/GATE corpus | docs/runs | ARCHIVE ONLY | historical evidence, not new architecture | legacy archive | none |
| legacy CLI | `cli.py` | DO NOT COPY WHOLESALE | mixed responsibilities and Stage commands | new JSON CLI later | structured exit codes; dry-run default |
| old tests | `tests/` | SELECTIVE PORT | many valuable pure tests; many preview/doc tests not useful | new tests by module | new contract assertions |


---

# 7. KEEP / REFACTOR / REPLACE / DO NOT MIGRATE Summary

## 7.1 KEEP

“KEEP” 表示保留领域逻辑和测试意图，不表示逐文件原样复制。

优先保留：

1. AbqJobPilot latest-attempt parser。
2. AbqJobPilot datacheck/full-run command semantics。
3. AbqJobPilot fatal/success pattern corpus。
4. AbqPilot StaticValidator。
5. AbqPilot DiffGuard。
6. AbqPilot PhysicsGuard。
7. AbqPilot INP inventory logic。
8. AbqPilot job/log diagnosis taxonomy。
9. AbqPilot read-only ODB extraction script concepts。
10. approval hash-binding concept。
11. source-candidate traceability concept。
12. fixed pipeline resume test scenarios。

## 7.2 REFACTOR

必须迁入新 contract 后才能使用：

1. Abaqus command builder。
2. solver preflight。
3. CAE export。
4. ODB extractor。
5. controlled INP patch。
6. model-condition preservation。
7. solver monitoring。
8. job request/status schemas。
9. authorization。
10. artifact registry。
11. repair plan。
12. fixed pipeline compatibility。
13. parser outputs and reason codes。
14. atomic JSON storage ideas。
15. Runtime Foundation branch concepts。

## 7.3 REPLACE

新 Runtime 中重新实现：

1. `RunContext`。
2. `TaskWorkspace` 的控制平面职责。
3. local JSON queue。
4. runner loop。
5. settings store。
6. workspace guard。
7. authorization lifecycle。
8. checkpoint/staging/promotion。
9. evidence freeze。
10. plan/state machine。
11. report-to-verdict chain。
12. artifact identity/provenance store。
13. CLI。

## 7.4 DO NOT MIGRATE

禁止进入新 Runtime：

1. public raw subprocess launcher。
2. `run_next_job()` 式直接执行 API。
3. placeholder RollbackManager。
4. GUI 直接控制 solver。
5. shutdown/taskmgr/resource UI。
6. Stage-driven preview/card architecture。
7. 大量 Stage 5 draft/fixture/smoke 模块。
8. ACOM Markdown handoff choreography 作为核心 Runtime。
9. NARM 文档概念。
10. arbitrary model/Python generation placeholders。
11. fixed PASS/FROZEN Markdown verdict。
12. hard-coded repository roots。
13. implicit CWD。
14. test fixture 被当成物理 evidence。
15. unversioned ordinary-dict queue contract。
16. GUI messagebox 作为 authorization。
17. Skill/Prompt 作为安全边界。


---

# 8. Repository and Package Strategy

## 8.1 New repository

建议建立新仓库：

```text
repository: AegisCAE-Runtime
python package: aegiscae
```

旧仓库处理：

```text
BrunelXian/abq_job_pilot:
  status: legacy maintenance / archived reference
  new architecture development: NO

BrunelXian/AbqPilot:
  status: frozen legacy reference
  new Stage development: NO
```

## 8.2 Legacy dependency policy

新项目不在 `pyproject.toml` 中依赖：

```text
abqjobpilot
abqpilot
```

迁移代码必须：

1. 在旧仓库定位具体函数和测试；
2. 在新项目创建对应 contract；
3. 提取最小实现；
4. 重写 import、path、state 和 execution boundary；
5. 增加 provenance 和 policy；
6. 通过新测试；
7. 记录来源和修改说明。

## 8.3 Compatibility package

`abqpilot` compatibility package 不是 Milestone 0–2 的必需项。

只有在新 Abaqus Adapter 稳定后，才考虑：

```python
from abqpilot import ...
```

映射到：

```python
from aegiscae.adapters.abaqus import ...
```

兼容层不得包含：

- subprocess；
- direct writes；
- approval；
- verdict；
- GUI；
- hidden state。


---

# 9. Runtime Foundation PR Decision

对象：

```text
origin/agent/runtime-foundation-v01
Draft PR #1
```

裁决：

```text
merge into legacy main: NO
archive/delete immediately: NO
use as design seed: YES
copy wholesale into new project: NO
```

可吸收：

- versioned serializable Context 思路；
- separated Runtime package；
- ControlledWorkspace API 方向；
- unified Executor 方向；
- solver runner 路由到 Executor；
- unknown tool / wrong executable / path escape tests。

必须修正：

- `AbqPilotContext` 更名为 `AegisContext`；
- compatibility helper 不得把 source/staging/output/evidence 全部指向同一 run dir；
- authorization 必须由 Runtime service 验证和消费；
- Executor 必须绑定 plan step、tool definition 和 risk policy；
- 所有 CAE/ODB/solver subprocess 都必须统一迁移；
- Context 需增加 artifact identities、policy digest、adapter version 和 provenance；
- 测试必须在新项目实际运行，不沿用 PR 中“未运行”的状态。


---

# 10. Legacy Freeze Policy

## 10.1 AbqJobPilot

允许：

- 修复阻止旧 GUI 正常使用的 bug；
- 修复严重数据损坏风险；
- 文档标记 legacy 状态；
- 记录已知限制。

禁止：

- 增加新 Runtime Core；
- 增加新 queue architecture；
- 增加 MCP；
- 增加智能 Agent；
- 扩展为多求解器平台；
- 将新项目代码反向堆入旧仓库。

特别注意：AbqJobPilot 审计时 working tree 已存在修改和未跟踪测试。迁移前必须由用户单独确认哪些未提交改动代表有效资产，不能仅以审计 commit 为唯一来源。

## 10.2 AbqPilot

允许：

- 安全或文档性收尾；
- 打 tag / archive；
- 保存 Runtime Foundation PR 供参考；
- 导出 legacy source map。

禁止：

- 新增 Stage 5.x/6.x；
- 合并 Runtime Foundation 作为另一旧 Stage；
- 继续 GUI preview 链；
- 继续扩展 ACOM；
- 新增 execution corridors；
- 把 AegisCAE Runtime 建在旧 package 下。


---

# 11. Migration Batches

## Batch 0 — Architecture Freeze and New Repository

### Objective

建立新项目骨架和不可违反规则，不迁移运行代码。

### Deliverables

```text
ARCHITECTURE.md
RUNTIME_INVARIANTS.md
THREAT_MODEL.md
ADR-001-runtime-first.md
ADR-002-legacy-selective-migration.md
LEGACY_MIGRATION_DECISIONS.md
pyproject.toml
src/aegiscae/
tests/
```

### Acceptance

- 新 repository 与旧仓库独立；
- package 名为 `aegiscae`；
- 无 `subprocess`；
- 无 Abaqus 执行；
- 无 legacy dependency；
- invariants 测试/静态规则存在。

### Abaqus required

NO。

## Batch 1 — Runtime Control Plane

### Objective

实现新 Runtime 最小可信执行边界。

### Modules

```text
runtime/context.py
runtime/workspace.py
runtime/policy.py
runtime/authorization.py
runtime/executor.py
runtime/events.py
```

### Legacy input

仅参考 Runtime Foundation PR 和旧 approval 逻辑。

### Acceptance

- 所有生产 subprocess 只有私有 launcher；
- adapter 无权 import raw launcher；
- source/staging/output/evidence roots 分离；
- traversal、external absolute path、symlink escape 被拒绝；
- L2 execution 无有效 authorization 时不 spawn；
- authorization single-use；
- Context 可序列化和恢复；
- event ledger 记录 request/reject/start/finish。

### Abaqus required

NO，使用 mock executable。

## Batch 2 — Pure Abaqus Contracts and Diagnostics

### Objective

迁移不产生外部副作用的 Abaqus 领域逻辑。

### Modules

```text
adapters/abaqus/contracts.py
adapters/abaqus/commands.py
adapters/abaqus/diagnostics.py
adapters/abaqus/inp_inspection.py
```

### Legacy input

- AbqJobPilot command builders；
- latest-attempt parser；
- fatal/success patterns；
- AbqPilot diagnosis；
- InventoryTool；
- StaticValidator/DiffGuard/PhysicsGuard。

### Acceptance

- pure functions only；
- no file writes outside test temp；
- structured reason codes and evidence spans；
- datacheck excludes GPU；
- stale log and contradictory evidence tests；
- malformed INP tests；
- validators return machine verdicts only from deterministic rules。

### Abaqus required

NO。

## Batch 3 — Abaqus Job Lifecycle Adapter

### Objective

建立 adapter command plan、job identity 和 controlled execution integration。

### Modules

```text
adapters/abaqus/jobs.py
adapters/abaqus/monitoring.py
adapters/abaqus/artifacts.py
```

### Legacy input

- AbqJobPilot queue/job field vocabulary；
- AbqPilot solver preflight；
- solver monitor；
- approval binding ideas。

### Acceptance

- adapter only creates `ExecutionPlan`；
- Unified Executor is sole process authority；
- CPU/timeout/version/executable checked；
- prelaunch manifest includes INP hash/job/run/time；
- old artifact collision detected；
- mock timeout/failure/cancel/restart tests；
- no direct `Popen` in adapter。

### Abaqus required

NO for first pass；controlled integration later。

## Batch 4 — ODB Provenance and Extraction

### Objective

把 ODB 从“存在的文件”升级为“有身份、可读取、满足 contract 的 artifact”。

### Modules

```text
adapters/abaqus/odb.py
adapters/abaqus/field_contracts.py
validation/provenance.py
validation/execution.py
```

### Legacy input

- AbqPilot ODB script writer；
- ODB metrics extractor；
- job/ODB diagnosis。

### Acceptance

- stale ODB rejected；
- wrong-job ODB rejected；
- corrupt/unreadable ODB rejected；
- missing required step/frame/field rejected；
- missing fields cannot produce PASS；
- extraction result bound to input/job/run manifest；
- no final physical verdict from existence alone。

### Abaqus required

Mock first；real read-only ODB test later with explicit authorization。

## Batch 5 — Controlled CAE/INP Mutation

### Objective

迁移窄范围、声明式 Abaqus model/input changes。

### Modules

```text
adapters/abaqus/cae.py
adapters/abaqus/inp.py
adapters/abaqus/validation.py
runtime/checkpoint.py
```

### Legacy input

- HeatFluxPatchBuilder；
- CAE exporter；
- DiffGuard；
- PhysicsGuard；
- MCPGuard；
- sanity-base traceability。

### Acceptance

- immutable source；
- clone to staging；
- declared editable region only；
- unrelated changes = 0；
- model-condition preservation contract；
- failed candidate quarantined；
- no arbitrary Python/model generation；
- atomic promotion after validation。

### Abaqus required

No for INP tests；real CAE export only in later authorized environment test。

## Batch 6 — Session, Workflow and Evidence

### Objective

建立可恢复工作流和 tamper-evident evidence。

### Modules

```text
runtime/session.py
runtime/workflow.py
runtime/artifacts.py
runtime/evidence.py
```

### Legacy input

- TaskWorkspace resume ideas；
- PipelineRunner tests；
- approval artifacts；
- ArtifactRegistry fields；
- evidence package report layout。

### Acceptance

- Plan–Authorize–Execute–Monitor–Validate–Report–Freeze state；
- out-of-plan execution rejected；
- partial run recoverable or quarantined；
- append-only ledger；
- SHA-256 manifest；
- post-freeze mutation detected；
- final verdict generated from validated events/artifacts；
- Markdown is view only。

### Abaqus required

NO for mock workflow；later E2E yes。

## Batch 7 — JSON CLI and Legacy Compatibility

### Objective

提供机器友好接口，不接入 LLM 内核。

### Modules

```text
interfaces/json_cli.py
interfaces/python_api.py
legacy_compat/
```

### Acceptance

- stable JSON request/response；
- versioned schemas；
- deterministic exit codes；
- dry-run default；
- legacy commands only create request objects；
- no direct solver invocation；
- no GUI dependency。

### Abaqus required

NO。

## Batch 8 — Intelligent Client Integration

### Objective

让 Codex 等模型成为 Client，而不是 Runtime。

### Deliverables

```text
Codex Skill
optional MCP adapter
client integration tests
```

### Acceptance

- model can only call structured Runtime tools；
- model cannot mutate source directly；
- model cannot override Validator verdict；
- same structured request + same Runtime/input yields same domain verdict；
- fixed pipeline works with no model；
- Skill is guidance, not security boundary。

### Abaqus required

Not initially；controlled E2E later。


---

# 12. Required Architecture Tests

新项目 CI 至少包含：

1. 禁止 adapter 调用 `subprocess.run/Popen`。
2. 禁止 public raw launcher。
3. 禁止 production code 使用 implicit CWD。
4. 禁止 hard-coded user/repository absolute paths。
5. 禁止 source scope 写入。
6. 禁止 symlink escape。
7. 禁止 unknown tool execution。
8. 禁止 out-of-plan execution。
9. 禁止 expired/reused/revoked authorization。
10. 禁止 report layer 创建 machine PASS。
11. 禁止 LLM/client module import Executor internals。
12. 禁止 missing ODB field 被判 PASS。
13. 禁止 stale artifact 被接受。
14. 禁止 fixture 被标记为 physical evidence。
15. 禁止 evidence freeze 缺少 hash manifest。
16. 禁止 post-freeze mutation 不被发现。


---

# 13. Decisions on Queueing

AbqJobPilot 的 queue 是有价值的领域经验，但新项目第一版不应优先重建通用 queue。

裁决：

```text
Milestone 0–2:
  no generic queue subsystem

Milestone 3+:
  local sequential workflow through Session/Workflow

future:
  queue adapter only if repeated concurrent workloads justify it
```

原因：

- 目前主要需求是受控单机 Abaqus 工作流；
- queue、lease、retry、license scheduling 会显著扩大 Runtime scope；
- 先建立执行、artifact identity 和 evidence 更重要；
- Abaqus license awareness 需要真实业务需求和环境证据。

如果未来实现 queue，必须具备：

- versioned job schema；
- claim/lease；
- idempotency；
- stale claim detection；
- retry policy；
- quarantine/dead-letter；
- resource/CPU policy；
- license-aware admission；
- per-run provenance；
- Unified Executor integration。


---

# 14. Decisions on Physics Validation

旧 PhysicsGuard 和 model-condition checks 可以迁移，但新项目不得把所有 physics checks 都作为同一硬门槛。

必须区分：

```text
execution validity:
  hard gate

artifact provenance:
  hard gate

required output contract:
  hard gate

physics plausibility:
  PASS / WARNING / OUT_OF_EXPECTED_RANGE / MANUAL_REVIEW / REJECTED
```

物理规则必须记录：

- rule ID；
- rule source；
- applicable adapter/domain；
- units；
- threshold；
- evidence fields；
- severity；
- whether it blocks evidence；
- version。

LLM 不得生成或修改 physics rule verdict。


---

# 15. Decisions on UI, Skill and MCP

## UI

旧 Tkinter GUI 和 Stage GUI 不迁移。

未来 UI 顺序：

1. read-only run/evidence viewer；
2. approval presentation；
3. structured request form；
4. only after Runtime maturity, controlled execution actions。

UI 不是安全边界。

## Skill

Codex Skill 只负责：

- 何时调用 AegisCAE；
- 推荐工作流；
- tool selection guidance；
- 输出解释；
- 禁止直接操作 source 的行为规范。

Skill 不负责：

- authorization；
- path permissions；
- process execution；
- ODB verdict；
- evidence freeze。

## MCP

MCP 延后到 JSON CLI/schema 稳定后。

第一机器接口：

```text
Python SDK
→ JSON CLI
→ optional MCP
```


---

# 16. Naming Decisions

正式总项目名称：

```text
AegisCAE Runtime
```

Python package：

```text
aegiscae
```

Abaqus adapter：

```text
aegiscae.adapters.abaqus
```

旧名称处理：

```text
AbqJobPilot:
  legacy project name only

AbqPilot:
  legacy project name and possible future compatibility namespace only
```

不建议新项目继续以 `Pilot` 作为总名称，因为新系统的核心身份是 Runtime authority，而不是助手。


---

# 17. Open Questions Deferred

以下问题不在本迁移决策中提前锁死：

1. 新仓库 GitHub 最终命名是否使用 `AegisCAE-Runtime` 或更短名称。
2. 首个正式 Abaqus domain plugin 是 AM thermal control 还是 generic job/ODB lifecycle。
3. 是否在 v1 提供本地 persistent queue。
4. authorization 是否使用签名 token 或受控本地 state store。
5. evidence ledger 使用 JSONL、SQLite 还是两者组合。
6. physics rules 的正式版本化格式。
7. 是否保留 `abqpilot` compatibility import。
8. 何时增加 MCP。
9. 何时增加 read-only UI。
10. 真实 Abaqus integration test 的独立测试仓库或 private fixture 策略。

这些问题必须通过后续 ADR 决定，不得由迁移代码隐式决定。


---

# 18. Final Migration Verdict

```text
target project:
  AegisCAE Runtime

legacy projects:
  AbqJobPilot = Abaqus Job Lifecycle legacy reference
  AbqPilot = Abaqus Domain Adapter legacy source

new Runtime Core:
  REBUILD

legacy whole-repository copy:
  PROHIBITED

legacy direct dependency:
  NO

legacy branch continuation:
  NO

runtime-foundation PR:
  retain as design seed
  do not merge as another legacy Stage

primary migration assets:
  Abaqus command semantics
  log/status diagnosis
  INP inspection and narrow controlled patching
  StaticValidator / DiffGuard / PhysicsGuard
  solver preflight and hash-binding concepts
  read-only ODB extraction contracts
  resume and failure test scenarios

primary replacement targets:
  Context
  Workspace
  Executor
  Authorization lifecycle
  Session / Workflow
  Artifact provenance
  Checkpoint / Staging
  Evidence Recorder
  JSON CLI

prohibited legacy patterns:
  public raw subprocess
  GUI-driven execution
  Stage-driven preview architecture
  hard-coded roots
  implicit CWD
  unversioned dict queue
  placeholder rollback
  fixed Markdown PASS
  fixture-as-physical-evidence
  Skill/Prompt as safety boundary

migration strategy:
  define new contracts first
  extract only minimal pure legacy logic
  refactor behind Runtime boundaries
  re-test in new repository
  integrate real Abaqus only under explicit authorization

final decision:
  APPROVED_SELECTIVE_MIGRATION_TO_AEGISCAE_RUNTIME
```
