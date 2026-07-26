# ADR-001: Runtime-first

## Status

ACCEPTED

## Date

2026-07-26

## Context

The legacy repositories contain useful Abaqus domain and job-lifecycle knowledge,
but neither legacy control plane satisfies the invariants of the new Controlled CAE
Runtime. Beginning with adapter code would preserve old execution, workspace, path,
authorization, and evidence assumptions before the new trust boundary existed.

## Decision

先建立独立 Runtime contracts 和控制平面，再迁移任何 Abaqus legacy capability。

Runtime Core will be rebuilt from new invariants. Source artifacts will be immutable
by default, deterministic Runtime/Validator logic will retain verdict authority, and
the future Unified Executor and ControlledWorkspace will be the exclusive production
execution and write boundaries.

Milestone 0 creates documentation and empty package namespaces only.

## Consequences

- Abaqus capability is unavailable until new public contracts and controls exist.
- Legacy code may inform later design but cannot become the control plane directly.
- Adapter extraction must wait for the Runtime-owned boundaries required by its Batch.
- Review can evaluate Runtime authority independently from solver-specific behavior.

## Rejected alternatives

Rejected: 先复制 AbqPilot，再补 Workspace 和 Executor。

Also rejected are renaming either legacy repository and treating its existing
Runtime-like modules as the new Runtime Core.

## Supersedes / Superseded by

Supersedes: None.

Superseded by: None.
