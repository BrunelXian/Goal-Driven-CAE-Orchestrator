# M02-B1 — Model Mutation Guard

Implementation status: implemented, synthetic-only. Acceptance evidence belongs to the delivery report.

## G1: terminology and compatibility decision

`ScientificConstraint` in frozen schema 1 means a metric acceptance limit over displacement,
stress, reaction_force or strain at a specific selector. Its V3 mapping remains unchanged.
It is not the union of every scientific, model, provenance and resource constraint. The M02-A
phrase “all hard constraints” applies only to this metric DTO and must not be generalized.

| Meaning | Owner | Existing frozen source |
|---|---|---|
| Input/version identity | V0 | Project/Bundle/part IDs and artifact manifest |
| Permitted model change | V1 | Model/Goal allowed and forbidden categories, semantic selectors |
| Numerical validity | V2 | required_checks.V2 and validator reference |
| Metric acceptance | V3 | objective, ScientificConstraint, hard_constraint_checks |
| Physical applicability | V4 | required_checks.V4 and physical_reference |
| Resource/authorization policy | Policy | budget and explicit absence of execution authority |

A new versioned, derived mutation-admission coverage description will reference these fields;
it will not relabel historical rules or alter a frozen ContractBundle schema. Shared rules and
multi-rule dependencies are represented explicitly. Unknown evidence blocks the decision
requiring it; V2/V3/V4 remain deferred for a mutation-only admission, and block scientific claims.
Independent reviewer confirmed no mandatory frozen-schema migration for this bounded design.

Persistence decision: append a new explicitly versioned Candidate publication event to the
existing audit table, with a separately validated payload. No new database, table migration or
rewrite of old events/parts/bundles. Project revision continues to mean contract-state revision;
candidate operations compare it under BEGIN IMMEDIATE, while audit sequence serializes events.
Old readers reject unknown event kinds; forward compatibility is not claimed. Candidate events
are historical observations, not continuing assurances that files still exist.

## G2: syntax review and selected operator

The [SIMULIA CLOAD reference, university-hosted copy](https://abaqus.uclouvain.be/English/SIMACAEKEYRefMap/simakey-r-cload.htm)
describes node/set, DOF and magnitude, but also contextual amplitude/operation behavior and
other options. A scalar replacement alone cannot qualify an arbitrary INP model. This milestone
therefore chooses the taskbook's fallback: **NOT_ABAQUS_QUALIFIED synthetic text**, not an Abaqus parser.

Implemented profile `synthetic-load-v1` is ASCII, LF-only, exact line order, optional single bounded
COMMENT data line, no includes or executable statements. Immutable lines describe fixed units,
material, boundary, mesh, contact, step/entity/frame/DOF and anchor. Only the final `LOAD_N`
decimal token may change. Fixed engineering range is 0–100 N inclusive; caller limits must equal
the profile. The profile only supports Beam/Tip NODE_SET, Load step/frame 1, DOF 1, load_tip anchor.
All non-approved bytes must compare exactly under a second deterministic checker. No real model
data will be read, copied or parsed.

Exact baseline example (10 is the old scalar; the new value can be any canonical Decimal in range):

```text
GDCAE_SYNTHETIC_V1 NOT_ABAQUS_QUALIFIED
UNITS mm N s MPa
MATERIAL E=210000
BC FIXED=Base
MESH FIXED=mesh1
CONTACT NONE
STEP Load
ENTITY Beam.Tip NODE_SET
FRAME 1
DOF 1
ANCHOR load_tip
LOAD_N 10
END
```

Final LF is mandatory. One optional `COMMENT ` line containing at most 128 printable ASCII
characters is allowed immediately before LOAD_N. It is inert immutable data, never returned
as an instruction or used to expand policy. A comment may contain arbitrary advice, but cannot
insert a newline, extra keyword, second target or executable statement. Maximum input 8192 bytes.
The source filename is exactly `baseline.txt`. `.cae`, `.py`, INP keywords including `*INCLUDE`,
repeated loads, arbitrary replacement expressions and other fixture layouts are unsupported.

Numeric values use the M02-A Quantity Decimal-string validator. Floats, NaN/Infinity, exponents,
locale commas, leading/trailing zeros, negative values, non-N units and other dimensions reject.
The caller supplies lower/upper quantities but they must exactly equal the fixed 0/100 N profile;
they are not an authority to widen its limits. A no-op is rejected. Material E, boundary, mesh,
contact, target identifiers and every byte outside the numeric span must remain unchanged.

## Typed request and independent check

`research.mutation_rules.MutationRequest` is separate from frozen ContractBundle schema 1.
It has schema/operator versions, candidate ID, idempotency key, synthetic workspace ID, staging
identity, Project ID/revision, four frozen digests, baseline artifact ID/hash/size, filename,
exact target selector/DOF/anchor/parameter and old/new/lower/upper Quantity values. Unknown and
missing fields reject. IDs use fixed prefixes and UUID-shaped hexadecimal values. Paths and
free-form patches are not request fields. Requests are canonicalized and hashed.

The parent must be the currently frozen Bundle for a new candidate, with matching Project and
all four digests. Both Goal and Model must allow load changes and Goal must not forbid them.
This operator accepts one synthetic BASELINE artifact with no dependencies, `DECLARED_ONLY`
closure and the supported units/entity/frame. Any additional or unresolved dependency is
unsupported; the guard never tries to resolve includes or read extra files.

The editor replaces its parser-selected numeric span. `check_diff` independently parses both
byte strings, compares line count and each line, requires exactly one changed LOAD_N line,
checks old/new quantities and separately compares the full prefix and suffix. It does not call
the editor. The manifest contains request/baseline/output digests, output size, 1-based line,
0-based byte offset, old/new token lengths, prefix/suffix hashes and versioned coverage.
Tests replace the editor with an illegal extra modification to prove this second check rejects it.

Coverage defines six uniquely named V0/V1/V2/V3/V4/Policy rules and explicit source-field edges.
Artifact identity references both V0 and V1; objective and multiple metric constraints may share
the V3 rule. No rule is orphaned. The stored coverage must equal the deterministic derivation;
removing a mandatory constraint edge, even while recomputing record digests, is rejected.
V0/V1 entries identify requirements for mutation; V2/V3 remain NOT_RUN, V4 NOT_ASSESSED,
Policy NOT_ENFORCED_NO_EXECUTION. This is not a VerificationRecord.

## Synthetic workspace and publication API

`create_synthetic_workspace(explicit_new_root)` exclusively creates a new root under the OS TEMP
directory, a `staging` subdirectory and `synthetic.json`. The marker binds workspace ID, canonical
root digest and root/staging filesystem identities. It does not create a model. Only the trusted
test fixture prepares baseline.txt; the guard opens the baseline readonly. No CWD inference,
existing root reuse, nested repository/AF/ResearchProject path or `CAE models` component is allowed.
Every path uses lstat/reparse/hardlink checks; marker/file reads are bounded and checked before/after.
This is local cooperative ownership protection, not a hostile same-user/administrator sandbox.

`propose_mutation(explicit_write_project, workspace, request)`:

1. Strictly validates request and workspace, then obtains the existing Project write transaction.
2. Checks exact replay/conflict, Project revision and immutable parent references; reads baseline.
3. Computes an edit and independently verifies it before staging.
4. Exclusively creates `staging/<stage_id>/`, writes `INCOMPLETE.json`, then `candidate.txt` with
   exclusive binary opens, flush and fsync. Never overwrites or renames the baseline/output.
5. Rechecks marker, source, candidate and diff, appends the versioned audit event, rechecks again,
   commits and rechecks after commit before returning PERMITTED.

Publication is the database observation plus a successful live recheck, not merely the presence
of candidate.txt. The INCOMPLETE marker intentionally remains even after a successful commit:
it means directory contents alone cannot prove publication. There is no completion marker that
could be mistaken for authority after an interrupted DB write. Unknown extra files invalidate readback.

Identical replay never rewrites artifacts or records, but revalidates the actual staged files.
Same key/different request, reused candidate identity or output identity rejects. Under concurrent
writers the SQLite transaction admits one effective record; a competing call may replay or return
STORE_BUSY. After a failure before the record commits, an existing orphan directory is never reused;
this milestone has no resume/cleanup function or automatic retry.

`inspect_candidate(readonly_project, workspace, candidate_id)` returns a bounded result after
recomputation. A missing/corrupt/unbound file produces INCONCLUSIVE even if a historical publication
event exists. `contract_revision`, `current_project_revision` and `scope` distinguish a current
mutation from `HISTORICAL_MUTATION` after a later freeze. Historical replay/inspection makes no
new admission under the later contract; new candidates require the current revision and parent.
The only positive claim is MODEL_MUTATION_PERMITTED_ONLY; execution_authorized is always false.

## Compatibility, crash policy and limits

No M02-A DTO, table schema, old audit bytes or frozen Bundle/part bytes are rewritten. The only new
persisted shape is `CANDIDATE_PUBLICATION_OBSERVED` with `candidate-publication-v1` payload and
`mutation-diff-v1`/`mutation-coverage-v1` nested versions. Candidate uniqueness, parent revision,
coverage and metadata digest are checked while reading the existing audit chain. Revision remains
the contract-state revision; candidate journal events have their own unique audit sequence/transaction.
Old binaries fail closed on this new event kind and should not be used to write a Project after B1 events.

Exception/child-process fault tests cover before staging, partial staging, after file/before DB,
before commit and after commit/before response. Incomplete or orphan outputs remain recognizable;
they are never auto-repaired, adopted or deleted. A committed record with changed/missing files is
inconclusive. This is not a single atomic filesystem+SQLite transaction or a power-loss certification;
fsync and readback improve durability, but directory metadata/hardware failures are not proven here.

The M02-A journal policy remains: any journal/WAL/SHM blocks product opening with STORE_BUSY.
A hard exit during the DB transaction can therefore block even readonly audit access. No attempt
is made to remove journals, force locks, recover the DB or infer a missing event means “not accepted”.
If opening is safe, audit_events can expose historical observations; it cannot validate files itself.
A future separately reviewed administrative design could inspect a bounded copy with recorded hashes,
distinguish cold/hot journals and obtain explicit recovery authorization. None is implemented here.

Limits: one artificial grammar/operator, fixed target and range, 8192-byte files, existing bounded
audit/store capacity, no real include closure, no physical/numerical validation or authentication.
An external actor can modify files immediately after a successful read; consumers must recheck at
their own decision boundary. Some low-level creation APIs can raise native OS exceptions; the public
proposal/read result suppresses raw filesystem exception text. New corpus growth must not be
represented as a BudgetLedger: budget enforcement remains absent and is proposed separately.

## M02-B2 boundary

BudgetLedger is only a design proposal in the delivery report. No reservation, AF receipt query,
submission, grant, solver invocation, workflow, event bridge or Codex continuation is implemented.
