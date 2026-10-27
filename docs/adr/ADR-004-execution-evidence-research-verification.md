# ADR-004: Execution evidence and independent research verification

## Status and authorization

**ACCEPTED — authority separation and M01-A read-contract scope only.**

Date: 2026-10-28.

Authority: the researcher's explicit M01-A approval in the development
conversation. This ADR does not implement a verification engine, approve a model,
issue execution permission, or certify the independence of any deployment.

## Context

A receipt, a process observation, Solver completion text, a DAT comparison, a goal
metric, and a physical validation claim answer different questions. Combining them
into a single success flag would erase missing evidence and scope limitations.

The previous architecture assigned machine-verdict ownership to Runtime/Validator
logic without the new delegated execution boundary. Under ADR-003, AF owns its
recorded execution facts; GD-CAE must not recreate or revise them.

## Decision

AF is the sole source for its recorded job, process, authorization, and Solver
facts. GD-CAE may produce explicitly sourced, bounded read projections. It must not
convert those projections into newly asserted execution facts.

The future GD-CAE verification engine owns independently computed research-level
checks against frozen contracts. A Codex Main or Independent Reviewer produces
proposals and advisory findings, not authoritative VerificationRecords. Neither a
Markdown report nor an agent's `PASS` is a substitute for deterministic checks.

| Layer | Required distinction | M01-A capability |
| --- | --- | --- |
| V0 — Provenance | Inputs, Run/attempt, artifacts, versions, and hashes must be bound to the intended identities | Validate read binding and response shapes; report source fields without claiming complete artifact provenance |
| V1 — Model integrity | A candidate must preserve the approved model contract and permitted mutation scope | Not implemented |
| V2 — Solver/numerical health | Managed-scope completion, Solver evidence, convergence, and numerical checks have distinct scopes | Read existing AF fields only; no new Solver or numerical validation |
| V3 — Goal acceptance | Frozen metric/entity/step/unit/tolerance must be evaluated independently | Not implemented |
| V4 — Physical validation | Applicable analytic, benchmark, independent-model, or experimental support must exist | Not implemented; no inferred validation |

These are the M00-P product verification layers, as also described in the
DOC-001 README proposal; they are not a claim that the historical M00 Runtime
implemented five validators. M01-A emits no V0-V4 VerificationRecord. Its binding
checks are a limited provenance prerequisite, and its status/validation projections
are attributed AF observations. In particular, `fixed_standard_dat_only` and
`simulation` records cannot establish model integrity, goal acceptance, or physical
validation, even when their recorded verdict is `PASS`.

## Unknown and incomplete evidence

- An unknown or absent source field remains unknown or absent. Never fabricate a
  Run revision, artifact hash, output field, or successful check.
- `UNKNOWN` and `INCONCLUSIVE` block decisions that require resolved evidence.
  A transport error is not evidence that a submission never occurred.
- `NOT_RUN` denotes a check not performed; `NOT_ASSESSED` denotes physical
  applicability/support not assessed. Neither is a pass nor an automatic failure
  of an unrelated check.
- Read-envelope success means that the bounded projection was obtained. It does
  not mean `GOAL_SATISFIED`, `ODB_VALID`, or `PHYSICS_VALIDATED`.
- Completeness applies to the declared read scope. A complete page is not a
  complete history, a field whitelist is not a full artifact, and several read
  calls do not form a single atomic snapshot.

In later milestones, a Goal must declare its required V0-V4 checks before
candidate generation. Goal satisfaction requires all mandatory checks to be
resolved and passed, with no outstanding blocking review findings. A change to
criteria or validator identity requires a new approved contract version.

## Artifact and reviewer trust

Hashes detect byte changes but do not establish trusted origin or physical
validity. AF's diagnostic public-body digest is not a signature or a digest of all
original records. Read views must state that distinction.

Future ODB extraction must bind the source Run/attempt, source artifact, extraction
script version, requested fields/regions/steps, and output identity. Requiring an
Abaqus process still makes extraction controlled external execution under ADR-003;
calling it read-only does not authorize a separate launcher.

An advisory Reviewer should challenge assumptions and inspect independent evidence.
Using another agent with the same writable inputs and validator does not prove
independent numerical validation or OS isolation. Frozen code/criteria, explicit
provenance, appropriate independent references, and deployment permissions require
their own verification.

## Historical supersession and retained rules

This ADR narrows the old Runtime's exclusive machine-verdict authority only where
it conflicts with AF's ownership of recorded execution facts. It retains
deterministic research-verdict authority, source immutability, fixture/physical
evidence separation, fail-closed behavior, and the rule that reports are views.

Historical ADRs, original invariant text, and frozen baselines remain byte-preserved.
The [current authority register](../architecture/CURRENT_AUTHORITY.md) maps every
old invariant to its current scope.

## Acceptance boundary

M01-A acceptance is `SYNTHETIC_CONTRACT_PASS` only when its offline tests actually
pass. `AF_READ_COMPATIBILITY_VERIFIED` requires M01-B. Neither status proves
Solver execution, ODB validation, model integrity, research acceptance, physical
validation, or automatic Codex continuation.

See [ADR-003](ADR-003-codex-native-delegated-execution.md) and the
[read contract](../architecture/M01_EVIDENCE_BRIDGE.md).
