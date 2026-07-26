# AegisCAE Runtime Architecture

Status: Milestone 0 — Architecture Freeze

## 1. System purpose

AegisCAE Runtime is a new, solver-neutral Controlled CAE Runtime. Its intended
purpose is to provide deterministic, authorized, workspace-confined, and auditable
control for future CAE workflows. Milestone 0 defines boundaries only; it does not
implement Runtime behavior or Abaqus capability.

## 2. Trust boundary

The future Runtime boundary will separate untrusted requests, plans, adapters,
external tools, solver artifacts, and presentation reports from Runtime-owned
authorization, execution, controlled storage, validation, verdict, and evidence
authority. Inputs crossing that boundary must eventually be represented by explicit
contracts and handled fail-closed. No such control-plane implementation exists in
this Batch.

## 3. Runtime Core ownership

Runtime Core will exclusively own execution authorization, controlled mutation,
workflow state, artifact provenance, evidence lifecycle, and final orchestration.
Production subprocess creation will belong only to the future Unified Executor.
Production writes will belong only to the future ControlledWorkspace.

Runtime Core is rebuilt from new invariants. Legacy runtime classes, state machines,
workspace guards, launchers, and evidence authorities are not the new control plane.

## 4. Validation ownership

`aegiscae.validation` will own solver-neutral deterministic validation contracts.
Runtime will own validation orchestration and final machine-verdict authority.
Adapter-specific validation will remain behind adapter boundaries and will not
become Runtime private logic.

Milestone 0 creates only the namespace marker and no Validator implementation.

## 5. Interface ownership

`aegiscae.interfaces` is reserved for future client-facing surfaces over public
contracts and the Runtime public facade. Interfaces cannot launch tools directly,
write around the workspace boundary, or reach private Executor internals. No CLI,
MCP, GUI, LLM, queue, or compatibility interface is created in this Batch.

## 6. Abaqus Adapter ownership

`aegiscae.adapters.abaqus` is reserved for future Abaqus-specific contracts,
command planning, diagnostics, artifact interpretation, and domain validation.
Adapters will not own subprocess execution, uncontrolled writes, authorization,
Runtime state, or final evidence authority. The namespace is empty in Milestone 0.

## 7. Dependency direction

An arrow means that the package on the left may import the package on the right.

```text
contracts  -> Python standard library only
validation -> contracts
runtime    -> contracts and validation public contracts
adapters   -> contracts and validation public contracts
interfaces -> contracts and runtime public facade
```

These permissions are upper bounds, not evidence that an import or implementation
already exists.

## 8. Future composition root

A future composition root may assemble Runtime public contracts and concrete
adapters. It will be the only place where those concrete implementations meet.
The composition root is deferred until public contracts and registration rules
exist and is not created in this Batch.

## 9. Prohibited dependency directions

The following directions are prohibited:

```text
runtime -> concrete adapters
adapter -> runtime private internals
validation -> adapter
contracts -> runtime / validation / adapters / interfaces
interfaces -> raw launcher or private Executor internals
```

Direct or indirect dependency on `abqpilot` or `abqjobpilot` is prohibited.

## 10. ADR-required architecture changes

Changes to ownership, trust boundaries, dependency direction, execution or write
authority, verdict or evidence authority, legacy migration policy, compatibility
surfaces, or the minimum Python version require a reviewed ADR. An accepted ADR is
not edited silently; a later decision must supersede it.
