# Architecture Decision Records

Architecture Decision Records (ADRs) document durable architecture choices for
AegisCAE Runtime.

## Status values

- `PROPOSED`: under review and not authoritative.
- `ACCEPTED`: approved and authoritative until superseded.
- `SUPERSEDED`: replaced by a newer accepted ADR.
- `REJECTED`: considered and explicitly not adopted.

Accepted ADRs must not be modified silently. A later change requires a new ADR that
identifies the earlier record under `Supersedes`; the earlier record then identifies
the replacement under `Superseded by`.

## Minimum ADR structure

Every ADR contains:

```text
Title
Status
Date
Context
Decision
Consequences
Rejected alternatives
Supersedes / Superseded by
```

Number records sequentially as `ADR-NNN-short-title.md`. Architecture ownership,
trust boundaries, dependency direction, execution/write/verdict/evidence authority,
legacy migration policy, compatibility surfaces, and supported Python baselines
require an ADR.
