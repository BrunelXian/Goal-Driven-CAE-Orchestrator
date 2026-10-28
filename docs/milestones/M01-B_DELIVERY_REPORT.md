# M01-B — Real AF Read Compatibility delivery

Date: 2026-10-28. Result: **PASS — AF_READ_COMPATIBILITY_VERIFIED**, limited to
the audited AF revision, seven read methods, and newly created Fake/TEST_ONLY
instances described below. This is real authenticated loopback IPC evidence,
not a replacement of live acceptance by mocks.

The separate M01-A status remains **SYNTHETIC_CONTRACT_PASS**. Neither status
qualifies Abaqus, Standard, CAE/noGUI, ODB, production Projects, scientific
validation, same-user OS isolation, or automatic Codex continuation.

## G0 — baseline, source audit and startup manifest

The complete M01-B instruction, applicable global and Dev AGENTS, Python registry,
M01-A delivery, ADR-003/004, current authority register, bridge contract, current
adapter/DTOs and safety tests were read. Narrow AF source review covered product
creation, lifecycle/owner host, discovery, authenticated client/Supervisor, retained
process references, Fake backend/validation, read-only Store, and the existing
`supervisor_helpers.py`, `run003_process.py`, `execution_helpers.py` test harness.
No AF tests were edited or run as a broad suite. No Stable or model inspection
was performed.

| Item | Verified state |
| --- | --- |
| GD-CAE | `main@af3cfd90821cddf65ef93827a20fc2b26d98f0fc`; clean at entry |
| Delta from old M01-A reference | Existing commit `af3cfd9` includes DOC-001 and M01-A files; this session did not create that commit |
| AF Develop | `Develop@7f4b8d8f3a2c862ed8b244d495295f5d51ea0d88`; tracked state clean before/after |
| AF package | `0.3.0.dev0`, read directly from the explicit Develop source checkout |
| Python | `D:\XianLab\envs\LangChainEnv\Scripts\python.exe`; CPython 3.12.10, Windows x64 |
| Existing tooling | pytest 9.1.0; standalone Ruff 0.12.0 at `D:\ProgramData\anaconda3\Scripts\ruff.exe` |
| G0 baseline rerun | **138 passed in 0.41s**; repo-wide Ruff passed |
| Dependency/environment changes | None; process-local PYTHONPATH only |

The prior M01-A proposed directory was inside this repository and therefore did
not meet M01-B's stronger outside-repository condition. The approved TEMP fallback
was used. The exact retained root is represented without user-private components:

`%TEMP%\gdcae-m01b-85ae90a8782d43b69caa4dfa695ca0a5`

It was a nonexistent direct child of the current user's TEMP. Before creation,
all existing ancestors were checked for symlinks/reparse attributes and targeted
repository/Project markers; lexical/resolved parent equality was checked. The new
directory was created exclusively and confirmed empty. No directory was adopted,
copied from a historical run, deleted, or selected through Recent.

`prestart-manifest.json` was written before either owner start. Its limits were:

- G1: new `g1-product`, product TEST_ONLY/Fake; G2: separate new `g2-fixture`, fake-v1.
- Two owner-start calls total, one owner at a time, no restart.
- At most four owner-related OS processes total, allowing a Windows venv
  redirector plus Python host per owner. The test runner is separate.
- Total cooperative wall budget 300 seconds; G2 setup budget 120 seconds;
  bounded startup and cleanup waits. Actual G1+G2 elapsed time: **16.640 seconds**.
- G1 cleanup: official idle-stop API plus retained OS handle exit evidence.
  G2 cleanup: existing harness with original identity-bound handles.
- Unconfirmed G1 startup/exit prevents G2; no generic PID/name kill or takeover.

The real AF runtime/host preflight passed. The source's outer Windows Job hierarchy
remains explicitly UNKNOWN; no sandbox or descendant-management guarantee is
inferred from the host observation.

## G1 — product creation, empty reads and orderly stop

`create_project` created an empty product Project with DPAPI-protected local
credentials and initial PAUSED policy. Pre-start Plan/Grant/Run/Receipt/Validation
counts were zero. There was no owner metadata, process-fixture configuration or
Standard extension. `ServiceLifecycleManager.start(wait_seconds=10)` was called
once and returned a newly connected owner. Its creation chain was matched to the
recorded transport PID; actual host identity was bound to retained Windows handles.

| Identity | Value |
| --- | --- |
| Project | `p_29c8275f817b48459b7f4e6f1abae9e1` |
| Instance | `pi_e1bfd5897d79459f9b66e26ab73b1c52` |
| Owner | `owner_832a6804b61b41efb28b2ad3f5f92f18` |
| Health | backend `fake-v1`, simulation true, execution_scope TEST_ONLY, only Fake backend configured |

Through the unmodified bridge and real `discover`, capabilities, empty Run page,
and empty events succeeded. Missing Run/Receipt/Validation/Diagnostic queries
returned NOT_FOUND. Wrong instance and stale expected owner returned typed identity
failures without fallback. Read instrumentation observed **15 actual RPCs**, all
from the seven read-operation names.

The measured read interval began after owner acquisition and ended before stop.
All 16 measured logical tables, counts, event sequence, gate/slot and revisions
were identical before/after. Plan/Grant/Run/Receipt/Validation counts stayed zero;
event sequence stayed 0; PAUSED gate version stayed 2. Initial creation, owner
acquisition and orderly stop are authorized setup/lifecycle writes and are not
misreported as pure reads.

The official `stop(owner_id=..., operation_key='m01b-g1-stop-once')` committed the
idle stop. One ready record and one stopped record exist. `inspect` confirmed
NOT_RUNNING, separately from the stronger retained-handle exit evidence below.
Subsequent bridge discovery returned PROCESS_IDENTITY_UNKNOWN. That error alone
is not used as proof of process exit.

## G2 — seeded Fake evidence and seven live reads

The existing trusted `ProcessHarness(..., fake_jobs=70)` prepared **70 fake-v1
Plans and 70 TEST_ONLY Grants** in its own new fixture Store, then handed ownership
to one Fake Supervisor. No ProcessFixture or Standard configuration was supplied.
Its existing child harness enabled launch/legacy/path traps. The setup client
submitted each synthetic request once and waited for terminal Fake completion.

Fake execution emits bounded JSON and automatically records simulation validation.
It produced 70 Runs, 70 Receipts, 280 Events, 70 Observations and 70 Validations.
There were **zero explicit validate_run calls, zero management-grant issuance and
zero management receipts**. No extra validation authority or secondary writer was
needed. All Runs were FINISHED at revision 4 and the slot was empty before read
measurement. These writes are fixture preparation, not EvidenceBridge operations.

| Identity | Value |
| --- | --- |
| Project | `p_106001ba778d460f8c42d3a66be9bc77` |
| Instance | `pi_936f416ec4a3425593fa291a4304fe2c` |
| Owner | `owner_a27aca30f2474464ad3bd2f86db94cbb` |
| Configured execution | TEST_ONLY / fake-v1; simulation true; process_fixture_enabled false |

| Bridge method | Actual live result |
| --- | --- |
| capabilities | Seven read operations; execution_authorized false even though native health also advertises writes |
| list_runs | 70 unique Runs in **32 / 32 / 6** pages; native page timestamps and non-atomic declaration retained |
| get_run | Selected Run ID, revision, execution, backend, simulation and Plan digest matched fixture-side values |
| get_receipt | request_id matched original submission; setup independently confirmed original key and private namespace; neither private namespace nor key was exported |
| list_events | **280 unique events** traversed; a last-Run filter on the first 64 source events produced an empty visible page with cursor **64** and more_possible true |
| get_validations | One existing simulation record for the selected Run; validation_id and recorded verdict matched source |
| get_diagnostic | Recorded Run/validation summary; correct Run identity; digest_verified false; no current-artifact/liveness claim |

All successful selected reads were COMPLETE for their required projection scope.
Unknown optional fields from native summary pages were not fabricated. A second
independently constructed EvidenceBridge returned the same Run data/source. Each
public method also creates a fresh real discovery/client connection internally.

The measured G2 interval observed **36 actual read RPCs**. The interceptor allowed
only health/project_view/run/receipt/events/validations/diagnose and forwarded each
call to the original authenticated client; it did not replace response data.
Process-launch traps were active in the bridge caller during that interval.

The trusted TEST oracle used AF's existing read-only Store, an explicit context,
and one transaction per snapshot. It recorded counts plus ordered-row SHA-256
digests, all Run revisions, event high-water mark and gate/slot. Before/after
comparison was equal for all 16 tables:

`plans, grants, runs, receipts, events, validations, observations, consumption,
management_grants, management_receipts, control_events, dispatch_gate, slot, meta,
configuration, reconciliations`.

Run/Grant/Receipt/Validation counts stayed 70; Events stayed 280; all 70 revisions
stayed 4; the gate stayed OPEN/version 2 and the slot remained empty. No active WAL
byte-hash inference was used. The fixture uses AF's existing DELETE journal mode.
The production bridge never imports this oracle or opens the Store directly.

Wrong Project and stale expected owner failed closed. Original-key absence yielded
NOT_FOUND without submit/retry/new acceptance. Run limit 33 and event limit 65 were
rejected. Separately from read measurement, the test modified only its own private
handoff to verify AUTHENTICATION_FAILED, then restored it. After proven shutdown,
its own manifest was temporarily changed to version 999 and restored, producing
UNSUPPORTED_FORMAT; a newly created isolated legacy marker yielded LEGACY_PROJECT.
No production credential or manifest was touched.

## Process exit and retained artifacts

| Stage/process | PID | Creation time, 100 ns | Exit evidence | Exit code |
| --- | --- | --- | --- | --- |
| G1 Python owner | 25052 | 134375970355149482 | Identity-matched retained Windows handle | 0 |
| G1 venv transport | 13116 | 134375970354883554 | Retained handle for the creation-chain transport | 0 |
| G2 Python owner | 35124 | 134375970390047047 | Identity-matched retained Windows handle; harness handle signaled | 0 |
| G2 venv transport | 34004 | Held by original Popen object | Original Popen wait/poll completed | 0 |

Exactly two owner starts occurred, serially. G1 used the official idle-stop API;
G2 used its original harness stop file and close procedure. G2's documented
owned-handle termination fallback was **not used**. No PID/name kill, unknown-owner
restart, takeover or retained live owner was observed.

G2's child audit recorded all_confined=true, all_data_accesses_confined=true,
launch_and_legacy_traps=true, fixed_process_launch_whitelist=false. Its harness
confirmed the synthetic Recent sentinel unchanged and credentials absent from
remaining files after removing its bootstrap/process configuration. The temporary
connection file was also removed; it was briefly recreated only to test offline
discovery after verified exit and then removed again.

G1's encrypted lifecycle/operator/connection material remains inside the created
protected private directory, each using windows-user-dpapi-v1. It was not exported
or decrypted into this report. The owner is stopped. Retention preserves the test
record; these resources must not be silently reused as a later Project. No broad
directory cleanup was performed. The entire new test root contained **zero .inp,
.cae, .odb or .jnl files**.

Retained evidence beneath the redacted root above:

| Relative file | SHA-256 |
| --- | --- |
| prestart-manifest.json | `D3A47207D428B04C6197D923D4D159A7E315AD557332852E9D67F175088CC783` |
| evidence.json | `E1598EC540E8A4D2AC4CCB634339A85D0A316B7AB06E716637D790F1C13CEAF8` |
| g2-fixture/lifecycle.json | `A5FF4F7EC98DF1E98B0899073806DC6E3E5F5BAAAAEA1F39E58528454677A7FC` |
| g2-fixture/inventory.json | `7C71D44937F534A558CBA41781F8D6336CA221C1D460839281DA1DA44575B26F` |
| g2-fixture/process_0/io.json | `E092B476842010B7201991A6C5D7D6C0AC089C6E41D342F267D602551F9872B0` |

The summarized evidence file contains no raw credentials or user-private root.
Private local lifecycle/path records remain local; their contents are not copied
into tracked documents. Hashes identify retained files, not signatures or physical
verification.

## B-01–B-12 acceptance

| ID | Result | Evidence and scope |
| --- | --- | --- |
| B-01 | PASS | Two brand-new isolated TEMP child instances; explicit roots; no Recent/production selection |
| B-02 | PASS | Actual discover, loopback authentication, context/owner binding, creation-chain and retained OS identities |
| B-03 | PASS | Both read intervals preserve all 16 logical table snapshots, counts, revisions and event sequence; setup/stop writes separately identified |
| B-04 | PASS | Native health checked Fake/TEST_ONLY; bridge publishes only read capability and false execution permission |
| B-05 | PASS | All seven methods exercised successfully over real IPC with nonempty G2 records; empty/missing behavior in G1 |
| B-06 | PASS | Empty Run/events and typed missing records; nonempty pages; scope-based completeness and explicit non-atomic semantics |
| B-07 | PASS | Original receipt key/namespace verified privately, request_id preserved, 70 Runs and 280 events paged; raw cursor 64 on filtered-empty page |
| B-08 | PASS, live + regression | Actual credentials, private root, namespace and Grant values absent from serialized bridge outputs; native nested provenance filtered. Adversarial arbitrary nested injection remains covered by M01-A unit tests, not falsely claimed as modified live Store content |
| B-09 | PASS | Wrong instance/Project/owner, bad credential, stopped owner, unsupported version and legacy fixture fail closed; no fallback/restart |
| B-10 | PASS | Two owned Fake owner starts; four owner-related OS processes accounted for; all exited 0; no termination fallback |
| B-11 | PASS within test boundary | G1 zero engineering Plans/Grants/Runs; G2 only Fake emitter, child launch/legacy traps, explicit confined data access, no engineering artifacts or real backend configuration |
| B-12 | PASS | M01-A 138 tests rerun; live integration passed; final default regression 138 pass/1 intentional live opt-in skip; Ruff/diff checks pass; protected files unchanged |

No credentials leaked and no unexpected bridge-attributable state mutation was
detected. If either had occurred it would have been a security blocker. The proof
is of this read facade and these observed test paths; **same-user OS isolation is
not established**.

## Commands and actual outputs

The live test was run alone so the old package-import-side-effect test remains an
independent cold-import check. No dependency installation or global environment
change was used.

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
$env:PYTHONPATH='D:\Projects\Goal-Driven-CAE-Orchestrator\src'
$env:GDCAE_M01B_LIVE='APPROVED_TEST_ONLY'
$env:GDCAE_AF_SOURCE='D:\Projects\abqjobpilot_dev'
$env:GDCAE_M01B_ROOT=Join-Path $env:TEMP 'gdcae-m01b-85ae90a8782d43b69caa4dfa695ca0a5'
& 'D:\XianLab\envs\LangChainEnv\Scripts\python.exe' -B -m pytest -q -s --tb=short -p no:cacheprovider tests/integration/test_af_read_live.py
```

Actual output: **1 passed in 16.70s**, with G1=PASS, G2=PASS and
AF_READ_COMPATIBILITY_VERIFIED. No live attempt failed, no source compatibility
patch was needed, and no startup was retried. Collection and Ruff had passed
before this invocation. The recorded root now exists and is deliberately rejected
by reruns; a future authorized rerun must choose a new unique TEMP child.

In a separate shell without the live opt-in variables, final regression used
process-local PYTHONPATH, `-B -m pytest -q -p no:cacheprovider`, and a unique
repository-local `.pytest_cache/m01b-final-<uuid>` basetemp. Actual result:
**138 passed, 1 skipped in 0.46s**. The one skip is the explicit live startup gate;
that same integration test was independently run and passed above. No M01-A
safety test was skipped or weakened. `ruff check --no-cache .` returned
**All checks passed!**; `git diff --check` returned exit 0. CI was not invoked.

## Source changes and preservation

Only two files are new in this stage, untracked and unstaged:

- `tests/integration/test_af_read_live.py`: opt-in, reproducible G0/G1/G2 test,
  trusted setup separated from read measurement, sanitized evidence and cleanup.
- `docs/milestones/M01-B_DELIVERY_REPORT.md`: this report.

No production source, existing test, ADR, policy, dependency declaration or old
report was changed. No discovered bridge defect required a fix. No commit, push,
PR or CI trigger occurred. GD-CAE HEAD remains `af3cfd9`; AF Develop remains at
the reference revision with no tracked diff. Its historical untracked tree was
not enumerated. Stable was not inspected or modified.

Before/after byte hashes:

| File | SHA-256, unchanged |
| --- | --- |
| README.md | `EBE31922B1AC9914880DFCF4E2D99CAA36AEBB322300F74606D4A5171B8661CE` |
| .gitignore | `F39FFDAE60D369912E56F6BF3B29B93464BA960A34D00C37BBCEE25D57769058` |
| adapter af_evidence.py | `8B7A1CDD57DD0D4A067BC32037AC8893AA1662348F9D94BAEC01B34E670A88B0` |
| contracts af_evidence.py | `401ECB551591376F854247B7E64CC4D13F82CD54C17C098BDBA2B26943D5F012` |

The working tree was clean at entry, so its unchanged tracked state also confirms
preservation of ADR-003/004, historical ADRs and baselines. Both local asset areas
remain ignored by root-anchored rules and have zero tracked entries. No model
content was read. Kickoff material was read as instructed but not edited.

## Remaining risks and M01-C proposal

1. Qualification is revision-specific and Fake-only. Standard/real Solver/ODB
   response compatibility and scientific correctness remain unverified.
2. Ordinary AF credentials still possess capabilities beyond this facade. Neither
   AST checks, a test interceptor, a Skill nor the wrapper establishes same-user
   OS isolation or a server-enforced read-only credential.
3. Native validation reads remain unpaged; large histories can be rejected by the
   bridge's bounds. Multi-call reads are not atomic; stale owner binding requires
   explicit reviewed handling, not automatic rebinding.
4. COMPLETE covers required read projection, not complete scientific provenance.
   Optional fields may be unknown; diagnostic digests remain explicitly unverified.
5. Test evidence and the stopped product's DPAPI-protected test credentials remain
   in the new TEMP root for review. They must not be reused or published wholesale.
6. The test has cooperative time budgets and bounded waits, not a generic watchdog
   allowed to kill unknown processes. Unknown startup/cleanup must stop qualification.

Proposed M01-C, requiring separate review: a schema-constrained MCP read wrapper
for these seven methods plus a Codex Skill documenting explicit Project binding,
source/read/verification distinctions, budgets and stop conditions. Preserve
default-deny tools, field minimization, immutable expected identities, no generic
RPC/submit/Grant/lifecycle/recovery access, and protocol-level negative tests.
Re-use native Codex agents instead of creating another agent harness. Review any
server process/configuration or dependency requirements separately. No MCP,
Skill, role configuration, SDK/app-server, Event Bridge, M02 or later feature has
been implemented. Work stops here for the next review.
