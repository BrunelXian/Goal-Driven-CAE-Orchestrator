# Migration from Legacy

Status: Milestone 0 — selective migration policy frozen

## Source roles and governing decision

```text
AbqJobPilot:
  role = Abaqus Job Lifecycle Adapter legacy reference

AbqPilot:
  role = Abaqus Domain Adapter legacy source

Runtime Core:
  REBUILD

whole repository copy:
  PROHIBITED

direct dependency:
  PROHIBITED

migration mode:
  copy-by-selection, refactor-behind-new-contracts
```

`LEGACY_MIGRATION_DECISIONS.md` is the final authority when legacy summaries,
project planning, or this operational summary conflict.

## KEEP

KEEP means retain verified domain knowledge and test intent, not copy files
unchanged. Candidate knowledge includes narrow command-construction semantics,
bounded log parsing and classification, read-only monitor helpers, deterministic
diagnostic rules, INP inspection, declared-edit validation, and selected ODB
extraction concepts.

## REFACTOR

Reusable pure logic must be extracted by selection and reshaped behind new
`aegiscae` contracts. Abaqus-specific behavior remains in the Abaqus Adapter.
Direct paths, process creation, writes, authorization assumptions, verdict creation,
and legacy data shapes must be removed or replaced at the new boundary.

## REPLACE

Runtime Context, workspace control, execution control, authorization lifecycle,
workflow/session state, artifact provenance, evidence authority, legacy report
authority, and unsafe local queue behavior are rebuilt from the new Runtime
invariants. Legacy implementations are evidence and design input only.

## DO NOT MIGRATE

Do not migrate whole repositories, legacy Git history, public raw launchers,
GUI-driven execution, Stage-driven orchestration, placeholder rollback, arbitrary
code builders, legacy evidence-freeze authority, hard-coded paths, runtime/output
state, generated artifacts, or compatibility packages without a later ADR.

## Extraction policy

Any later extraction must:

1. identify a specific approved migration-matrix entry;
2. define the new contract and ownership boundary first;
3. copy only the selected logic or test intent;
4. record legacy provenance without adding a package dependency;
5. remove legacy execution, write, path, and authority assumptions;
6. add deterministic tests in the appropriate later Batch;
7. undergo review as new AegisCAE Runtime code.

The Runtime Foundation PR is a read-only design seed only. It is not a branch to
merge, a control plane to vendor, or authority to import legacy packages.

## Batch 01 declaration

The number of legacy Python files migrated in this Batch is **0**.
