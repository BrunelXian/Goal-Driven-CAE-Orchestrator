# D7-R2F-E1 — Production Issuer Test Boundary Repair

Date: 2026-11-01. Scope: test isolation only; no production authorization semantics changed.

## Result

`D7_R2F_E1_TEST_BOUNDARY_PASS` applies only to the reviewed A whitelist and regression boundary. Original R2F remains `D7_R2F_BLOCKED`; this does not qualify Plugin activation, Owner lifecycle, or real execution.

## Root cause and repaired paths

The original product control fixture substituted process launch, native Job queries, host checks and `StandardConfig.verify`, but retained the production issuer. Its `c.approve` calls `ProductStandardControl.invoke(authorize)`, which imports and calls `standard_contract._issue`, inserts `REAL_FIXED_STANDARD`, and updates the Grant's product scope. A fake process backend does not make that Grant TEST_ONLY.

Additional reachable entry points are `ExecutionService.authorize_standard` → `issue_execution` → `_issue`, and `standard_sequence.issue_pair` → `_issue`. Captured import aliases reference the same function objects. The Store exposes SQLite connections, so direct INSERT/UPDATE (including the original test's Grant mutation) also requires a boundary. `FakeGrantFixture.issue_exact(**overrides)` previously allowed replacing its Grant kind/issuer before a raw INSERT.

The AF tests root now loads a fail-closed plugin before collection/fixtures. It accepts only two exact reviewed A files and a fresh explicit basetemp. It replaces the original production callable code objects in the test process, covering existing aliases, and rejects B/unreviewed selection before collection. No replacement is persisted in production source.

SQLite connections are confined to that fresh root (or memory). A one-use, thread-local construction permit rejects pre-captured original connect aliases and direct constructors. A narrow default-factory wrapper installs an authorizer before returning the connection. Raw Grant and management-Grant INSERT/UPDATE/DELETE, ATTACH and writable-schema access are denied. One validated `TEST_ONLY` / `FakeGrantFixture` INSERT is permitted by an explicit helper; its gate closes in `finally`, including error cases, and resets prepared-statement authorization. No production Grant substitute is relabeled after insertion.

This is an accidental-call regression boundary for reviewed code, not protection against malicious same-user Python, deliberate conftest bypass, native API bypass, or monkeypatch removal. Plugin autoload is disabled by the existing qualified runner. No general sandbox was added.

## Exact E1 changes

| Repository | File | Change |
|---|---|---|
| AF Develop | `tests/conftest.py` | Load boundary before collection |
| AF Develop | `tests/no_real_grants.py` | Exact A whitelist, callable/SQLite guards, bounded side-effect receipt |
| AF Develop | `tests/test_e1_issuer_boundary.py` | 19 boundary cases, including aliases, raw SQL, override, failure-close and scope refusals |
| AF Develop | `tests/execution_helpers.py` | Route FakeGrantFixture writes through explicit TEST_ONLY helper |
| AF Develop | `tests/test_product_standard_control.py` | Mark whole original module B; no authorization-test rewrite |
| GD | `tests/integration/d7r2f_e1_evidence_audit.py` | Read-only bounded preservation and reference audit; counts/digests only |
| GD | this report | Delivery and retained limitations |

A = `test_e1_issuer_boundary.py` plus the unchanged `test_d7r2f_owner_selection.py` (8 static/selector cases). B includes the entire original product control module; it was not executed. Other legacy files are unreviewed for this runner and denied by default; they are not implicitly approved because they have no marker. Broader regression requires a separate static whitelist review. Tests using other direct test-authority writers are likewise not silently allowed.

## Actual verification

Interpreter: `D:\XianLab\envs\LangChainEnv\Scripts\python.exe`, Python 3.12.10, pytest 9.1.0. Existing environment reused unchanged.

The existing GD `tests/integration/g3_d6_offline_checks.py` ran in AF Develop with the exact two A paths, private FD capture, P1 output projection, disabled plugin autoload, child/network denial and a new basetemp. Label: `af-e1-boundary-02`.

| Check | Actual result |
|---|---|
| Minimal A pytest | 27 passed, 0 failed, 0 skipped, 0 errors; exit 0 |
| Fresh root before | 0 DBs / 0 Grants |
| Fresh root after | 11 DBs with Grant tables; 2 TEST_ONLY Grants; 0 Runs |
| Production-type Grant increment | **0** |
| SQL refusals exercised | 10 |
| Native/network attempts | 0 |
| Ruff, new guard/tests/helper/selector and GD audit | PASS |
| B module Ruff | Existing 34 E701 + 43 E702, identical to HEAD; not reformatted |
| Git diff whitespace checks | PASS for changed tracked files; no staging/commit |

The first label `af-e1-boundary-01` is retained as FAIL_CLOSED, not PASS. Its hook attempted `set_authorizer` during CPython's `sqlite3.connect/handle` event, before the connection was usable. A memory-only diagnostic confirmed `ProgrammingError`. The run had 11 fixture setup errors and no final pytest count receipt; 11 empty SQLite files contained no Grant tables/rows. Its 15 progress dots are not promoted to a completed test result. The outer wrapper returned `BLOCKED_PRIVACY_PROJECTION` because final counters were not produced; no private log was emitted. The corrected wrapper was independently re-reviewed before the fresh second run. Logical/physical Windows path differences were observed during diagnosis but were not the confirmed root cause.

## Preservation and non-propagation

The exact original `af-d7r2f-selection-01-temp` tree was audited before/after via bounded file hashing and immutable read-only SQLite, without importing application services or copying credential contents. Both snapshots report:

- 32 execution DBs, 32 Plans, 27 REAL_FIXED_STANDARD Grants, 1 TEST_ONLY Grant, 19 Runs, 0 owner.json.
- 369 files, identical closure SHA-256: `bbf00777051fcbd497701b72a8146bad3446a545a053c84b3123a1914eda5592`.
- All 32 runtime bindings lack required production configuration fields.
- 925 bounded objects scanned in the exact D7-R1 source candidate, D7-R2 wheels/manifest/A-only preview, current GD/AF source and Plugin v1/v2 source; 0 incident-ID/path references. No unrelated historical Project or database scan.

Static production checks: `read_extension` and Owner bootstrap call `StandardConfig.verify`; normal service submission/dispatch also checks the configuration and exact Plan/runtime binding. The missing fixed backend fields fail those checks. Supplying another valid config does not match the frozen Plan, and preparation rejects existing Plans/Grants. Thus these unmodified fixture records cannot be validly reaccepted through the current supported production path. Old receipts can remain readable; Grants were not revoked, deleted or made physically inaccessible. Same-user tampering is outside this conclusion.

Evidence resides beneath the existing task-only LOCALAPPDATA directory `GDCAE-G3-D3-OFFLINE-20261030-A01/D6-20261031-A01/gdcae-m03f1p1-g2long-d6`: `af-e1-incident-before.safe.json`, `af-e1-incident-after.safe.json`, `af-e1-boundary-02.safe.json`, and `af-e1-boundary-02-temp/e1-boundary.safe.json`. Original logs, credentials and databases remain in place.

## Preserved R2F state and recovery boundary

GD main HEAD remains `a75a614f9738af8f257fd490ceec2df4c012ea19`; AF Develop HEAD remains `7f4b8d8f3a2c862ed8b244d495295f5d51ea0d88`; indexes remain empty. All pre-existing unrelated modifications are retained.

Before/after closure hashes are identical for GD production source (`f1d5bafea417c2288657c76cdd08ae03c6383d9bdf748dde258ad7385e5e11f2`), AF production source (`c870c4f07488443dcdd3742c29a55c861a9e3029bb2a4d49ca48bcdab24cd7a7`), Plugin v2 source (`9a608e791f2274cb7e615746f6147d21e0c6f4289a5f42a7b99af24a4c5a4696`) and Plugin v1 source (`d8fab1b199bf88b0f805069649741f6303aec08ad6058d774739abde13eb9519`). Hash algorithm: sorted relative path/content-SHA pairs, compact JSON; excludes bytecode/cache entries.

Plugin v2 implementation and Owner interpreter repair remain at their prior source state. No installed Plugin/Core/cache or shared environment was changed. No Owner, Solver, real Grant or external installation ran.

Independent Reviewer approved the initial exact whitelist, identified the corrected construction timing and failure-cleanup requirements, and reviewed the revised boundary before the passing run. Final independent receipt/source review is recorded below. Resuming D7-R2F scoped integration planning and separately reviewed offline validation is technically supported; Plugin installation, Owner lifecycle qualification and real execution still require their own explicit authorization. This turn stops here.

Final independent review: `FINAL_REVIEW_PASS_LIMITED`. Reviewer independently read the final guard, safe receipts and audit implementation, confirmed the counts/closures and found no WAL files in the exact incident tree (0), limiting the risk of immutable reads overlooking WAL content. Reviewer recommends `D7_R2F_E1_TEST_BOUNDARY_PASS` for this whitelist only; no whole-repository regression claim or new execution authorization.
