# VeriCAE CHANGELOG

## 1.0.0 — Research workflow release freeze

2026-11-27. Frozen from the 0.5.6 public package. This release preserves the three native Skills, four persistent research roles, file workspace and Desktop MCP recovery protocol. The installation asset contains a local marketplace, plugin, license, installation guide, release notes and per-file checksums.

UAT-100 on the 0.5.6 baseline passed real Desktop read-only communication with AbqJobPilot 0.5.3 DEV. Autonomous execution of a new real-solver study remains unqualified.

## 0.5.6 — MCP Runtime Verification & Environment Recovery

2026-11-25 · Development baseline. The public branch packages these changes for research evaluation.

- **Desktop Native MCP Runtime Verification**: after adding, re-registering, rebuilding or changing an MCP
  server, the current Desktop Main must discover its actual tools and make a safe, authorized read.
  CLI registration, `codex mcp list/get` and independent tests cannot replace Desktop acceptance.
- **Conditional Desktop restart notification**: investigate configuration loading, project environment and
  session state after discovery fails. Prompt for a full restart only when runtime refresh is needed;
  a successful connection does not require a restart.
- **Original Main Resume and environment recovery**: return to the original project/Main, restore current
  files and reverify identity, version, tools, permission boundaries and actual responses before unblocking work.
- **Research State Preservation**: preserve Card, Task Cards, existing role identities and recovery entrypoints;
  retain pending/unknown tasks and append-only history rather than recreating agents or discarding research.
- **Setup/Main responsibility boundary**: Setup reports read-only diagnostics; Main alone saves primary
  research state. The user controls Desktop restart after other running tasks have safely stopped.
- **Separate environment/evidence verdicts**: READY_TO_RESUME resolves only the environment blocker.
  It neither grants execution permission nor changes FAILED, REVIEW_REQUIRED, INSUFFICIENT or scientific qualification.

Includes the accepted source improvement at `fdaa423f9b3d422551446f1f2be67cbd7f1a7b0a`.
The user package remains three Skills, optional native role configs, Markdown/YAML templates and static protocols;
no additional Python/Node/EXE runtime, database or communication service is introduced.
