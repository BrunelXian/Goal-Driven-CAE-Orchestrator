<div align="center">

<img src="docs/vericae/images/vericae-logo.svg" alt="VeriCAE — finite-element mesh and verification mark" width="96" height="96">

# VeriCAE

**Verifiable, Goal-Driven CAE Research Agent**

*From research questions to evidence-based engineering decisions.*

**English** · [简体中文](README_CN.md)

[![Project — Research Software](https://img.shields.io/badge/Project-Research%20Software-386597)](product/vericae/vericae-research/README.md)
[![Workflow — Goal-Driven](https://img.shields.io/badge/Workflow-Goal--Driven-237468)](ENGINE.md#research-decisions)
[![Runtime — Codex Native](https://img.shields.io/badge/Runtime-Codex%20Native-70599C)](ENGINE.md#connection-and-recovery)
[![Interface — MCP](https://img.shields.io/badge/Interface-MCP-286E86)](product/vericae/vericae-research/references/mcp-runtime-verification.md)
<br>
[![Release — v1.0.0](https://img.shields.io/badge/Release-v1.0.0-365E94)](https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator/releases/tag/v1.0.0)
[![License — Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-96536E)](LICENSE)
[![Execution — AbqJobPilot](https://img.shields.io/badge/Execution-AbqJobPilot-97562F)](https://github.com/BrunelXian/AbqJobPilot)
[![Solver — Abaqus](https://img.shields.io/badge/Solver-Abaqus-75612A)](docs/vericae/INT-001.md "Historical Abaqus axial-bar verification")

[Download release](https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator/releases/tag/v1.0.0) · [Documentation index](docs/README.md) · [Explore source code](product/vericae/)

</div>

## 1. What is VeriCAE?

VeriCAE is an open-source AI research framework for computational engineering. Rather than prescribing every simulation step, researchers define a scientific goal. VeriCAE helps organize a persistent research team, formulate hypotheses, plan numerical experiments, review models, analyze evidence and decide what to investigate next.

The framework is built on three principles: **Verified-Model-First** — start from a model qualified for the research question; **Goal-Driven** — investigate within explicit objectives and constraints; **Verifiable** — connect scientific claims to evidence and independent review.

### What can you investigate?

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/vericae/images/research-applications-dark.svg">
  <img src="docs/vericae/images/research-applications-light.svg" alt="Four research applications: 01 Inverse Identification — small-punch material calibration; 02 Simulation-Driven Scientific Discovery — scaling laws and dimensionless analysis; 03 Engineering Design and Process Optimization — laser deposition scan strategy; 04 Mechanism and Sensitivity Investigation — structural failure or thermal distortion." width="100%">
</picture>

*Illustrative research applications for planning, investigation and verification. These examples do not imply that every scenario has passed end-to-end real-solver validation.*

## 2. How does VeriCAE work?

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/vericae/images/research-workflow-dark.svg">
  <img src="docs/vericae/images/research-workflow-light.svg" alt="VeriCAE research workflow: define a research goal; Main coordinates CAE, Results and Independent Validation; scoped MCP connects the research layer to AbqJobPilot; returned evidence informs research findings and the next decision." width="100%">
</picture>

### The three research skills

1. **Initiate CAE Research** — Frame the question, agree on the scope and acceptance criteria, and create a Research Contract and Research Card.
2. **Conduct CAE Research** — Main coordinates scoped Task Cards across three specialist conversations: CAE reviews the model and physics, Results analyzes observations and provenance, and Independent Validation checks claims independently. Main synthesizes the findings and proposes the next research decision.
3. **Set Up Research Environment** — When computational tools are needed, verify the actual environment, MCP availability and service identity before dependent work proceeds.

### Two products, two responsibilities

VeriCAE is built on **Codex Native** conversations. Main is the sole writer of primary research state; contracts, cards, tasks and reports are inspectable Markdown/YAML files. No separate VeriCAE agent runtime or database is required. Role and Task Card boundaries define the research workflow, not a host-enforced security sandbox.

**[AbqJobPilot](https://github.com/BrunelXian/AbqJobPilot)** is the independent Windows execution platform. It owns authorization, job lifecycles and execution evidence, connecting to VeriCAE through MCP. A research agreement does not authorize a solver run.

*The architecture diagram illustrates the intended research workflow, not a completed end-to-end live solver run.*

The historical axial-bar verification demonstrates numerical agreement and independent review; a newly initiated real Abaqus solve-and-extract loop remains unqualified end to end. [Technical architecture](ENGINE.md) · [Engineering case study](docs/vericae/ENGINEERING-CASE-STUDY.md) · [Verification status](docs/COMPATIBILITY.md)

### Repository Structure

```text
product/vericae/
├── .agents/plugins/marketplace.json      Marketplace catalog
├── vericae-research/                     Codex Native research plugin
│   ├── skills/                           Initiate, Conduct and Setup skills
│   ├── native-agents/                    Specialist agent definitions
│   ├── references/                       Research and collaboration protocols
│   └── templates/research-project/       Research workspace templates
├── developer/                            Workspace checker for developers
└── release/                              Package builder and release tests
```

## 3. Installation

**VeriCAE 1.0.0** requires a Codex installation with local plugin marketplace support. Abaqus is not required for research planning or offline model review.

1. Download [VeriCAE-1.0.0.zip](https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator/releases/download/v1.0.0/VeriCAE-1.0.0.zip), verify the [SHA-256](https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator/releases/download/v1.0.0/VeriCAE-1.0.0.zip.sha256) and extract it to a permanent folder.
2. Open PowerShell in the directory containing the extracted `VeriCAE-1.0.0` folder and register the local marketplace:

```powershell
codex plugin marketplace add ./VeriCAE-1.0.0
codex plugin add vericae-research --marketplace vericae-public --json
codex plugin list --marketplace vericae-public --json
```

3. Open your research workspace in Codex Desktop. Verify that the three VeriCAE skills are available at version 1.0.0, then use **Initiate CAE Research** to begin.

For example, ask: *"Plan a cantilever tip-displacement study. Identify the reference model and acceptance criteria, and show me the Research Card before creating files."*

**Optional execution platform:** [Download AbqJobPilot 1.0.0 for Windows x64](https://github.com/BrunelXian/AbqJobPilot/releases/download/v1.0.0/AbqJobPilot-1.0.0-Windows-x64-Setup.exe). The installer is unsigned. Use your own licensed Abaqus installation and configure it in AbqJobPilot Settings; real execution requires a separately authorized, supported environment.

[Full installation instructions](docs/INSTALL.md) · [Compatibility and requirements](docs/COMPATIBILITY.md) · [Offline numerical replay — no Abaqus required](docs/vericae/demo/README.md)

## 4. Development & Contributors

<p align="center">
  <a href="https://github.com/BrunelXian">
    <img src="https://avatars.githubusercontent.com/u/43325767?v=4&amp;s=120" width="72" height="72" alt="BrunelXian"><br>
    <strong>@BrunelXian</strong>
  </a><br>
  VeriCAE founder, system architect and maintainer
</p>

ChatGPT and Codex assist development. The maintainer sets the research direction and reviews changes for acceptance.

Contributions, independent reproductions and research collaborations are welcome. VeriCAE is licensed under [Apache-2.0](LICENSE); the companion AbqJobPilot project uses MIT.

## 5. Roadmap

These are future research and engineering priorities, not claims of completed capabilities in v1.0.0.

- **Autonomous numerical experiments:** qualify general execution-environment binding, new-task real-solver execution and independently verified results.
- **Simulation-driven scientific discovery:** investigate hypothesis generation, scaling laws, counterexamples and informative experiment selection under a research budget.
- **Material and process research:** explore small-punch and tensile-test inverse identification, design optimization and additive manufacturing process studies.
- **Multi-solver and multiphysics research:** explore additional CAE backends and verifiable coupled thermo-mechanical and fluid–structure workflows.

[Research agenda](docs/vericae/RESEARCH-AGENDA.md) · [Current verification boundaries](docs/COMPATIBILITY.md)

### Research Projects

Related research programmes that inform the development and application of VeriCAE. Each repository maintains its own scientific and validation status.

| Project | Research focus |
| --- | --- |
| [**RL-LAM-ScanOpt**](https://github.com/BrunelXian/RL-LAM-ScanOpt) | Laser additive manufacturing: scan-path optimisation, LDED benchmarks and FEA teacher data. A target application for VeriCAE. |
| [**SP-InvOpt / SMALL-PUNCH**](https://github.com/SHUAIXSYU/SMALL-PUNCH) | Small Punch Test inverse optimisation: material constitutive parameter identification from force–displacement curves. Earlier GD-CAE and AbqJobPilot workflows have supported this research. |

These links identify related research, not completed VeriCAE 1.0.0 end-to-end qualifications. Further projects will be added as they are made public.
