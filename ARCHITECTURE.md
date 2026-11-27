# VeriCAE 1.0.0 architecture

VeriCAE organizes computational research in Codex Desktop. Its project files hold the research question, model assumptions, role reports and decisions. A separately configured MCP connection lets the team request execution or inspect recorded evidence in AbqJobPilot. Planning and offline model review work with VeriCAE alone. [Compatibility and verification scope](COMPATIBILITY.md)

| Layer | Responsibility | Records |
| --- | --- | --- |
| VeriCAE in Codex Desktop | Define the question and acceptance criteria, review the model and decide which conclusions the evidence supports | Research Contract, Research Card, Task Cards, model definition, handoff and research reports |
| AbqJobPilot on Windows | Check project identity, Plan, Grant and budget, supervise authorized processes and record what happened | Acceptance Receipt, Run and Attempt, outcomes, artifact bindings and versioned validation |

## Research decisions

Initiate prepares the Research Contract and handoff. Conduct restores that state in the project's Main conversation. Main is the sole writer of primary research state. It dispatches scoped Task Cards to CAE to examine the physics, Results to check observations and their provenance, and Independent Validation to challenge assumptions and check the result independently. Main reads their original replies and records the decision to continue, revise the experiment or stop. [Role and dispatch protocol](product/vericae/vericae-research/references/cross-thread-protocol.md)

## Execution and evidence

A research agreement does not authorize a solver run. For delegated execution AbqJobPilot checks the bound Project, Plan and Grant. On acceptance, it persists a Receipt and creates a Run. The client can retrieve the original Receipt by submission key and look up the outcome and validation evidence by Run ID. The historical axial-bar study illustrates why numerical agreement, process completion and output provenance have separate verdicts. [INT-001 case record](docs/vericae/INT-001.md)

## Host and recovery

Codex provides conversations and native cross-thread messaging. VeriCAE requires no separate runtime or database. Setup checks tool registration, discovery in the active Desktop Main, an authorized read and the responding service's identity. Before a necessary Desktop refresh, Main saves the research state. On resume, the original conversation checks identity, version and permissions again. [MCP recovery protocol](product/vericae/vericae-research/references/mcp-runtime-verification.md)

## Source map

| Location | Contents |
| --- | --- |
| [Research plugin](product/vericae/vericae-research/) | The three skills, role definitions, templates and protocols |
| [Marketplace catalog](product/vericae/.agents/plugins/marketplace.json) | The local plugin entry and its source path |
| [Release tools](product/vericae/release/) | The reproducible package builder, checks and frozen install guide |
| [Developer tools](product/vericae/developer/) | The optional file-based research workspace checker |
| [Research materials](docs/vericae/) | The public evidence replay, case findings and research agenda |
| [Development archive](docs/archive/README.md) | Historical architecture, acceptance records and the original source trees for AegisCAE and GD-CAE |

For the Windows execution implementation, see the [AbqJobPilot repository](https://github.com/BrunelXian/AbqJobPilot).
