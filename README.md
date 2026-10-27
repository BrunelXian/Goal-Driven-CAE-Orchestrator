# Goal-Driven CAE Orchestrator

## From verified models to verifiable discoveries

**An Agentic CAE Research Environment built around Codex as its sole Agent Harness.**

One researcher. One main conversation. Specialized engineering agents, called on
when the research needs them.

Goal-Driven CAE Orchestrator aims to help researchers carry a scientific question
from a trusted Abaqus model through controlled experiments to independently
checked conclusions. Its foundation is bounded autonomy: preserve the physical
problem, record each experiment, and make conclusions traceable to evidence.

**中文简介：** Goal-Driven CAE Orchestrator 面向拥有可信 Abaqus 模型的科研人员，以 Codex 为唯一 Agent Harness。研究者通过一个 Main 主对话提出科研目标、确认模型基线和授权边界；Codex 按需协调专业子 Agent，GD-CAE 管理持久科研状态、模型契约、预算和独立验真，AbqJobPilot 负责获批的 Abaqus 执行与作业证据。这是正在设计的产品方向，尚非已交付的自主科研工作流。

> **Current status: M00-P architecture and product design; implementation remains
> a Milestone 0 skeleton.** The Python distribution and namespace are still
> `aegiscae`, version `0.0.0`. There is no supported end-user GD-CAE installation,
> `gdcae` CLI, MCP workflow, or autonomous CAE loop yet. The workflow, roles,
> architecture, and verification mechanisms below are proposed capabilities.

## A persistent environment for computational research

Simulation supports hypothesis testing, parameter identification, model comparison,
diagnosis, and design-space exploration. Those activities often span model files,
solver logs, scripts, notebooks, experimental data, and many conversations.

GD-CAE is intended to connect them through a durable **ResearchProject** record:
the approved goal and model baseline, permissible changes, candidate identities,
execution references, budgets, verification results, and decisions. That record
must survive the end of an agent turn or the closure of a client.

The conversation is the primary interface. The persistent research record holds
research decisions; AbqJobPilot remains the authority for its execution facts.

### The intended researcher experience

1. **Bring a verified model.** Register an approved Abaqus baseline, its input
   dependencies, provenance, validation evidence, and known limitations.
2. **Define a research goal.** Specify observables, experimental data, constraints,
   units, tolerances, allowed changes, and a bounded execution budget.
3. **Work with Project Main.** Codex plans the investigation and delegates narrow
   tasks to specialized subagents when useful.
4. **Review controlled candidates.** Model changes receive explicit identities
   and pass contract checks before execution authorization is considered.
5. **Run approved experiments.** AbqJobPilot executes within its supported,
   precisely authorized scope and records job-level evidence.
6. **Examine the evidence.** Check provenance, numerical results, frozen goal
   criteria, and applicable independent references before accepting a conclusion.
7. **Continue, pause, or stop.** A supported but unmet goal may justify a new
   candidate. Unknown execution, missing evidence, changed physics, or exhausted
   authority must block further automatic action.
8. **Keep a reproducible record.** Preserve candidate inputs, execution bindings,
   result provenance, verification records, decisions, and scientific caveats.

Automatic continuation after an external job completes is a separate feasibility
milestone. Starting a programmatic Codex turn must not be assumed to resume the
researcher's original visible Main conversation.

## Verified-Model-First

The initial scope starts with trusted engineering assets and constrained changes.
Generating arbitrary complex CAE models from natural language (Text-to-CAE) is
outside the first implementation scope.

A valid input file alone does not establish a valid physical model. Contact,
material laws, sets and surfaces, boundary conditions, load histories, and thermal
interfaces carry engineering meaning that must be preserved or revalidated.

The planned **Model Contract** makes those assumptions and allowed mutations
explicit. Broader geometry, mesh, or physics changes would require new contract
versions and appropriate review. Baselines remain immutable; candidates are
derived in controlled workspaces.

## One Main, specialized expertise

Codex provides the agent harness and native subagent coordination. GD-CAE will
define domain roles and handoff contracts without implementing another multi-agent
framework. Specialists are used on demand rather than kept permanently active.

| Role | Intended responsibility | Structured handoff |
| --- | --- | --- |
| **Project Main** | Clarify the research question, coordinate work, and explain decisions and approval requests. | Research plan and agent tasks |
| **CAE Model** | Inspect baseline semantics and propose scoped model variants. | Candidate proposal and mutation manifest |
| **Results / ODB** | Specify admissible extraction and interpret traceable numerical data. | Extraction request and evidence references |
| **Inverse / Optimization** | Propose experiments and parameter candidates using appropriate numerical methods. | Parameter proposal, method, and uncertainty |
| **Independent Reviewer** | Challenge assumptions and identify missing evidence or validation. | Findings and unresolved concerns |

Reviewer opinions are distinct from machine verification records. Frozen,
deterministic checks should decide whether machine-checkable criteria are met;
an agent's self-report cannot substitute for those checks. Role instructions alone
also do not provide operating-system permission isolation.

## Proposed architecture

```mermaid
flowchart TB
    R["Researcher: goal, constraints, approvals"] --> C["Codex Main"]
    C --> S["On-demand Codex Subagents: CAE, Results, Inverse, Review"]
    C --> G["GD-CAE: ResearchProject, Contracts, Budget, Verification"]
    S --> G
    G -->|"Precisely approved requests"| A["AbqJobPilot: Grant, Receipt, Supervisor, Run evidence"]
    A --> B["Abaqus within the approved backend scope"]
    B --> A
    A -->|"Execution evidence"| G
    G -->|"Research decisions and open questions"| C
```

- **Codex proposes and reasons.** Main and subagents cannot issue their own real
  solver grants, change frozen acceptance criteria, or create authoritative
  verification records.
- **GD-CAE governs research state and acceptance.** It will manage contracts,
  candidates, budgets, evidence bindings, and research-level decisions. It must
  not become a second Abaqus process supervisor or write the execution backend's
  private database.
- **AbqJobPilot owns controlled Abaqus execution.** Its Agent-first service manages
  job-level authorization, receipts, process lifecycle, and observed execution
  evidence. A completed job does not establish a research conclusion.
- **The researcher approves the scientific scope.** Baselines, assumptions,
  consequential changes, and execution authority remain subject to explicit review.

These are logical responsibility domains. They do not require three distributed
microservices.

## Evidence and verification

The proposed verification model keeps distinct questions separate:

| Layer | Question |
| --- | --- |
| **V0 — Provenance** | Do the inputs, Run, attempt, outputs, versions, and hashes belong together? |
| **V1 — Model integrity** | Were mutations permitted and declared physical invariants preserved? |
| **V2 — Solver and numerical health** | Is there sufficient evidence of execution, convergence, and numerical reliability? |
| **V3 — Goal acceptance** | Do the metric, entity, step, units, and tolerance satisfy the frozen goal? |
| **V4 — Physical validation** | Is the model supported by applicable benchmarks, independent analysis, or experimental data? |

`UNKNOWN`, `INCONCLUSIVE`, and `NOT_ASSESSED` are meaningful outcomes. Solver
completion, artifact existence, and curve-fit quality must not silently become
claims of physical validity. Each goal must declare which checks are required.

## Research applications we are building toward

- **Small Punch material inversion.** Infer Hollomon parameters from measured
  force-displacement data and an approved model, examining fit quality,
  non-uniqueness, and contact and mesh assumptions.
- **LDED scan-order optimization.** Explore admissible scan sequences in trusted
  thermo-mechanical models while preserving element activation, evolving thermal
  boundaries, and the interpretation of deformation and stress metrics.
- **AFI-guided diagnostics.** Use Abaqus Failure Intelligence cases as sourced
  hypotheses, propose bounded diagnostic actions, and check whether a suggested
  numerical fix changes the physical problem.
- **Reproducible simulation studies.** Support controlled parameter sweeps,
  calibration, model comparison, and sensitivity analysis.

These are target use cases, not implemented workflows. Where a fixed script, DOE,
or numerical optimizer is sufficient, it should remain the baseline against which
agent assistance is evaluated.

## Engineering principles

- **Verified-Model-First:** preserve approved baselines and their scope of validity.
- **Persistent goals:** keep contracts, budgets, evidence, and decisions beyond a turn.
- **Evidence-governed autonomy:** separate proposals, authorization, and verification.
- **Single execution authority:** use the approved AbqJobPilot path for Abaqus work.
- **Conservative recovery:** query the original execution identity after an uncertain
  response; do not silently retry with a new request identity.
- **Fail closed:** stop advancement when identity, evidence, or authorization is unclear.
- **Reproducibility:** record rejected candidates and inconclusive results as well as
  successful experiments.

## Roadmap

Milestones describe planned work, not shipped functionality or execution permission.

| Milestone | Intended outcome |
| --- | --- |
| **M00-P — Architecture and product reconciliation** | Review Codex-native UX, authority boundaries, legacy ADR conflicts, and research-state contracts. Audit completed; decisions await review. |
| **M01 — Read-only evidence bridge** | Inspect bounded AF evidence through explicit Project bindings; verify synthetic contracts and isolated AF compatibility separately. |
| **M02 — Research and model contracts** | Implement frozen goals, model constraints, candidate checks, budgets, and deterministic verification records. |
| **M03 — Offline research loop** | Prove persistent, recoverable two-step workflows with Fake/Python fixtures and no Abaqus calls. |
| **M03-E — Codex continuation** | Test event-driven continuation, duplicate-event handling, and original visible Main-thread recovery separately. |
| **M04 — Real bounded Abaqus loop** | Following separate backend-extension and execution approvals, demonstrate legal parameter variants and independently checked outcomes. |
| **M05 — Reliability benchmark** | Measure unsafe acceptance, recovery behavior, diagnostic quality, and cost against simpler baselines. |
| **M06 — Domain research trial** | Conduct a nontrivial Small Punch inversion study with model, data, and uncertainty checks. |
| **M07 — Researcher experience** | Package installation, diagnostics, project initialization, documentation, and reproducible use. |

## Current implementation and historical records

The repository was renamed from **AegisCAE Runtime**. It currently contains
architecture documents, frozen historical snapshots, an empty Python namespace
skeleton, and architecture tests. ResearchProject persistence, the evidence bridge,
domain agents, and the verification engine have not been implemented here.

The separate [AbqJobPilot](https://github.com/BrunelXian/AbqJobPilot) project has a
limited, historically tested Agent-first execution MVP on its Develop line. At the
M00-P reviewed baseline, its normal product path is restricted to a fixed Standard
input and a single provisioned Plan/Run. Historical fixed DAT checks do not prove
arbitrary model support or ODB content verification. Parameterized multi-candidate
execution and controlled ODB extraction require separately reviewed extensions.

The documents below preserve the earlier architecture and its rationale. Existing
ADR-001/002 still contain decisions that conflict with the proposed delegation to
AbqJobPilot. This README describes the new direction; it does not accept proposed
ADR-003/004 or silently supersede the old decisions.

- [Historical architecture](ARCHITECTURE.md)
- [Existing runtime invariants](RUNTIME_INVARIANTS.md)
- [Historical threat model](THREAT_MODEL.md)
- [Legacy migration decisions](MIGRATION_FROM_LEGACY.md)
- [Frozen baseline register](docs/baseline/BASELINE_REGISTER.md)
- [Milestone 0 implementation plan](docs/milestones/MILESTONE_00_IMPLEMENTATION_PLAN.md)
- [ADR-001: Runtime-first](docs/adr/ADR-001-runtime-first.md)
- [ADR-002: Selective legacy migration](docs/adr/ADR-002-legacy-selective-migration.md)

**The ambition:** a research environment in which every experiment has an identity,
every conclusion has evidence, and every autonomous action has a defined boundary.
