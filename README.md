# VeriCAE

**Verifiable, Goal-Driven CAE Research Agent**

*From research questions to evidence-based engineering decisions.*

[VeriCAE v1.0.0](https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator/releases/tag/v1.0.0) · [AbqJobPilot v1.0.0](https://github.com/BrunelXian/AbqJobPilot/releases/tag/v1.0.0) · [Apache-2.0](LICENSE)

## 1. What is VeriCAE?

VeriCAE is a goal-driven AI research framework for computational engineering. Instead of prescribing every simulation step, researchers define a scientific objective, and VeriCAE helps organize the research team, plan numerical experiments, review models, analyze evidence and decide what to investigate next.

Built around **Verified-Model-First**, **Goal-Driven Research** and **Independent Verification**, VeriCAE connects scientific reasoning with controlled engineering workflows.

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

VeriCAE uses **Codex Native** conversations: Main manages the research state, CAE examines the model and physics, Results analyzes recorded outputs, and Independent Validation checks scientific claims. Research contracts, cards, tasks and reports are stored in Markdown and YAML.

**[AbqJobPilot](https://github.com/BrunelXian/AbqJobPilot)** is the independent Windows execution layer. It manages authorization, job lifecycles and execution evidence through MCP. A research agreement does not authorize a solver run. The diagram illustrates the intended research workflow; general new-task real Abaqus execution is not yet qualified end to end.

[Technical architecture](ARCHITECTURE.md) · [Real Abaqus case study](docs/vericae/ENGINEERING-CASE-STUDY.md) · [Verification status and compatibility](COMPATIBILITY.md)

## 3. Installation

**VeriCAE 1.0.0** requires a Codex installation with local plugin marketplace support. Abaqus is not required for research planning or offline model review.

1. Download [VeriCAE-1.0.0.zip](https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator/releases/download/v1.0.0/VeriCAE-1.0.0.zip), verify the [SHA-256](https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator/releases/download/v1.0.0/VeriCAE-1.0.0.zip.sha256) and extract it to a permanent folder.
2. Open PowerShell in the directory containing the extracted `VeriCAE-1.0.0` folder and register the local marketplace:

```powershell
codex plugin marketplace add ./VeriCAE-1.0.0
codex plugin add vericae-research --marketplace vericae-public --json
codex plugin list --marketplace vericae-public --json
```

3. Open your research workspace in Codex Desktop and use **Initiate CAE Research**. Verify that the three VeriCAE skills are available at version 1.0.0.

**Optional execution platform:** [Download AbqJobPilot 1.0.0 for Windows x64](https://github.com/BrunelXian/AbqJobPilot/releases/download/v1.0.0/AbqJobPilot-1.0.0-Windows-x64-Setup.exe). The installer is unsigned. Use your own licensed Abaqus installation and configure it in AbqJobPilot Settings; real execution requires a separately authorized, supported environment.

[Full installation instructions](INSTALL.md) · [Compatibility and requirements](COMPATIBILITY.md) · [Offline numerical replay — no Abaqus required](docs/vericae/demo/README.md)

## 4. Development & Contributors

**Project maintainer:** [BrunelXian](https://github.com/BrunelXian).

Developed through an AI-assisted engineering workflow using ChatGPT and Codex, with human-led research direction, architecture decisions and acceptance review.

Contributions, independent reproductions and research collaborations are welcome. VeriCAE is licensed under [Apache-2.0](LICENSE); the companion AbqJobPilot project uses MIT.

## 5. Roadmap

- **Autonomous research experiments:** qualify new-task real-solver execution, result retrieval and independent verification in a complete workflow.
- **Scientific discovery:** evaluate hypothesis generation, informative experiment selection and evidence-based stopping criteria.
- **Engineering applications:** investigate material inverse identification, additive manufacturing and design optimization.
- **Broader simulation support:** explore additional CAE solvers and coupled-physics research.

[Research agenda](docs/vericae/RESEARCH-AGENDA.md) · [Current verification boundaries](COMPATIBILITY.md)
