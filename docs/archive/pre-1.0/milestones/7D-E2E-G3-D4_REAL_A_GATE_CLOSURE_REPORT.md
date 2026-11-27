# G3-D4 real-A gate closure and Codex-native activation

**Overall: PARTIAL. REAL_A_NOT_READY.** D4 delivered executable offline code and
integration tests; it did not authorize or execute Abaqus, ODB, a real Grant,
Standard Owner, protected deployment, external Runner, commit, push or publication.

## Entry and preservation

GD main HEAD `69b144cea9aecc515e15cc830368972b09258af9` and AF Develop HEAD
`7f4b8d8f3a2c862ed8b244d495295f5d51ea0d88` matched the mandate. Both indexes were
empty. Entry dirty counts: GD 6 tracked / 44 untracked, AF 4 / 59620. The new D4
private root froze 368 scoped source hashes and ten historical G3 report hashes.
D3 report/readiness/Operator documents matched their accepted digests before
their safe status projection. Historical BLOCKED/UNKNOWN and NOT_RUN remain intact.
No old Owner, native Job or historical process identity was queried.

Final status: GD 9 tracked dirty / 60 untracked; AF 11 tracked dirty / 59622
untracked. Both branches and HEADs remain unchanged and both indexes are empty.
These totals include prior work, not only D4. D4 itself touched 24 GD files
(8 existing + 16 new) and 11 AF files (9 existing + 2 new), listed below.
Final checks found zero historical digest mismatches, zero non-document source
drift since the reviewed freeze, and zero tested privacy-pattern matches. Pattern
scanning is a bounded check, not proof that arbitrary sensitive text cannot exist.

Three native engineering workers had non-overlapping write ownership (AF, Core,
Product); Main implemented HIL and integration. A separate read-only Reviewer
reviewed source and evidence. A usage-limit interruption stopped three agents;
after the user's continuation, AF and Reviewer resumed and Main reran the saved
Core implementation. No interrupted result was assumed to pass.

## Concrete P0 implementation

**AF original trusted execution chain.** `RodProduct.prepare_real` now prepares
the separately versioned dynamic rod Plan through `rod_trusted.prepare` and the
existing Plan transaction. `ExecutionService.submit` uses original Standard Plan/
Grant validation, accepted Receipt and one-use consumption. The existing
`ProductStandardControl.dispatch_once` leads to original claim/START_INTENT,
`StandardBackend.execute`, ManagedScope, collection and result persistence.
Recovery/interruption/closeout recognize the dynamic backend through the same
existing predicates. No second Owner, new execution database schema or generic
shell API was added. Configured profile and the existing exact authority predicates
remain required; preparation does not permit dispatch. OS protection remains
unqualified. Fixed Standard remains a separate profile.

The new route binds candidate bytes, actual Project/Instance, backend/version,
resources, engineering/scratch/output, deadline and nonce. Engineering inside AF
Project metadata is rejected, as are changed immutable policies even with a fresh
hash. ACK loss replays the original Receipt; UNKNOWN retains the slot and pauses.
Real B Plans are not pre-issued.

**Actual acquisition mechanism and independent checker.** AF now obtains the
original persisted Plan, accepted Receipt, Run, ordered events, unique Validation,
input and collector-bound DAT from its public read facade. It checks bounded input,
request namespace/key/job, Run Project, artifact identity and original completion
records. GD independently parses DAT and rechecks identities, causal ordering,
units/selectors, U1/S11/RF1 and frozen Decimal tolerances. It persists the original
evidence projection plus independently reproducible numerical checks. It does not
use AF parser PASS as authority. All fixture-derived source authentication remains
NOT_VERIFIED and real-goal status INCONCLUSIVE.

**New real-intent frozen Project.** A new schema-1 ContractBundle and additive
`rod-real-workflow-v1` event discriminator reuse ResearchProject transactions,
revisions, audit and budget counter rules. Existing synthetic schemas are not
relabelled or migrated. Actual verifier/compiler/parser source bytes and explicit
numeric policy are frozen. Source/policy drift blocks reopen/admission; deployment
must retain the matching implementation version. A fresh isolated Project was
created through the API at revision 3, with A=1 N, the [0.019,0.021] mm goal, no B,
no Plan/Grant and no execution permission. The model remains DECLARED_EXTERNAL.
An ordinary separate Python tool invocation reopened it read-only at revision 3;
database bytes were unchanged, only A existed, and budget remained limit 2 / held 0 /
charged 0 / available 2. This was not a child-process/Job lifecycle experiment.

Reservation/intent/UNKNOWN/observation events are atomic and idempotent; max two
calls is frozen and UNKNOWN never refunds its reservation. **Successful real B
admission is still unimplemented**: `PROPOSE_B` rejects until authenticated real-A
qualification exists. Negative ordering/budget protection is not a completed A→B
experiment, nor proof of two actual authorized executions.

**Protected Operator candidate.** New preview and read-only audit code specifies
three distinct research/human-reviewer/issuer roles, original AF issuer runtime,
protected layout, exact tuple, expiry/nonce, revoke and rollback. No new Windows
service or account/ACL change was performed. A fresh non-secret canary's actual
AccessCheck observation found a non-elevated but administrator/linked-admin-risk
current token with all tested rights on its own files. No capability bytes were
read and canary bytes were unchanged. This does not establish cross-principal
isolation. Fixed protected-path inspection is prepared but NOT_RUN; inaccessible
paths are NOT_OBSERVED_ACCESS_DENIED rather than falsely absent. HIL stays BLOCKED.

## Product and native activation

Wheel version is `0.0.0+g3d4`, Plugin `0.1.0-alpha.3`. Strict runtime/resource/role
contracts, optional-dependency doctor, unchanged seven read tools and explicit
`init-real-research` now form the package closure. The init route creates a new
real-intent frozen Project, never a Plan or Grant. File-only extracted-wheel tests
remove cached package imports and source-checkout paths, load actual package code
from the layout, verify RECORD, initialize a fresh directory and reject tampering.
The distribution/installation metadata is an explicit fixture: no pip/venv install
or clean-machine claim is made. GitHub release-ref install and Desktop are NOT_TESTED.

Main actually invoked native `gdcae-cae`, `gdcae-results`, `gdcae-inverse` and
`gdcae-reviewer` with fresh-Project bounded handoffs. CAE retained A within bounds,
Results required original evidence, Inverse refused B without accepted A, and
Reviewer retained all source/HIL/host limits. These were professional role calls,
not default agents substituted for them. The native Reviewer had only supplied
handoffs; separate source review inspected files. Neither is physical authority.

## Actual testing and limits

Interpreter: `D:/XianLab/envs/LangChainEnv/Scripts/python.exe`, 3.12.10; pytest
9.1.0, MCP 2.3.0, pywin32 312. No dependency/shared environment changes. The D4
in-process wrapper reuses P1/D3 private FD output capture, denies native launches
and socket connect/bind, and records exact private node inventories. It is a test
guard, not an OS sandbox. All tests use isolated synthetic inputs.

| Selection | Actual result |
|---|---|
| New privacy gate | 34 passed, 2 process tests deselected |
| First corrected Project/HIL | 39 passed |
| Product/HIL/Project | 56 passed |
| Real verifier + architecture | 60 passed |
| Resumed Core/Verifier/cross-repo/HIL | 87 passed |
| Resumed AF first fixes | 28 passed |
| AF final partition (35 D4 cases, two safe legacy nodes and prior rod tests) | 236 passed, 1 process test deselected, zero guard hits |
| Full applicable GD pure partition | 1300 passed, 157 deselected, 0 failed/skipped/errors; 975.08 s; zero guard hits |
| Final AF whitespace-only change | 37 passed (35 D4 + two legacy nodes), zero guard hits |

Selections overlap and must not be summed as unique coverage. The broad GD selection
covered 54 test files; four complete live/STDIO files and 70 function references
were excluded before parametrized collection (157 deselected cases). Exact selection
and collected node inventories remain in the private evidence directory. This is
the full applicable pure partition, not every historical test or live acceptance. Full old AF Standard
suites were not run: some fixtures invoke the real issuer or native process paths.
Legacy coverage includes `test_real_requires_separate_grant_and_opt_in`,
`test_synthetic_cp936_sample_and_malformed_data`, and the new
`test_fixed_managed_worker_retains_original_result_policy`. The latter and dynamic
positive tests use TEST_ONLY stored Grants, substituted authority/config predicates
and a synthetic runner, with real issuance/launch trapped. They test original
transactions and policy branches, not genuine real authorization/containment.

New examples are traceable in exact test collections and these node families:

- AF `test_exact_prepare_replay_without_grant_or_run`,
  `test_original_accept_receipt_lost_response_replays_no_second_run`,
  `test_worker_unknown_keeps_slot_and_pauses_without_retry`,
  `test_engineering_cannot_be_inside_original_execution_project`,
  `test_acquisition_rejects_inconsistent_original_record_projection`.
- GD `test_actual_validator_bytes_and_explicit_tolerances_are_frozen`,
  `test_parser_source_drift_fails_read_and_admission_without_migration`,
  `test_concurrent_reservation_has_one_winner`,
  `test_fault_atomicity_and_lost_response_replay`,
  `test_unknown_holds_budget_and_blocks_b_and_new_a`.
- Cross-repo `test_actual_original_af_records_independent_gd_read_and_persistent_unknown`,
  `test_original_dat_pollution_stops_public_read_and_preserves_gd_revision`,
  `test_schema_pass_and_recomputed_hash_do_not_bypass_independent_numbers`.

Initial failures are retained: a Main HIL test syntax typo prevented collection
and safe projection; it was fixed before the 39-pass run. An incorrect legacy
filename caused AF selection exit 4 without tests. First AF run was 8 passed /
12 failed; fixes included checking ExecutionError.code rather than message regex,
complete synthetic RF rows, directory boundary and immutable policy checks. Initial
read-only ACL inspection failed on an unavailable pywin32 convenience method; the
buffer API was corrected and the same untouched canaries were queried successfully.
No failure created an unauthorized process, Grant, Solver run or privacy leak.

Full GD Ruff passed. AF retains historical style debt: baseline-diff, not a blanket
AF PASS, is required. One newly introduced E702 was split without semantic change;
the same isolated Ruff rules report 129 diagnostics on the selected D3 baseline
and 128 on current files, **zero introduced / one removed**. The two new AF files
are clean. Both repositories' diff checks passed. An initial baseline invocation
incorrectly assumed an AF pyproject.toml and exited 2; the final comparison used
identical explicit isolated defaults for both source sets.

## Candidate and independent review

New private root:
`%LOCALAPPDATA%/GDCAE-G3-D3-OFFLINE-20261030-A01/D4-20261031-A01`.
Its `candidate` directory contains newly built GD/AF snapshots, source archives,
two wheels and `external-bundle`; old D3 artifacts were not replaced.

| Manifest | SHA-256 |
|---|---|
| GD, 61 selected files | `5bed3249f2be1a81efc8901eaa557b133b07f35545dd951a1bf7906b74fc3e5d` |
| AF, 118 selected files | `762a96d64b6dc5e49f82a72c56c0d27b4e357f66f70e36a012717322c0e23371` |
| External BUNDLE.json | `ec81b296d753391ec13dbf0017f12d5f3ad7f8a4e2347b8adb0e711bc61ffde1` |

Reviewer independently matched all 179 selected files with current source and
archives; all eight snapshot artifacts, 171 wheel source entries and 175 non-RECORD
entries matched. Ten bundle files and Operator preview source bindings matched.
This qualifies file correspondence only. External execution is NOT_RUN_EXTERNALLY;
license/publication review remains unresolved and release_ref PENDING_RELEASE_REF.

Reviewer findings closed: AF Project-directory confinement; immutable policy
rehash rejection; actual implementation/policy freeze; inaccessible ACL path
classification. No remaining source authority bypass was found. Limits remain:
unqualified HIL/real source, simulated positive authorization, no successful B
route, implementation-version-pinned reopening, and AF/GD size limits that differ.
AF permits up to 1 MiB DAT / 512 events; GD currently accepts 16 KiB / 64 events.
Oversize output fails closed and needs explicit future compatibility qualification.

A final independent read-only closeout review compared the current reports with
safe test/static/reopen receipts and found no new blocking documentation defect.
It supported PARTIAL / REAL_A_NOT_READY and explicitly did not repeat the earlier
source/candidate review or run tests. Final-check and final-closeout safe receipts
retain source hashes, history comparison, Git status and test evidence digests;
these are consistency records, not tamper-proof security attestations.

## D4-01–D4-20

| Gate | Result | Evidence / limitation |
|---|---|---|
| 01 | PASS | Actual entry metadata, exact source hashes, no cleanup |
| 02 | PASS | Historical digests and old BLOCKED/UNKNOWN/NOT_RUN preserved |
| 03 | LIMITED PASS | Version separation; two pure legacy nodes + mocked managed-worker regression; real legacy execution unrun |
| 04 | PASS OFFLINE | Single CLOAD slot, immutable template, exact input/output checks |
| 05 | LIMITED PASS | Original owner transactions/receipt/worker/recovery integration; no real Owner started |
| 06 | PASS BOUNDARY | Missing/Fake/default-disabled authorization rejected; zero real Solver calls |
| 07 | LIMITED PASS | Original record/artifact acquisition mechanism and negative source checks; authenticity unqualified |
| 08 | LIMITED PASS | Independent frozen numerical parser; V2/V3 never upgraded from fixture |
| 09 | PARTIAL | New A freeze and B-before-A rejection; accepted real-A→B positive route absent |
| 10 | LIMITED PASS | Frozen cap2, idempotency/concurrency/UNKNOWN holds; two real attempts not demonstrated |
| 11 | LIMITED PASS | One typed three-principal deployment candidate; actual deployment BLOCKED |
| 12 | LIMITED PASS | Exact denial/expiry/forgery/replay checks and current-token ACL observation; cross-principal enforcement BLOCKED |
| 13 | LIMITED PASS | File-layout package loading/init + actual current native-role handoffs; installed activation unverified |
| 14 | NOT_TESTED | Prepared single disposable Desktop action; no global change |
| 15 | PASS BOUNDARY | Runner/clean install NOT_RUN; no push/publication |
| 16 | LIMITED PASS | GD 1300/157 partition, AF 236/1 and final 37; GD Ruff clean, AF zero introduced diagnostics; diff/privacy passed; live exclusions explicit |
| 17 | LIMITED PASS | Independent source and candidate review; not numerical or execution authority |
| 18 | PASS BOUNDARY | No fabricated executable request; exact gate sheet says NOT_READY |
| 19 | LIMITED PASS | New versioned private snapshot; exact source/hash inventory; heads/index/history preserved; no installation or publication |
| 20 | PASS | Three actions in exact-gates sheet; no secrets or thread IDs requested |

## D4 exact file scope

Modified GD: `src/aegiscae/research/project.py` (one new event router),
`tests/architecture/test_package_skeleton.py`, `plugins/gdcae/plugin.json`,
`plugins/gdcae/scripts/{candidate,gdcae}.py`,
`plugins/gdcae/skills/{research,setup}/SKILL.md`, `external_runner/package.py`.

New GD code/tests/resources: `src/aegiscae/research/rod_real_project.py`,
`rod_real_verify.py`; `tests/integration/g3_d4_offline_checks.py`,
`test_d4_cross_repo_offline.py`; `tests/unit/test_d4_{operator,product,real_project,real_verify}.py`;
`plugins/gdcae/references/runtime-contract.json`; `operator_deployment/{preview,audit}.py`.
New documents: this report, exact-gates and progress reports;
`docs/architecture/7D_G3_D4_OPERATOR_APPROVAL_ONE_PAGE.md` and
`7D_G3_D4_PRODUCT_ACTIVATION.md`.

Modified AF: `abqjobpilot/product_rod.py` and
`abqjobpilot/execution/{closeout,interruption,lifecycle,product_standard,recovery,service,standard_backend,standard_contract}.py`.
New AF: `abqjobpilot/execution/rod_trusted.py`, `tests/test_d4_rod_trusted.py`.
No Stable, production Project, real model or historical record was modified.

The next human decision is the protected Operator deployment scope, followed by
independent VM qualification and one official disposable Desktop activation.
None is real-A approval. See the exact-gates sheet for all missing fields and the
remaining authenticated-source/B software work. No F1 or installer expansion occurred.
