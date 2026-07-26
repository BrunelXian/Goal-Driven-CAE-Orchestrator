# AegisCAE Runtime

AegisCAE Runtime is a new **Controlled CAE Runtime**. It is an independent project,
not a rename of AbqPilot or AbqJobPilot.

```text
Current status: Milestone 0 — Architecture Freeze
Python package: aegiscae
```

This repository currently contains architecture governance, frozen documentation
snapshots, and an empty Python namespace skeleton. Runtime Core has not been
implemented. The project cannot run Abaqus and has no Solver, ODB, CAE, MCP, Skill,
GUI, LLM, or queue capability.

## Governing documents

- [Architecture](ARCHITECTURE.md)
- [Runtime invariants](RUNTIME_INVARIANTS.md)
- [Threat model](THREAT_MODEL.md)
- [Migration from legacy](MIGRATION_FROM_LEGACY.md)
- [Baseline register](docs/baseline/BASELINE_REGISTER.md)
- [Milestone 0 implementation plan](docs/milestones/MILESTONE_00_IMPLEMENTATION_PLAN.md)
- [ADR-001: Runtime-first](docs/adr/ADR-001-runtime-first.md)
- [ADR-002: Selective legacy migration](docs/adr/ADR-002-legacy-selective-migration.md)
