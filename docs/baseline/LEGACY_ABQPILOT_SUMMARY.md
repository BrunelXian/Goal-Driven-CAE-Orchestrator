# AbqPilot / AbqPilot-v2 旧版项目历史总结

## 1. Document Metadata

- document: LEGACY_ABQPILOT_SUMMARY.md
- audit date: 2026-07-26
- repository root: D:\Projects\AbqPilot-v2
- repository remote: https://github.com/BrunelXian/AbqPilot.git
- legacy baseline branch / commit: main / a305960eecd8a27600e900a6b1bd86f7e7b7c1a3
- runtime-foundation branch / commit: origin/agent/runtime-foundation-v01 / 320e91d3f911a4302d05ce662731a6b8ba0b532c
- current branch / HEAD: main / a305960eecd8a27600e900a6b1bd86f7e7b7c1a3
- working tree: clean; no untracked files before or after audit
- primary language / package / version: Python / abqpilot / 0.1.0
- report output path: D:\Users\wuxia\Documents\AbqPilot\LEGACY_ABQPILOT_SUMMARY.md
- files modified: this external report only; no repository file modified
- Abaqus executed / queue worker executed / GUI executed: no / no / no

Identity evidence: git rev-parse returned D:/Projects/AbqPilot-v2; origin fetch/push both resolve to BrunelXian/AbqPilot. main exists locally/remotely. agent/runtime-foundation-v01 exists only as origin remote ref, so this review used git show and git diff without checkout.

## 2. Executive Summary

总体成熟度：STAGE_DRIVEN_PROTOTYPE.

1. AbqPilot 试图把 controlled CAE/INP modification、guards、solver lifecycle、ODB metrics、repair advice 和 evidence 串成 Abaqus 闭环；README.md:1-121。
2. 它已经超越 LLM + arbitrary Abaqus scripts：窄热流 patch、StaticValidator、DiffGuard、PhysicsGuard、approval hash binding、fixed solver command、log diagnosis 和 gated ODB bridge 都有代码/测试。
3. 它尚不是统一 Controlled CAE Runtime，因为 main 没有统一 context、Tool Registry、ControlledWorkspace、common Executor、真实 rollback 或 tamper-evident evidence authority。
4. 五项最成熟资产是：热流 patch/diff、StaticValidator/PhysicsGuard、Abaqus log diagnosis、solver preflight/approval、ODB metrics script/contract。
5. 五项最严重问题是：public raw launcher、Stage-only workspace guard、placeholder rollback、ODB freshness/identity/required field gaps、fixed/non-hashed evidence freeze。
6. 实际形态是 fixed pipeline + finite state machine + multiple stage corridors；不是 Agent tool loop，也不是 recoverable workflow engine。
7. GUI/ACOM 增加 preview、handoff 和 non-solver governance，但大量 Stage 5 只是 draft、fixture、smoke、preview。
8. Runtime Foundation Draft PR 是过渡性设计尝试，不计入 main 的 legacy maturity。
9. 新项目不应继续在旧仓库增加 Stage；旧项目应作为 Abaqus Domain Adapter 的选择性代码来源。
10. 不建议整体复制，也不建议作为新 Runtime 的直接 Python dependency。

## 3. Original Mission, Claimed Scope and Actual Scope

### 文档宣称的使命

README 说明项目是 guarded/auditable closed-loop CAE-ODB workflow，并把 LLM 放在 deterministic toolchain 之外；README.md:1-121。AGENTS.md 要求 immutable sanity-base traceability、guard 不可绕过、Codex 不得成为 runtime authority；AGENTS.md:1-142。

### 实际实现范围

- IMPLEMENTED/PARTIAL：窄范围 heat-flux INP build + StaticValidator/DiffGuard/PhysicsGuard；abqpilot/builders/heat_flux_patch_builder.py:71；abqpilot/tools/static_validator_tool.py:6-35；abqpilot/tools/diff_guard_tool.py:28-124；abqpilot/tools/physics_guard_tool.py:4-25。
- IMPLEMENTED/PARTIAL：TaskWorkspace/PipelineRunner persist steps, trace, resume and rerun backup；abqpilot/core/task_workspace.py:11-30,34-195；abqpilot/core/pipeline_runner.py:80-215；tests/test_pipeline_resume.py。
- IMPLEMENTED/PARTIAL：sanity-base candidate preflight、token、fixed command runner、monitor/diagnosis/intake；abqpilot/solver/solver_preflight.py:19-146；solver_approval.py:15-103；controlled_abaqus_runner.py:13-127。
- IMPLEMENTED/PARTIAL：read-only job/ODB diagnosis and gated ODB metrics extractor；diagnostics/job_odb_diagnosis.py:30-203；odb/odb_metrics_extractor.py:27-176。
- IMPLEMENTED/PARTIAL：ACOM handoff/result intake marks Codex output as pending revalidation, never final evidence；acom/handoff_builder.py:26-145；acom/result_intake.py:12-103。

### 当前有意限制

runtime config is dry_run_only and sets allow_real_execution=false, allow_solver_submit=false, allow_llm=false, open_odb=false; abqpilot/configs/abaqus_runtime.yaml. Task config rejects solver submit, LLM and CAE modification; core/task_config.py:34-75. CAE export allows write_input_only only; cae/cae_inp_exporter.py:80-188. ODB is metrics-only gated; odb/odb_metrics_extractor.py:78-176. GUI Stage 5.1A catalog has disabled high-risk actions with no backend callback; gui/safe_action_catalog.py:281-461.

### 文档与代码冲突

| Claimed/Policy | Code evidence | Strict verdict |
| --- | --- | --- |
| rollback-oriented workflow | RollbackManager only makes in-memory placeholder records; core/rollback_manager.py:6-16 | PLACEHOLDER |
| evidence freeze must be traceable | manifest is path/byte inventory and final verdict is constant; analysis/evidence_freeze.py:7-45,63-83,266-276 | PARTIALLY IMPLEMENTED |
| GUI/CLI must not bypass deterministic tools | public execute_controlled_abaqus_command takes arbitrary command/cwd; solver/controlled_abaqus_runner.py:98-127 | CONFLICT |
| completion requires ODB/final-frame checks | intake accepts logs/path before ODB read; solver/solver_report.py:16-48 | PARTIAL |

## 4. Historical Evolution

Historical sequence, from code/status/docs rather than granular Git commit messages:

Early deterministic MVP -> guarded heat-flux mutation -> task workspace/pipeline -> AbqJobPilot preflight/dry-run/queue-only -> optional LLM advisory -> ACOM pipeline records -> GUI previews -> solver approval corridors -> Stage 5 root-remediation -> Runtime Foundation Draft.

Git history on main is short and largely generic/squashed: initial commits 99253e3/b948c11 then a sequence of fix commits ending a305960. Stage chronology is therefore documented primarily in PROJECT_STATUS_CURRENT.md, AGENTS.md, docs and filenames.

Real additions: validators, task state/resume, hash approvals, log diagnosis, gated ODB bridge, narrow solver runner. Mostly non-runtime additions: Stage 5 gate shapes, GUI cards, draft requests, inactive/fixture gates, non-final ledgers and doc assertions. Stage proliferation is architectural debt: gui contains 106 of 273 Python files and many modules are stage-specific preview/report/card code. New project must archive these as history, not copy them as runtime.

## 5. Current Architecture Map

User / CLI / GUI
  -> TaskConfig -> TaskWorkspace -> PipelineRunner [PARTIAL fixed pipeline]
     -> pipeline_steps -> validators / AbqJobPilot adapter -> EXTERNAL or MANUAL solver boundary
  -> DeterministicOrchestrator [legacy dry-run path]
     -> RunContext [PARTIAL] -> Inventory -> HeatFluxPatchBuilder -> StaticValidator -> DiffGuard -> PhysicsGuard -> DryRunBackend -> fixture metrics
  -> Controlled solver corridor [PARTIAL]
     candidate -> preflight -> approval -> fixed subprocess -> monitor/diagnosis -> ODB intake -> gated extractor -> report
  -> ACOM [EXTERNAL/MANUAL]
     handoff -> external Codex operator -> structured result -> revalidation scaffold

MISSING: common Planner with authorized structured plan; Tool Registry; central runtime Workspace; single Executor; Checkpoint Manager; Evidence Recorder.

PipelineRunner has fixed names/statuses and calls run_pipeline_step; core/pipeline_runner.py:80-215. Legacy orchestrator directly constructs tools; core/orchestrator.py:17-171. GUI is not only viewer: it calls run_solver_approved, DFLUX runner and demo-smoke API; gui/action_controller.py:423-427,981-987,1082-1085.

## 6. Repository Structure

| Path | Responsibility | Runtime critical | Quality | Migration value |
| --- | --- | --- | --- | --- |
| core | config/workspace/pipeline/state/approval | yes | PARTIAL | refactor selected contracts |
| tools/builders | validators and narrow patch | yes | strongest pure code | high |
| cae/solver/odb/diagnostics | Abaqus adapters | yes | PARTIAL | high with refactor |
| execution | dry backend abstraction | yes | legacy/dry-only | replace boundary |
| integrations | AbqJobPilot boundary | partial | external-coupled | legacy compat/refactor |
| guards/patching | condition/DFLUX/queue workflows | partial | narrow/stage-specific | selective refactor |
| analysis/reporting | evaluation/report/evidence package | partial | reporting not authority | selective refactor |
| llm/llm_nodes | advisory LLM | no | optional | no runtime-core migration |
| acom/pipeline_protocol | external handoff records | no | transition governance | legacy compat only |
| gui/ui_state | Tkinter cockpit/previews | no | Stage-heavy, separate caller | do not migrate wholesale |
| tests | unit/mock/doc contracts | yes | broad but mixed evidence | selective high value |
| docs/runs | history/policies/artifacts | no | Stage-heavy | archive/reference |

## 7. Core Runtime Components

### 7.1 Context and State

RunContext has five path fields only; core/run_context.py:8-20. TaskConfig and TaskWorkspace separately own safety flags/state; core/task_config.py:8-107 and core/task_workspace.py:34-195. There is no legacy AbqPilotContext on main.

Verdict: PARTIAL; no unified runtime context. Missing fields include source/staging/output/evidence roots, session identity, active model/CAE/INP/ODB hash, user goal/instructions, allowed tools, policy, limits, plan ID and common serialized authority.

### 7.2 Workspace Boundary

workspace_guard hard-codes project/forbidden roots and verifies a target path; workspace_guard.py:6-66. Its production integration is Stage 5.3A-v2 only; gui/controlled_solver_demo_smoke_v2.py:12,21-27. Normal writers use caller path directly: TaskWorkspace core/task_workspace.py:60-72; CAE exporter cae/cae_inp_exporter.py:35-72; ODB extractor odb/odb_metrics_extractor.py:36-71; evidence freeze analysis/evidence_freeze.py:19-45.

Verdict: local Stage-specific guard, not central workspace authority. Hard-coded roots/CWD appear in cli.py:90-101, solver_preflight.py:12-16, solver_report.py:11-13, llm/config.py:58 and GUI cards using Path.cwd().

### 7.3 Execution Boundary

| Entry | Caller | Command/CWD source | Authorization | Workspace guard | Bypass risk |
| --- | --- | --- | --- | --- | --- |
| CAE export | CLI/API CaeInpExporter | config + generated script / output_dir | flags | no | HIGH |
| normal solver | CLI/GUI runner | rebuilt preview / run_dir | token | no | HIGH |
| raw launcher | public Python function | arbitrary args | none | no | CRITICAL |
| DFLUX solver | CLI/GUI wrapper | fixed preview / run_dir | DFLUX token | no | HIGH |
| ODB extractor | CLI/API | config + generated script / output_dir | flags | no | HIGH |
| Stage 5.3A demo | CLI/GUI | fixed demo command/workdir | smoke-specific gate | local v2 only | HIGH |
| queue enqueue | adapter | external public API | token/config | no | EXTERNAL |

All production subprocess sites found use shell=False: cae/cae_inp_exporter.py:127-135; solver/controlled_abaqus_runner.py:105-114; odb/odb_metrics_extractor.py:122-130; stage5 demo runners. Normal preflight limits CPU 1..14; solver/solver_preflight.py:94-100; runner has timeout. No version probe/result and no common executor exist on main.

### 7.4 Authorization

Approval records bind candidate/source/command hashes, job, CPU, guards, actor and expiry; solver/solver_approval.py:15-96; core/approval.py:17-191. Tests cover phrase, expiry and hash mismatch; tests/test_solver_approval.py and tests/test_approval.py.

Verdict: PARTIAL. No token ID, single-use consumption, revocation, common risk policy, plan-step binding or central authorization ledger. A valid token may be reused during expiry. Preview/inactive/fixture GUI gates are not runtime authorization.

### 7.5 State Machine and Pipeline

StateMachine is a legacy finite transition graph; core/state_machine.py:8-66. PipelineRunner is resumable fixed pipeline with rerun backup; core/pipeline_runner.py:142-215. Classification: finite state machine plus resumable fixed pipeline, not Agent tool loop and not recoverable workflow engine. No structured plan, per-step authorization, compensation/rollback or common Executor/Validator contract.

## 8. Controlled Mutation and Validators

| Capability | Implementation | Contract/tests | Production verdict | Migration |
| --- | --- | --- | --- | --- |
| INP inventory | InventoryTool | path -> dict | PARTIAL | KEEP/refactor |
| heat patch | HeatFluxPatchBuilder | build request -> candidate/report; patch tests | narrow PARTIAL | REFACTOR |
| StaticValidator | token/region checks | test_static_validator.py | PARTIAL | KEEP |
| DiffGuard | normalized single heat-flux delta | guard tests | narrow PARTIAL | KEEP/refactor |
| PhysicsGuard | allowed diff/no uncertainty | test_physics_guard.py | PARTIAL | KEEP |
| MCPGuard | JNL/INP condition comparison | model-condition tests | narrow PARTIAL | REFACTOR |
| CAE export | noGUI writeInput template | mocked CAE tests | PARTIAL | REFACTOR adapter |
| arbitrary Python/INP generation | builders return allowed:false | code | PLACEHOLDER | DO NOT MIGRATE |
| repair plan | deterministic recommendation | evaluation tests | advisory | REFACTOR pure evaluator |

DiffGuard is a real deterministic declared-edit rule rather than LLM advice; tools/diff_guard_tool.py:28-124. MCPGuard currently covers concrete body heat-flux DFLUX/BF lifecycle plus schema hooks, not general semantic model preservation; guards/model_condition_schema.py:9 and reporting/project_status.py:298-330. Fixture candidate protection exists; tests/test_solver_candidate.py::test_fixture_inp_rejected_as_solver_candidate.

## 9. Abaqus Solver Lifecycle

candidate -> validate_solver_candidate/prepare_solver_run -> solver approval request -> token -> solver run request -> subprocess -> classify/diagnose -> ODB intake -> gated extract/report.

| Step | Implementation and strict status |
| --- | --- |
| candidate | sanity-base/hash/guard checks; PARTIAL |
| preflight | copy INP, timestamp dir, fixed preview; PARTIAL |
| approval | human phrase/expiry/hash JSON; PARTIAL, reusable |
| request | command rebuilt/compared; PARTIAL |
| subprocess | list + shell=False + timeout; HIGH RISK due public raw bypass |
| monitor/diagnosis | logs/lock/path metadata; PARTIAL |
| intake/report | accepted output then gated extractor; PARTIAL |

The bypass is execute_controlled_abaqus_command(command,cwd,timeout) at solver/controlled_abaqus_runner.py:98-127: it does not validate token, command origin or workspace. tests/test_controlled_abaqus_runner.py proves only mocked normal-wrapper behavior, not real Abaqus.

## 10. ODB Extraction and Validation

Current chain:
1. diagnose_job_output parses sta/msg/dat/log, lock and ODB path metadata; diagnostics/job_odb_diagnosis.py:174-203.
2. intake accepts diagnosis completed + ODB exists + no lock; solver/solver_report.py:16-48.
3. generated script opens ODB readOnly, selects last step/frame and seeks NT11/NT and S; odb/abaqus_odb_script_writer.py:43-102.
4. extractor can return PASS despite case missing_fields because its incomplete condition is narrow; odb/odb_metrics_extractor.py:151-158.

| Claim | Verdict |
| --- | --- |
| ODB existence, lock and text completion evidence | IMPLEMENTED |
| process exit captured | PARTIAL |
| ODB readable at intake | MISSING; only later extractor opens it |
| ODB fresh/current run | MISSING |
| job/input/model identity | MISSING |
| required step/frame/field as acceptance gate | PARTIAL |
| missing field blocks final extractor PASS | HIGH RISK |
| stale collision detection | PARTIAL only via usual timestamped run dirs |

Weakest point: output acceptance occurs before readability/freshness/job-INP identity/required fields. Existing tests reject no-completion, failed partial, missing ODB and locks; tests/test_job_odb_diagnosis.py and tests/test_solver_diagnosis_integration.py. They do not prove stale/corrupt/wrong-job/missing-field rejection.

## 11. Evidence and Auditability

| Layer | Asset | Strict verdict |
| --- | --- | --- |
| reporting | run/solver/GUI reports | IMPLEMENTED, not truth authority |
| trace logging | TaskWorkspace trace/TraceWriter | PARTIAL |
| artifact inventory | ArtifactRegistry paths | PARTIAL, not integrity proof |
| approval artifacts | request/token hash JSON | PARTIAL |
| RUN/HANDOFF/GATE | pipeline/ACOM records | governance records, non-final |
| Stage 1.10 evidence freeze | build_evidence_package | PARTIAL |
| tamper-evident evidence | whole bundle hash/immutability | MISSING |
| replayable evidence | context/plan/all calls/version ledger | MISSING |
| final evidence authority | unified final gate | NOT VERIFIED |

Evidence freeze sets constant FINAL_VERDICT and writes selected stage report/manifest outputs; analysis/evidence_freeze.py:7-45. Its manifest stores path/byte records, not file hashes; :63-83,266-276. It does not capture Git commit/working tree/software versions/all calls/approvals/exclusions. A Markdown report can diverge from execution, and post-freeze tampering cannot be detected.

## 12. LLM, Codex, ACOM and NARM

Codex as developer is allowed; Codex as runtime core is prohibited by AGENTS.md policy. ACOM is external/manual handoff: handoff builder sets codex_auto_execution_allowed false and codex_summary_is_final_evidence false; acom/handoff_builder.py:26-145. Result intake keeps accepted output pending revalidation; acom/result_intake.py:12-103.

LLM provider is schema-constrained advisory and disabled by default. Its prompt forbids solver submit, INP edit and direct ODB; llm/provider.py:13-16. Network call exists only when enabled; provider.py:21-125. No automatic Codex CLI call, Skill/MCP runtime, or core Agent loop was found. NARM is DOCUMENTED ONLY / NOT VERIFIED production implementation. Preserve the proposal-not-evidence principle; do not migrate ACOM Markdown choreography into runtime core.

## 13. GUI and Stage-Driven Development Debt

Tkinter GUI has task/artifact viewer, safe catalog, trace timeline and preview. Read-only viewer/disabled-action ideas are reusable. It also exposes calls to execution-capable APIs; gui/action_controller.py:423-427,981-987,1082-1085. Treat it as execution client, not merely viewer.

Debt: 106 GUI Python files, repeated Stage card/gate/draft/fixture/report modules, and smoke PASS terminology. Stage 5.3A-v2 produces scoped smoke request/status but not full ODB/evidence capability; gui/controlled_solver_demo_smoke_v2.py:15-60. Do not migrate Stage numbering, cards, copy assertions, fixture writer policy, smoke verdict vocabulary or redundant no-execution reports. New UI should render runtime policy/state, not encode it.

## 14. Testing System

Inventory: 273 test files, 857 collected test functions. Categories include unit, fixture/mock subprocess, documentation assertions, GUI imports/catalog, workspace, approval, pipeline resume, ODB/log and architecture-policy tests. This is not real Abaqus/ODB/QueueRunner/GUI end-to-end evidence.

Safety review: relevant tests use tmp_path, disabled defaults or monkeypatched subprocess. The Stage 5.3A-v2 test passes attempt_solver=False; tests/test_controlled_solver_demo_smoke_v2.py::test_demo_smoke_v2_creates_scoped_request_without_test_solver_invocation. No attempt_solver=True test call was found.

| Command | Exit | Passed | Failed | Blocked | Notes |
| --- | ---: | ---: | ---: | ---: | --- |
| specified Python --version | 0 | - | - | - | Python 3.12.10 |
| python -m pytest --collect-only -q -p no:cacheprovider | 0 | 857 collected | 0 | 0 | no test body |
| python -m pytest -q -x -p no:cacheprovider | 1 | 210 | 1 | 0 | stopped intentionally at first failure |
| python -m pytest -q --tb=no -p no:cacheprovider | terminal summary unavailable | NOT VERIFIED | 1 observed | 0 | progress reached end; do not infer numeric remainder |

Verified first failure is test_demo_smoke_v2_creates_scoped_request_without_test_solver_invocation: KeyError task_id after function returned safety-blocked payload. The test depends on a hard-coded global forbidden-root scan being clean; workspace_guard.py:6-66. This is environment coupling, not Abaqus execution. Runtime Foundation tests: NOT RUN — remote branch reviewed through Git objects only; no worktree was created under the one-new-file constraint. No test result here claims real Abaqus capability.

## 15. Stable and Reusable Assets

| Asset | Path | Why reusable | Required refactor | Target |
| --- | --- | --- | --- | --- |
| StaticValidator | tools/static_validator_tool.py | pure deterministic checks | context/path schema | validation/ |
| DiffGuard | tools/diff_guard_tool.py | declared-edit isolation | pluggable policy | validation/ |
| PhysicsGuard | tools/physics_guard_tool.py | simple fail-closed composition | policy schema | validation/ |
| inventory/heat patch | tools/inventory, builders/heat_flux_patch_builder | narrow deterministic domain action | Workspace + transaction | adapters/abaqus/inp/ |
| solver command/preflight | solver/solver_preflight.py | fixed command/hash/CPU | Executor/manifest | adapters/abaqus/ |
| diagnosis parser | diagnostics/* | pure log/lock taxonomy | provenance identity | adapters/abaqus/ |
| ODB scripts/contracts | odb/* | read-only field extraction | mandatory field/provenance acceptance | adapters/abaqus/ |
| approval hash binding | core/approval, solver/solver_approval | concrete binding | generic consume/revoke service | runtime/ |
| resume patterns/tests | TaskWorkspace/test_pipeline_resume | persistence insight | new workflow model | legacy_compat/ |

## 16. Critical Technical Debt

| Severity | Debt | Evidence |
| --- | --- | --- |
| CRITICAL | raw launcher bypass | solver/controlled_abaqus_runner.py:98-127 |
| CRITICAL | rollback placeholder | core/rollback_manager.py:6-16 |
| HIGH | fragmented context/no registry/common Executor | core/run_context.py:8-20; no registry implementation |
| HIGH | Stage-only workspace guard/direct writes | workspace_guard.py:6-66 and writer examples |
| HIGH | no separated source/staging/output/evidence roots | no legacy ControlledWorkspace; TaskWorkspace caller roots |
| HIGH | stale/wrong/unreadable/missing-field ODB gaps | section 10 chain |
| HIGH | incomplete non-tamper-evident evidence | analysis/evidence_freeze.py:63-83 |
| MEDIUM | reusable tokens/no revoke/plan binding | solver/solver_approval.py:15-96 |
| MEDIUM | hard-coded paths/implicit CWD | cli.py:90-101; llm/config.py:58 |
| MEDIUM | duplicate CLI/GUI/demo execution paths | cli.py:125-132,2509-2564; GUI controller |
| MEDIUM | report/action disconnect/fixed verdicts | analysis/evidence_freeze.py:7-45 |
| LOW | Stage/doc/preview explosion | gui modules and Stage docs/tests |

## 17. Runtime Foundation Branch Review

This is not legacy baseline capability. origin/agent/runtime-foundation-v01 is six commits ahead of main and changes 6 files: runtime context, controlled workspace, executor, runtime init, solver runner and runtime tests. GitHub PR #1 is open, draft, unmerged; base main a305960; head 320e91d; six commits, six changed files, +477/-38. Source: GitHub PR #1 metadata and git diff main...origin/agent/runtime-foundation-v01.

| Addition | Evidence | Assessment |
| --- | --- | --- |
| AbqPilotContext | remote abqpilot/runtime/context.py:8-116 | IMPLEMENTED serializable IDs/roots/command/version/CPU/mode/policy/tools; lacks goal and model/CAE/ODB identities |
| ControlledWorkspace | remote controlled_workspace.py:15-94 | IMPLEMENTED scoped read/write/CWD checks; compatibility helper aliases all roots to one run directory |
| ControlledExecutor | remote executor.py:12-104 | IMPLEMENTED tool allow-list, executable equality, CWD boundary, timeout, shell=false; authorization string is not validated/consumed |
| runner routing | remote solver/controlled_abaqus_runner.py:13-111 | removes raw launcher path in normal runner and writes resolved context; CAE/ODB/demo/all writers untouched |
| tests | remote tests/test_runtime_foundation.py:1-126 | context/workspace/executor mock tests; NOT RUN on remote ref |

PR body itself says its isolated test execution was environment-blocked. Remaining gaps: no Tool Registry, no all-writer migration, no robust source/staging separation in legacy adapter, no generic authorization, version probe, rollback, ODB provenance or evidence recorder. Recommendation: do not merge as another legacy Stage; retain it as design/reference seed for new Runtime.

## 18. Migration Matrix

| Component | Current path | Decision | Reason | New location |
| --- | --- | --- | --- | --- |
| validators | tools guards | KEEP | pure/narrow/tested | validation/ |
| INP patch/inventory | builders/tools | REFACTOR | useful but ungoverned paths | adapters/abaqus/inp/ |
| CAE/ODB bridges | cae/odb | REFACTOR | useful adapter code, fragmented execution | adapters/abaqus/ |
| diagnosis | diagnostics | KEEP/REFACTOR | strong pure parser asset | adapters/abaqus/diagnostics.py |
| solver preflight | solver | REFACTOR | fixed builder useful | adapters/abaqus/solver.py |
| runtime-foundation concepts | remote PR | REFACTOR | correct but incomplete | runtime/ |
| TaskWorkspace/PipelineRunner | core | REPLACE | fixed Stage flow, no plan authority | runtime/session.py |
| approval code | core/solver | REFACTOR | binding useful, lifecycle weak | runtime/authorization.py |
| evidence freeze | analysis/reporting | REPLACE | report not tamper-evident evidence | runtime/evidence.py |
| ACOM/pipeline protocol | acom/pipeline_protocol | DO NOT MIGRATE core | human transition process | legacy_compat if necessary |
| GUI Stage modules | gui | DO NOT MIGRATE | duplicate stage surface | new UI later |
| generic builder placeholders | builders | DO NOT MIGRATE | intentionally unsupported | none |

## 19. Recommended New Role

AbqPilot should become an Abaqus Domain Adapter legacy code source. It can supply CAE export, INP inspection, controlled mutation, command construction, monitoring, sta/msg/dat/lck diagnosis, ODB extraction, Abaqus field contracts and physics guards. It must not supply generic Runtime Context, Workspace, Executor, Authorization, Tool Registry, Session Manager, LLM loop, final evidence authority or generic UI.

## 20. Recommended Extraction Order

| Batch | Content | Dependency/risk | Acceptance |
| --- | --- | --- | --- |
| 0 | invariants, schemas, threat model | define runtime first | policy/schema tests; no Abaqus |
| 1 | pure validators and diagnosis | low | corpus/property tests |
| 2 | solver command/monitor adapter | new Context/Executor | mock process, timeout, job identity |
| 3 | ODB contracts/extraction | provenance rules | corrupt/stale/missing field tests |
| 4 | CAE export and mutation | Workspace + checkpoints | source immutability/rollback; human authorization for real actions |
| 5 | fixed pipeline compatibility | new Plan/Session | resume/migration tests |
| 6 | legacy CLI compatibility | stable adapter API | no automatic real execution |

## 21. Final Legacy Verdict

1. 核心价值：narrow Abaqus safeguards, INP diff rules, diagnosis and gated metrics.
2. 当前是：STAGE_DRIVEN_PROTOTYPE, not Agent Runtime.
3. 最值得迁移：StaticValidator, DiffGuard/PhysicsGuard, heat patch/inventory, log diagnosis, ODB contracts.
4. 必须废弃：raw launcher, placeholder rollback, Stage-only guard, fixed non-hashed evidence freeze, Stage-card architecture.
5. 是否继续在旧仓库开发新架构：否。
6. Runtime Foundation PR：仅作参考/seed，不作为 legacy Stage merge target。
7. 直接 dependency：否。
8. 迁移策略：extract pure modules, refactor behind new contracts; short-term legacy_compat only where necessary。
9. 新项目不应继续用 AbqPilot 作为总名。
10. 正式角色：Controlled CAE Runtime 下的 Abaqus Domain Adapter。

- recommended legacy status: USEFUL_LEGACY_REFERENCE, selective extraction only
- recommended new role: Abaqus Domain Adapter
- continue legacy development: no
- merge runtime-foundation PR: no into legacy; retain as new-runtime design reference
- direct dependency recommended: no
- migration strategy: selective extraction then refactor
- top reusable assets: validators, patch logic, log diagnosis, ODB contracts, command builder
- top refactor targets: context, workspace, executor, authorization, ODB provenance
- top replacement targets: rollback, evidence authority, fixed Stage pipeline
- top rejected patterns: raw launcher, Stage proliferation, hard-coded roots, GUI execution corridors, preview-as-progress
- tests executed: 857 collected; full attempt; 211 outcome verified by -x
- tests passed: 210 confirmed
- tests failed: 1 confirmed
- tests blocked: 0
- files modified: external report only; repository unchanged
- Abaqus executed: no
- final verdict: do not extend legacy; use it as selective Abaqus adapter source for the new Controlled CAE Runtime

Final safety confirmation: no Abaqus, queue worker, GUI or external solver was started; no commit, push, merge, rebase or checkout occurred; working tree remained unchanged; this report is the only newly created file for this task.

