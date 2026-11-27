# VeriCAE 1.0.0 architecture

VeriCAE coordinates a computational engineering study in Codex Desktop. AbqJobPilot is a separately installed Windows product that controls execution and records its evidence. The two products communicate through an explicitly configured MCP connection. Planning and offline model review work with just the VeriCAE plugin. [Release compatibility](COMPATIBILITY.md)

| Layer | Owns | Persisted evidence |
|---|---|---|
| VeriCAE in Codex Desktop | Research objective, scope, model assumptions, Task Cards and scientific conclusions | Markdown/YAML Research Card, Task Cards, model definition, Handoff, role reports and research logs |
| AbqJobPilot on Windows | Project and Owner identity, Supervisor, Plan, Grant, budget, backend dispatch and process supervision | Acceptance Receipt, Run and Attempt, outcome, artifact bindings and versioned validation |

## Research decisions

Initiate agrees the Research Contract and prepares the Handoff. Conduct restores that state in the project's Main conversation. Main is the sole writer of primary research state and dispatches bounded Task Cards through native cross-thread communication. CAE examines the physical model. Results checks the recorded observation and its selector. Independent Validation derives or checks the finding independently. Main connects their original replies to the scientific decision. The three optional specialist TOMLs accompany the four persistent roles. [Role and dispatch protocol](product/vericae/vericae-research/references/cross-thread-protocol.md)

## Execution evidence

A Task Card describes the research work. AbqJobPilot separately checks the bound Project, Plan and Grant for any delegated submission. On acceptance it persists the Receipt and creates the Run. A client can retrieve the original Receipt by submission key and the Run by ID. Subsequent execution adds outcomes and validation evidence to that Run. Scientific agreement, process completion, output provenance and qualification each answer a different question. [Historical example](docs/vericae/INT-001.md)

## Connection and recovery

Setup reports registration, tool discovery in the active Desktop Main, an authorized read and verification of the actual service response. Main preserves research state before a necessary Desktop refresh. On resume, the original project and conversation recheck identity, version, permissions and response before continuing dependent work. VeriCAE's package contains three Skills, role definitions, templates and static protocols. Codex supplies the host runtime. [MCP recovery protocol](product/vericae/vericae-research/references/mcp-runtime-verification.md)

Historical GD-CAE Core and AgentHub material remains available for readers tracing earlier designs. The packaged 1.0.0 research workflow requires neither service. [Historical architecture at its original revision](https://github.com/BrunelXian/Goal-Driven-CAE-Orchestrator/blob/4dbd849acb7cf0caf50d81d5f31326afd9fa5e5e/ARCHITECTURE.md)
