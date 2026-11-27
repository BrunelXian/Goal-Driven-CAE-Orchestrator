# G3 bounded public evidence consumption

Status: `PASS_OFFLINE` for the Core contract and negative tests described below.
This is not real Solver qualification, authenticated real DAT provenance, HIL
enforcement, or a claim that real A/B executed.

## Scope and reuse

`research/rod_public_evidence.py` adds `PublicRodEvidence(preview)`. It imports no
AF package, accesses no filesystem, opens no AF database, starts no process, and
issues no Grant. An injected public read port owns acquisition. The existing
G2 verifier independently recomputes displacement, stress, reaction, equilibrium
and analytical scale from the bounded synthetic DAT bytes.

The only existing production change is `RodBridge.observe_public`. It verifies a
public bundle and then uses the unchanged G2 `G2_OBSERVE` transaction. No new
reducer, event version, SQLite migration, frozen-contract schema, MCP tool, or
Agent Harness is introduced. The original seven MCP tools are unchanged.

## Committed contract identity

The rod preview has one combined immutable `rod-preview-contract-v1`, not
independently versioned GoalContract and ModelContract rows. `frozen_identity()`
reads public `ResearchProject.audit_events`, requires exactly one committed
`FREEZE`, and checks its content and digest against the replayed current state.
The initial freeze is committed at project revision 2. Read-before/read-after
checks reject project changes during this bounded acquisition.

The returned `shared_bundle_freeze_revision` identifies the common freeze.
AF's `goal_revision` and `model_revision` are independently checked request pins
for this same value; they are **not** asserted to be separate AF-persisted
component versions. AF's `research_revision` remains the original Plan
preparation revision. Core's `current_project_revision` may advance beyond both.

Component digests use canonical JSON of explicitly versioned projections:

| Component | Fields |
| --- | --- |
| Goal | `goal_min_mm`, `goal_max_mm`, `target_entity`, `units` |
| Model | `profile`, `baseline_digest`, `load_min_n`, `load_max_n`, `units` |

The model's baseline digest pins the complete frozen template, including material,
geometry, mesh, boundary and output selectors. The combined contract digest also
pins numerical tolerances and budget policy. Ordinary hashes and event timestamps
provide consistency and correlation checks, not tamper-proof authentication.

## Public input and independent checks

The accepted bundle is `af-rod-public-evidence-bundle-v1`. Only the two explicit
sources `AF_FAKE_IPC_PLUS_SYNTHETIC_DAT` and
`OFFLINE_PUBLIC_PORT_FIXTURE_PLUS_SYNTHETIC_DAT` are allowed. Source labels alone
do not establish authenticated real provenance.

Core checks:

- Exact persisted inert rod Plan, candidate bytes/digest, Project, contract,
  resources, tolerances, output identity and preparation revision.
- Public persisted Fake Plan identity against the independently committed Fake
  intent; the Fake Plan and rod Plan remain separate.
- Exact original Receipt, Run, Events and Validation equality against the
  separately supplied completed Fake evidence and owned-process close proof.
- `REQUEST_ACCEPTED`, `START_INTENT`, `FAKE_COMPLETED`, `VALIDATION_RECORDED`
  exactly once and in order; per-Run sequences and payload revisions 1–4 agree
  with terminal Run revision 4. Final evidence references include the Validation
  and its observation references.
- Fake backend/outcome, attempt number, no retry, terminal execution, no
  reconciliation, non-applicable Solver process/exit observations, and `NOT_RUN`
  Solver conclusion. Missing records, unknown status or conflicting attempts
  are refused.
- Public bundle canonical digest, stable synthetic artifact metadata, exact
  output digest/bytes, units and entities, followed by independent numerical
  recomputation. AF's reported PASS is not accepted as numerical proof.

Bundle digests follow AF UTF-8 canonical JSON. The `dat_bytes` value is excluded
from that JSON projection; its exact bytes are independently bound by the
artifact content digest. The entire JSON projection remains bounded by existing
Core canonical-data limits, and DAT content remains bounded to 16 KiB.

The interface requires `raw_solver_logs = ABSENT_NOT_REAL_SOLVER`. Substituting a
Solver-looking string, claiming real execution, or providing an unqualified
real-schema declaration cannot unlock real evidence acceptance. A future real
reader must separately prove authorized Run and raw log/artifact provenance;
this implementation provides no branch that enables that reader.

## Lifecycle and API recipe

For actual TEST_ONLY IPC, acquire the public bundle **while the owned Fake Owner
is alive**. Afterwards close that Owner using the test harness and retain its
actual close result. Do not try to call a live port after its Owner has exited.

```python
verifier = PublicRodEvidence(bridge.preview)
identity = verifier.frozen_identity()
# AF public read occurs here, with both component revision pins set to:
revision_pin = identity["shared_bundle_freeze_revision"]
# bundle = AF read_test_evidence(... goal_revision=revision_pin,
#                               model_revision=revision_pin, ...)
# raw = {**completed_fake_evidence, **actual_owner_close_result}
record = verifier.verify(bundle,
    expected_revision=bridge.inspect()["project_revision"], fake_evidence=raw)
result = bridge.observe_public(bundle, raw,
    bridge.inspect()["project_revision"], "observe_public_A")
```

`read(port, expected_revision=..., fake_evidence=..., evidence_key=...,
output_digest=..., at_time=...)` is a convenience for an **offline or retained
immutable** public snapshot port. It performs one read call and never retries a
lost response. Project advancement during that call is rejected.

The thin `observe_public` method returns `workflow` and `verification`. Existing
raw Fake evidence and the numerical envelope are persisted by the unchanged G2
event. The additional public-acquisition record is returned to the caller and
explicitly has `public_record_persisted = False`; it is not silently inserted
into the historical event format. A test harness can retain it in its private
audit package. A durable public-acquisition journal would require separate
review and is not claimed here.

Exact G2 event-key replay has one effect. New concurrent observers cannot both
commit at the same revision. A pending or UNKNOWN intent retains its existing
allocation, and absent a verified observation it cannot produce B. After an
accepted test observation, B uses the existing causal binding and two-attempt
budget; B remains `SYNTHETIC_NOT_REGISTERED` with no real Plan/Grant. The wrapper
does not reserve, refund, or enlarge a budget.

## Verification status

| Dimension | Current returned meaning |
| --- | --- |
| Acquisition | `PASS_TEST_ONLY`, with explicit offline/IPC source |
| V0 | `NOT_VERIFIED` for real provenance |
| V1 | `MODEL_CONTRACT_CHECKED` |
| V2 | `NOT_VERIFIED` for real Solver/numerical evidence |
| V3 / real goal | `INCONCLUSIVE` |
| V4 | `NOT_ASSESSED` |
| ODB | `NOT_VERIFIED` |
| Numerical fixture | Separately reports provenance/numerical/goal checks |
| Execution / HIL | `execution_authorized=False`, `NOT_ESTABLISHED` |

## Actual focused evidence

All tests use new deterministic synthetic files and isolated test directories.
Core started no Owner, Solver, ODB tool or CLI session.

- `core-g3-first`: 49 passed / 2 failed. Two fault-injection tests attempted to
  monkeypatch a frozen ResearchProject instance; the fixture was changed to patch
  its class method, without relaxing the production frozen-object behavior.
- `core-g3-fixed`: 212 passed / 1 failed. The concurrent-observer test did not
  accept the existing store's `ProjectError` refusal alongside `ContractError`.
  Its allowed refusal types were aligned with the existing G2 concurrent-intent
  test; the assertion still requires exactly one committed effect.
- `core-g3-complete`: **223 passed / 0 failed / 0 skipped**, 28.14 seconds.
  This includes 61 new public-evidence tests and the unchanged 162-test rod
  regression selection. Three touched Core/test Python files pass Ruff.

The complete G3 regression, installed-package integration and independent review
are owned by Main and must be reported separately from this focused result.

## Remaining gates

Real dynamic Standard dispatch, protected Operator isolation, genuine Run/log/DAT
source authentication, real A, real A-derived B, V4 and ODB remain unqualified or
unmeasured. Matching offline schemas, Fake IPC success and valid synthetic
numerics cannot substitute for those gates. No real B Plan is created here.
