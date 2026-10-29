# M03-B — Real AbqJobPilot TEST_ONLY Workflow Integration

Date: 2026-10-28. **PASS — AF_TEST_ONLY_WORKFLOW_IPC_PASS**, restricted to the
authenticated Fake/TEST_ONLY integration described here. All B-01–B-20 checks below
are satisfied within that scope. Stop for architecture review; no M03-C work started.

| Dimension | Actual conclusion |
|---|---|
| Real AF Fake IPC A→B | PASS, two distinct accepted Fake Runs, complete recorded evidence |
| GD-CAE decision | Existing synthetic fixed A/B workflow, A miss then B match |
| Candidate/Plan inputs | PROVEN_BYTES_AT_CHECKS, separate identical-byte `.txt` copies |
| Safety/cleanup | PASS, retained-handle exits accounted for, no forced owner termination |
| M03-A qualification | M03A_SYNTHETIC_WORKFLOW_PASS preserved |
| ABAQUS_EXECUTION_VERIFIED | false |
| AF_PRODUCT_MULTI_PLAN_VERIFIED | false |
| PHYSICAL_VALIDATION_AVAILABLE | false |
| CODEX_AUTOMATIC_MAIN_CONTINUATION_VERIFIED | false |

Implementation and semantic limits: [M03 AF test workflow architecture](../architecture/M03_AF_TEST_WORKFLOW.md).
There is no new product executor, no schema migration, no MCP write operation and
no authenticated AF fact silently reclassified as a physical result.

## G0 and preserved workspace

Branch `main`, HEAD `6c549dc98c25a12dcb9c93baa4fbf8d629c80ec1`, index empty.
AbqJobPilot Develop HEAD `7f4b8d8f3a2c862ed8b244d495295f5d51ea0d88`, tracked clean
before and after. Stable was not inspected or changed. Source review covered the
taskbook, global environment rules, M03-A implementation/reports, research contracts,
store/mutation/budget, M01 Bridge, and the named AF client/discovery/service/planning/
models/backend/validation/test harness and supervisor/attachment tests. Native
Reviewer independently reviewed the safety seam and AF semantics.

Selected existing interpreter: `D:\XianLab\envs\LangChainEnv\Scripts\python.exe`,
Python 3.12.10, SQLite 3.49.1, pytest 9.1.0, mcp 2.3.0. Existing Ruff:
`D:\ProgramData\anaconda3\Scripts\ruff.exe`, 0.12.0. No installation/environment edits.
G0 no-owner workflow/architecture regression: **204 passed in 302.69s**.

The entry hash manifest contained 86 nonignored files. **All 86 remain byte-identical**,
including M03-A's four tracked changes and six new files, every product source,
README/.gitignore, ADRs, frozen baseline and the retained M01-C review patch.
Patch SHA-256 remains `52232088439a097ed814dfcd9005cc7d2e7d3af5e716bfe7e71ea7aebc764859`.
No staging, commit, push, PR or CI action occurred.

This milestone adds exactly six files:

1. `tests/integration/m03b_support.py` — exact TEST provisioner/port, immutable mapping/oracle, Bridge capture and independent semantic checks.
2. `tests/integration/m03b_child.py` — one bounded advancement in an independently identified Python child, with hard-exit seams.
3. `tests/integration/test_af_workflow_live.py` — 19 real IPC/fault/negative cases, explicit opt-in only.
4. `tests/architecture/test_af_workflow_test_boundary.py` — four offline privilege/surface guards, including controlled forbidden examples.
5. `docs/architecture/M03_AF_TEST_WORKFLOW.md`.
6. `docs/milestones/M03-B_DELIVERY_REPORT.md`.

Final Git state: the four inherited tracked M03-A modifications remain; 13 untracked
files comprise seven inherited files plus these six additions. Index remains empty.
All execution data lives outside the repository. Kickoff_Docs remains ignored and
unmodified; only authorized task instructions there were read. CAE models and local
Codex config remain ignored/untracked and their contents were not accessed.

## Actual positive cross-system mapping

Final evidence root, home path redacted:
`%TEMP%\gdcae-m03b-acceptance-79612e3929bf422093db901b4e5dc857`.
Positive case directory:
`test_b01_b09_real_ab_lost_reply_independent_reader_and_competing_main`.
Public mapping is in `public-result.json`; raw AF captures are `A-facts-*.json` and
`B-facts-*.json`. Provisioning/mapping/oracle/definition and per-step submit tickets
are retained there. Raw namespaces, connection tokens and Grant IDs are not copied
into this report. Source records are test-harness artifacts, not new product state.

AF Project `p_01269e75241b4e968a1987146aada7cf`, instance
`pi_9d2b390e2213490e82e330de2e695d3c`.

| Identity | A | B |
|---|---|---|
| Stable business key | `fake_eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee_A` | `fake_eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee_B` |
| Candidate | `candidate_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa` | `candidate_cccccccccccccccccccccccccccccccc` |
| AF Receipt request_id | `req_0d465292e87b4a21ac1deee759230631` | `req_b0b09e93993e4fc7a785b3ac663f968c` |
| AF Run | `r_673034414e5942fcb87bc473f1ff6e9a` | `r_67b84809215d4289a19ca8fd92e9b332` |
| AF Plan | `plan_f81f9426d6b94a2eb7a389b5263b6f1e` | `plan_6fff92c7342d42daa54c67b1dbb7be6e` |
| AF phase | `phase_ef052f90c49d4384b2bafbcdebb56cc3` | `phase_c36b961bbf4849a0bf56a4fdcf5fdb7a` |
| Oracle metric | 2 mm / target unmet | 0.5 mm / target met |

A Candidate/input SHA-256:
`49b77ce3adc1871b9e03140f97a8d0ff0b9b4579117ae49f85932176e62d0ecf`.
B Candidate/input SHA-256:
`1becc39ec77dc37eaf541578650f29d9bf78763c4e5d8ddb2f44fe174d82267b`.
A Plan SHA-256:
`828b848dfba9f7af6e420ae2da3399b456a6bb01acaa5ceeac5d12b69d554621`.
B Plan SHA-256:
`07727016745622bf318a051b87dfa8c642de4074ffbfddaaefb255af9a4b1ced`.

Global event sequence 1–4 belongs to A, 5–8 to B; each is REQUEST_ACCEPTED,
START_INTENT, FAKE_COMPLETED, VALIDATION_RECORDED in that order. Both original
validations are PASS under `fake-result-v1` / `fake-json-validator` v1, scope simulation.
Each phase, evidence reference and deterministic output digest is cross-checked.
No validation write API is called by the adapter.

A's submit reply was discarded after actual AF commit. Recovery queried the original
key and did not call the coordinator submit path again. A separate explicit test
replayed the same AF request to verify AF idempotency; it returned the original
Receipt and no new Run. Same key/different content returned IDEMPOTENCY_CONFLICT.
Two independent Python coordinators competed for B: one CLAIMED, the other
REVISION_CONFLICT. There were exactly two acceptance events and two workflow submit
tickets. B's ticket records one already committed A decision. A second independent
reader got the same original Receipt and did not change the AF event history.

Local accounting after B: held=0, charged=2, available=0. TEST grants and local
synthetic budget observations remain distinct. No third submission/Run occurred.

## Scientific and input qualification

Both Plans pin different supported `.txt` input bytes predicted by the existing
typed editor and independent diff guard. Actual workflow Candidate outputs match
these bytes before submission and after evidence retrieval. AF checks its own
manifest at acceptance and dispatch; validation binds the JSON to the same Plan
input digests. This is byte equivalence at the checked boundaries, not proof that
FakeBackend solved or numerically interpreted those inputs.

The frozen objective remains displacement <=1 mm with 0.01 mm tolerance and separate
hard limit 10 mm. The immutable `TEST_ORACLE` supplies 2 mm and 0.5 mm, bound to the
exact Candidate/step/Project/frozen selectors. AF JSON supplies no displacement.
V0/V1 are synthetic checks; AF artifact integrity is simulation evidence; V3 is
the synthetic oracle comparison. Real V2=NOT_RUN, V4=NOT_ASSESSED, real Goal remains
INCONCLUSIVE, physical_evidence_eligible=false. Frozen criteria/rules/budget do not
change in response to A.

## B-01–B-20 acceptance matrix

| ID | Result | Actual evidence |
|---|---|---|
| B-01 | PASS | Exact HEADs, 86-file hash manifest, global environment verification, 204-test G0, fresh TEMP/prelaunch manifest |
| B-02 | PASS | Real discover + authenticated IPC, exact owned endpoint, fake-v1/TEST_ONLY/simulation/open dispatch; no additional backend |
| B-03 | PASS | Trusted prepare creates exactly two independent fixed Plans/TEST grants/requests before any submit; archived provisioning |
| B-04 | PASS | Port verifies persisted CLAIM, exact request and intent-state reservation, then creates exclusive submit ticket before IPC |
| B-05 | PASS | Positive A original request_id/Run/phase/Plan/digest/namespace and normalized request digest checked |
| B-06 | PASS | Independent AF simulation validation plus frozen TEST_ORACLE A=2; objective miss and hard constraint pass |
| B-07 | PASS | B submit checks committed VALID_SYNTHETIC_TARGET_MISS; actual A events precede B; invalid/absent A evidence blocks |
| B-08 | PASS | Distinct B acceptance, oracle 0.5, unchanged criterion, INCONCLUSIVE real Goal |
| B-09 | PASS, bytes only | Both Plan manifest hashes equal actual Candidate output hashes before submit and after reads; output validation binding |
| B-10 | PASS | Actual accepted reply discarded; original-key query recovery; forced unknown holds quota and prevents B |
| B-11 | PASS | AF same-key replay/conflict, actual two-process CLAIM race, terminal replay, live budget exhaustion prevents B |
| B-12 | PASS | Nine real IPC hard-exit boundary cases plus lost/paused owner, unresolved START_INTENT, journal refusal; separate-process reopen |
| B-13 | PASS | Exact Project/instance/context/owner/Plan/phase/Run/namespace/key checks; 26 corrupted original-response paths; candidate/oracle/mapping tamper |
| B-14 | PASS | Actual AF invalid Fake JSON yields FINISHED/INVALID/FAIL and blocks B; absent validation/START_INTENT holds; missing decisive evidence BLOCKED |
| B-15 | PASS | All product/Bridge/MCP bytes unchanged, seven-read capture surface, no product fixture import or generic/write RPC in read wrapper |
| B-16 | PASS | No old file changed, no schema/contract/ADR migration; explicit fixture sidecars only |
| B-17 | PASS | All 37 Owner hosts and launchers across attempts exit 0, no forced fallback; all 23 new coordinator children have original-handle exit evidence |
| B-18 | PASS | fake-v1-only checks, AF child launch/default-path guards, no Standard/process fixture, no Abaqus/CAE/ODB call or production Project |
| B-19 | PASS | 19 live; 564 offline +21 expected skips; Ruff/diff checks; independent 45-test Reviewer run and no remaining blocker |
| B-20 | PASS | This report, exact identity mapping, architecture limitations, cleanup/retention risks and bounded M03-C proposal |

The 26 corruptions modify test-side copies of actual captured AF responses; they
are not claimed to be 26 independently corrupted AF databases. Separate tests use
real bad credentials/stale binding, real owner dispatch fault and a real invalid
Fake artifact in this invocation's owned directory. No historical data is changed.

## Actual tests, failures and verification commands

All pytest invocations use absolute existing Python, `-B`,
`PYTHONDONTWRITEBYTECODE=1`, `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, explicit repository
`src` on PYTHONPATH, `-p no:cacheprovider` and fresh `--basetemp` outside the repository.
Historic M01 live opt-ins stay unset. No entire AbqJobPilot suite is run.

```text
# G0, live opt-ins unset
python.exe -B -m pytest tests/unit/test_synthetic_workflow.py tests/architecture -q -p no:cacheprovider --basetemp <fresh TEMP>
204 passed in 302.69s (0:05:02)

# Final real IPC, GDCAE_M03B_LIVE=APPROVED_TEST_ONLY,
# GDCAE_AF_SOURCE=D:\Projects\abqjobpilot_dev, GDCAE_M03B_ROOT=<new exact TEMP child>
python.exe -B -m pytest tests/integration/test_af_workflow_live.py -x -q -p no:cacheprovider --basetemp <separate fresh TEMP>
19 passed in 184.23s (0:03:04)

# Full default no-owner regression, all live opt-ins unset
python.exe -B -m pytest -q -p no:cacheprovider --basetemp <fresh TEMP>
564 passed, 21 skipped in 455.51s (0:07:35)

# Independent Reviewer, no owner
python.exe -B -m pytest -q -p no:cacheprovider tests/architecture/test_af_workflow_test_boundary.py tests/architecture/test_research_boundary.py
45 passed in 0.31s

D:\ProgramData\anaconda3\Scripts\ruff.exe check --no-cache .
All checks passed!
```

`python.exe` above abbreviates only `D:\XianLab\envs\LangChainEnv\Scripts\python.exe`;
it was never resolved through PATH. Output excerpts preserve actual terminal summaries.
The 21 skips are the 19 M03-B cases explicitly run above and two existing M01-B/M01-C
live tests. They are not untested substitutions for real M03-B IPC.

Tracked `git diff --check` and explicit `git diff --no-index --check -- NUL <file>`
checks for all six additions have no remaining whitespace errors. The no-index
commands return 1 for added-file differences; this is not a test failure. One
initial trailing empty line was removed. Git emits existing LF→CRLF advisory
warnings; no old file was normalized or rewritten. Final Ruff remains clean.

Earlier real runs: smoke **1 passed/14 deselected in 14.58s**; initial faults
**15 passed in 158.29s**. Reviewer-driven diagnostic strengthening exposed two test
adapter compatibility mistakes: singular `facts.receipt` versus `receipts`, then
comparison of projected event payloads as full originals. Each produced one
BOUNDED_WAIT_FAILED (47.16s and 47.13s respectively), conservatively held A, and
created no B. Both Owners exited 0. The fixes use actual AF projected schemas,
minimum mandatory fields and recursive optional-null comparison. Retained raw data
from this milestone verified the corrected comparison without IPC; the final run
then used an entirely new root. No unknown launch was retried or owner replaced.

Independent Reviewer `/root/m03b_review` found and re-reviewed the diagnostic
completeness/contradiction checks, process ownership registry, enforced deadline and
owner-hash binding. Final source/architecture review reported no remaining blocker;
the Reviewer did not modify files or run an Owner. Product runtime does not delegate
to a new Agent framework.

The Reviewer also reviewed this completed report and supported the scoped PASS
using the final observed results. Its final wording correction distinguishes the
authorized Kickoff taskbook read from untouched model/config contents; that correction
is applied above. No remaining implementation blocker was reported.

## Process exit and retained materials

Only newly created roots were audited, never old M01 credentials. Prefixes below are
under `%TEMP%`; all suffixes uniquely identify this invocation's attempts.

| Root suffix | Owners | Coordinator children | Retained synthetic journals |
|---|---:|---:|---:|
| smoke-d2b7a9a8d5e1495c87960969ab726d99 | 1 | 2 | 0 |
| faults-3153ac9b17a040ab865c5f1a9a540a2e | 15 | 10 | 1 |
| final-b710dc504d1f4881b2ac759cc78fae18 | 1 | 0 | 0 |
| verified-af03e3a0339049f99ba758074ec3ee2d | 1 | 0 | 0 |
| acceptance-79612e3929bf422093db901b4e5dc857 | 19 | 11 | 1 |

Each full root begins `gdcae-m03b-`. Every `af/lifecycle.json` reports
exited=true, actual_process_handle_signaled=true, exit_code=0,
terminated_by_owned_handle=false. Positive final Owner host PID=22864,
launcher PID=17428, creation_time_100ns=134376715673730599; both exited normally.
Host image is the registered venv's Python312 base executable, matched to the expected
venv interpreter and parent before use. Coordinator `exit.json` records actual and
launcher exit codes; 73/74 are deliberate injected hard exits, not unclosed processes.

All newly generated private connection handoffs and harness bootstrap/process
credentials were removed by exact owned cleanup. All 37 AF inventory checks report
credential_absent_from_remaining_files=true. No cleanup-blocked marker exists.
Two deliberately retained synthetic journal sentinels remain; no journal deletion,
repair, refund or owner restart occurred. Raw AF metadata, TEST Grant identifiers,
test databases and failure evidence remain local in those roots. They are not
repository files and should not be published as scientific or production evidence.
Historical M01-B encrypted material was neither reused, read nor deleted.

## Residual risks and M03-C minimum proposal

| Risk / limit | Treatment |
|---|---|
| Cross-store commit gap | Durable research intent/claim and exclusive ticket; query-only recovery, no cross-DB atomicity claim |
| Accepted invalid/missing Fake evidence | Local budget remains held/UNKNOWN conservatively; no automatic administrative settlement |
| Same-user coordinated tampering / file races | Hashes and identity checks detect ordinary inconsistency only; no cryptographic trust or OS sandbox claim |
| Test sidecars required on reopen | Preserve exact mapping/oracle/endpoint; no production AF binding API or auto-discovery/recovery |
| Finite fixture deadlines/Grant expiration | Stop, never extend/reissue silently; new invocation needs fresh scope |
| Retained test DB/journals/raw metadata | Local retention documented; no unsanctioned broad cleanup |
| Real Standard multi-plan and physical validation | Unsupported and unverified; Fake success provides no such authorization |

M03-C proposal only: keep one fixed A→B research scope and the current TEST_ONLY
port. Let Codex Main obtain A's verified simulation facts and separate oracle result,
ask a native Evidence Analyst to explain the feedback, and propose a typed B scalar
within the already frozen range. An independent native Reviewer challenges identity,
hard constraints and missing physical evidence. Persist the proposed value, references
and review/decision before existing Mutation Guard and BudgetLedger admission.
Reject free-form code/patches, new entities, contract/rule changes, unknown A evidence,
insufficient budget and a third candidate. Test changed/invalid proposals and replay
across a new explicit Main turn. AF provisioning for any newly selected B still needs
an exact separately approved TEST Plan/Grant; this milestone does not grant dynamic
execution authority. Keep real Abaqus/ODB, automatic desktop-thread wakeup, SDK/app-server
continuation, general DAGs and writable MCP tools out of that minimum experiment.

Compatibility gate for that proposal: v1 already freezes B in WorkflowDefinition.
The smallest next experiment accepts Main's proposal only when it exactly matches
the existing preapproved B template; other values are review proposals without
execution. Truly selecting a different B after A needs an explicitly reviewed new
version/admission design, not silent mutation of a historical v1 definition.

**STOP: awaiting architecture review. No M03-C implementation, commit or push.**
