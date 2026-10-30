# G2 public rod bridge and verification

This is a no-Solver integration implementation. Inert rod Plans, actual Fake IPC
records, and original synthetic DAT bytes are distinct evidence classes. No
source label, fixture capability, parser agreement or native Agent verdict grants
real execution authority. Real A and B remain NOT_RUN.

## Persistence and compatibility

`RodBridge(RealPreviewAdapter(project))` adds explicit `rod-preview-event-v2`
events to the existing ResearchProject audit and short-transaction path. It does
not create another store, migrate SQLite, change the frozen v1 rod contract, or
reinterpret earlier v1 events. An old reader rejects the new version; the new
reader reopens old histories unchanged. Entering v2 requires no v1 attempts, and
subsequent v1 route writes are rejected to prevent mixing allocations or verdicts.

The v2 actions admit a candidate, bind A's inert public PlanRef, reserve one Fake
intent, mark UNKNOWN, and commit exact Fake evidence plus a numerical fixture
observation. Allocation and intent share the existing transaction. UNKNOWN keeps
the allocation; no new-key retry/refund API exists. The global maximum remains
two attempts across A/B Projects, with `real_solver_calls=0`. A second intent is
refused until A has valid committed fixture evidence and the A Owner is reported
closed by the trusted test harness. This is a tested interface contract, not
machine-wide exclusion or OS isolation.

## Public ports and data

The production bridge imports no AF package and never accesses AF SQLite. Its
injected public port supports `prepare(...)` and `inspect(plan_id,digest,at_time)`.
The actual implementation is AF's `product_rod.RodProduct`. A's Candidate bytes
are independently reconstructed before calling this port; the returned persisted
PlanRef is checked against input bytes, frozen contract/tolerances, Project,
revision, resources and output identities. Reopening and exact replay use the
same Plan. A different prepare key, validity window or payload is refused.

`fake_intent` stores the exact `af-fake-plan-ref-v1` before a caller starts or
submits the separately owned Fake fixture. `observe` consumes its original
Receipt, Run, Event and Validation records plus normal-exit proof, checking their
cross-identities and statuses. The rod Plan is never assigned the Fake Grant.
The bridge itself has no submit/owner/launcher or Grant issuance capability.

`rod_evidence.verify_envelope` independently parses bounded DAT bytes and
recomputes displacement, stress, reaction and frozen-goal comparison. It does not
call AF's numerical parser or accept its PASS. AF owns bounded, confined, stable
artifact acquisition; GD-CAE checks its exact returned envelope and independently
recomputes the bytes' digest and numeric rules. Both parsers share the rod theory
and intended output layout, so common specification mistakes remain possible.

A's envelope uses `af-rod-evidence-envelope-v1` from the public AF reader. B in
this rehearsal uses an explicit `SYNTHETIC_NOT_REGISTERED` numerical reference,
`gdcae-synthetic-evidence-envelope-v1` and `stable_read=false`: it is a pure byte
fixture, not a registered real B Plan or AF-acquired B artifact. The resulting
record distinguishes `AF_PUBLIC_STABLE_READ` from `SYNTHETIC_BYTES_ONLY`.

Each new record keeps real V0/V2 NOT_VERIFIED, V1 MODEL_CONTRACT_CHECKED, V3
INCONCLUSIVE, V4 NOT_ASSESSED and ODB_NOT_VERIFIED. Numerical and goal successes
are separately named `fixture_checks`; they cannot satisfy a real research goal.
`validate_real_source_contract` checks the future real metadata schema against a
separately supplied expected binding, including exact typed status, Run/Receipt/
Grant/Plan/input/output/resources/tolerance/entity/unit identities. Its accepted
test data is TEST_ONLY_REAL_SCHEMA_FIXTURE or an untrusted AF_REAL_DECLARATION.
Even matching declarations return source_authentication NOT_VERIFIED and
live_read_enabled=false. It is not an authenticated real artifact reader.

## Causality and bounded Agent view

B is calculated only from a committed eligible A metric and the frozen target,
with A Run, Receipt digest, output digest, verification digest, contract digest,
revision and proposal time/order bound into its proposal. Two admissible A
fixtures at 1 N and U1=0.0099995/0.0100005 mm lead to different loads
2.000100005/1.999900005 N. Both A values meet the frozen analytical tolerance;
this demonstrates sensitivity without asserting physical experimental validity.
A satisfied target, UNKNOWN, wrong identities or missing evidence stops B.

`public_summary` exposes only bounded statuses, scalar metrics and verification
digests. It excludes raw DAT, filesystem paths, Run identities and arbitrary
event payloads. Stored bytes are only for deterministic replay/reverification.

## Test evidence and limitations

First Core invocation: 127 passed / 3 failed. One new test exposed proposal creation
for an already-used phase; a guard now rejects it. Two fault tests expected an
OSError, while the existing Project API deliberately wraps it as
STORE_UNAVAILABLE; their expectation was corrected without weakening rollback
or lost-response assertions. The next invocation passed 130 tests. Expanded
prepare-replay and hard-exit tests passed 132 tests, with no skips. These include
the existing 76 G1 rod cases and overlap, so the counts must not be added.

The contract-focused invocation (`core-g2-contract-final`) passed 158 tests,
0 failed/errors/skipped, exit 0, 11.86 seconds. Final targeted invocation
`core-g2-events-final` passed 162 tests, 0 failed/errors/skipped, exit 0,
12.25 seconds: the existing 76 G1 cases plus 86 G2 cases. These add exact
real-source schema negatives, untrusted matching
declaration checks, runtime-origin consistency, satisfied-A stopping B, fake/rod
separation and the no-third-attempt rule. Final hardening requires unique
REQUEST_ACCEPTED, START_INTENT, FAKE_COMPLETED and VALIDATION_RECORDED events in
that order, with a completed Fake backend outcome, rather than inferring execution
from a final validation PASS. Six changed/new Core Python files pass Ruff with
exit 0. The actual code-under-test did not launch an AF Owner or Solver. These
counts overlap the earlier invocations.

Main owns the fresh cross-repository public API and
actual Fake IPC integration plus installed-snapshot rehearsal; unit fixtures
alone do not establish those passes. Neither interface checks nor SHA-256/local
timestamps establish trusted source authentication, an unforgeable audit, actual
human consent, host-wide resource exclusion or strong Operator separation.
