# ADR-002: Legacy selective migration

## Status

ACCEPTED

## Date

2026-07-26

## Context

AbqJobPilot is an Abaqus Job Lifecycle Adapter legacy reference. AbqPilot is an
Abaqus Domain Adapter legacy source. Both contain selected useful knowledge and
tests, but also contain ownership, execution, path, UI, Stage, queue, and evidence
assumptions that are prohibited in the new Runtime.

## Decision

Migration follows these rules:

```text
no whole-repository copy
no direct dependency
no legacy Git history
selective extraction only
Runtime Foundation PR is design seed only
```

Any later extraction is copy-by-selection and refactor-behind-new-contracts. It must
be assigned to the new owner, stripped of legacy authority assumptions, and reviewed
as new AegisCAE Runtime code.

## Consequences

- Legacy packages cannot be runtime or development dependencies.
- Useful behavior is migrated only through an approved matrix entry in a later Batch.
- Provenance may cite legacy sources without importing or vendoring them.
- This Batch migrates zero legacy Python files.
- A compatibility package is deferred and requires a later ADR after the adapter
  surface is stable.

## Rejected alternatives

- Copying either repository wholesale.
- Depending directly on `abqpilot` or `abqjobpilot`.
- Importing legacy Git history into the new repository.
- Merging or copying the Runtime Foundation PR as the new control plane.
- Creating a compatibility package during Milestone 0.

## Supersedes / Superseded by

Supersedes: None.

Superseded by: None.
