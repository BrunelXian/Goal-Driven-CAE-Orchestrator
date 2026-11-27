# Development archive

## Release evidence

| Question | Where to look |
| --- | --- |
| What did the release carry forward from earlier tests? | The [compatibility record](../../COMPATIBILITY.md) gives the versions, operations and verdicts for UAT-100, INT-001 and the INT-002 series. The [original freeze notes](../../product/vericae/release/RELEASE_NOTES.md) document the package contents, dependencies and build procedure. |
| What can I inspect from the historical axial-bar run? | The [INT-001 case report](../vericae/INT-001.md) explains the numerical result and the gap in extraction provenance. The [public replay](../vericae/demo/) includes the model input, published observations and arithmetic check. |

## Before VeriCAE 1.0

The following records describe the earlier AegisCAE and GD-CAE projects. Paths, permissions, commands and verdicts in them belong to the experiments as recorded. References to local host files identify historical observations. The [1.0 installation guide](../../INSTALL.md) covers the published product.

| Topic | Preserved material |
| --- | --- |
| Design and terminology | [Project vocabulary](pre-1.0/CONTEXT.md), [migration decisions](pre-1.0/MIGRATION_FROM_LEGACY.md), [runtime invariants](pre-1.0/RUNTIME_INVARIANTS.md), [threat model](pre-1.0/THREAT_MODEL.md) |
| Human approval and deployment | [HIL boundary test](pre-1.0/architecture/7D_G2_HIL_BOUNDARY.md) and [operator deployment proposal](pre-1.0/architecture/7D_G3_D3_OPERATOR_DEPLOYMENT_APPROVAL.md) |
| Role activation and handoff | [Desktop acceptance record](pre-1.0/milestones/D6-P_PLUGIN_FOUR_NATIVE_AGENTS_ACCEPTANCE.md) and [Research Preview handoff audit](pre-1.0/architecture/RESEARCH_PREVIEW_TASK_HANDOFF_AUDIT.md) |
| Offline execution evidence | [D7 feasibility report](pre-1.0/milestones/D7_RESEARCH_PREVIEW_VERTICAL_SLICE_CONVERGENCE_2026-11-01.md) and its [machine-readable test results](pre-1.0/milestones/D7_VERTICAL_SLICE_OFFLINE_EVIDENCE_2026-11-01.json) |

The local archive includes all 118 historical Markdown documents outside `docs/vericae/` from the pre-cleanup documentation tree, their ten JSON records and a source patch. Browse the [milestones](pre-1.0/milestones/), [architecture](pre-1.0/architecture/), [decision records](pre-1.0/adr/), [baselines](pre-1.0/baseline/), [skill guides](pre-1.0/skill-guides/) and [user guide](pre-1.0/user/).

Five source and test links in the [M03-F0 design](pre-1.0/architecture/M03_F0_PERSISTENT_CODEX_MAIN_RUNTIME.md) now open their original Git files. The [D7-R2F-E2 report](pre-1.0/milestones/D7-R2F-E2_INTEGRATION_QUALIFICATION.md) prints the original workstation path for its local manifest. Both records can be inspected at their original revisions. [Original M03-F0](https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator/blob/efd3e5c5cd28e39c3edf3e39896c475afb9c2e29/docs/architecture/M03_F0_PERSISTENT_CODEX_MAIN_RUNTIME.md) · [Original D7-R2F-E2](https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator/blob/efd3e5c5cd28e39c3edf3e39896c475afb9c2e29/docs/milestones/D7-R2F-E2_INTEGRATION_QUALIFICATION.md)

The four one-time PowerShell scripts referenced by the deployment records can be read alongside their original dependencies in the snapshot. [Stage installer](https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator/blob/efd3e5c5cd28e39c3edf3e39896c475afb9c2e29/docs/milestones/Stage-PowerShell769-Approved.ps1) · [Install](https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator/blob/efd3e5c5cd28e39c3edf3e39896c475afb9c2e29/docs/milestones/Install-PowerShell769-Approved.ps1) · [Check staging offline](https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator/blob/efd3e5c5cd28e39c3edf3e39896c475afb9c2e29/docs/milestones/Test-PowerShell769-StagingOffline.ps1) · [Check direct install offline](https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator/blob/efd3e5c5cd28e39c3edf3e39896c475afb9c2e29/docs/milestones/Test-PowerShell769-DirectOffline.ps1)

## Earlier README artwork

The [first workflow and application-card illustrations](readme-artwork/) preserve both themes from the README redesign. The current [light](../assets/research-workflow-light.svg) and [dark](../assets/research-workflow-dark.svg) diagrams show the research decision loop.

## Complete source snapshot

The [pre-cleanup tree](https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator/tree/efd3e5c5cd28e39c3edf3e39896c475afb9c2e29) retains the original paths at commit `efd3e5c5cd28e39c3edf3e39896c475afb9c2e29`, the revision preserved by the `archive/pre-1.0-cleanup` branch. The [current VeriCAE source](../../product/vericae/) is in the main project tree.

| Browse the original tree | Contents |
| --- | --- |
| [Core source](https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator/tree/efd3e5c5cd28e39c3edf3e39896c475afb9c2e29/src/aegiscae), [plugins](https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator/tree/efd3e5c5cd28e39c3edf3e39896c475afb9c2e29/plugins), [product prototypes](https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator/tree/efd3e5c5cd28e39c3edf3e39896c475afb9c2e29/product) | The earlier Python runtime, research plugins and distribution sources. |
| [Tests and fixtures](https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator/tree/efd3e5c5cd28e39c3edf3e39896c475afb9c2e29/tests), [examples](https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator/tree/efd3e5c5cd28e39c3edf3e39896c475afb9c2e29/examples), [external runner](https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator/tree/efd3e5c5cd28e39c3edf3e39896c475afb9c2e29/external_runner), [deployment tools](https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator/tree/efd3e5c5cd28e39c3edf3e39896c475afb9c2e29/operator_deployment) | Original checks, rehearsal scripts and operator tooling together with the source they exercised. |
| [Milestones and run records](https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator/tree/efd3e5c5cd28e39c3edf3e39896c475afb9c2e29/docs/milestones), [architecture](https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator/tree/efd3e5c5cd28e39c3edf3e39896c475afb9c2e29/docs/architecture), [decision records](https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator/tree/efd3e5c5cd28e39c3edf3e39896c475afb9c2e29/docs/adr), [baselines](https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator/tree/efd3e5c5cd28e39c3edf3e39896c475afb9c2e29/docs/baseline) | The full development reports, evidence attachments, one-time scripts and design history. |
