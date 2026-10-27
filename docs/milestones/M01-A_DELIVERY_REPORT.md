# M01-A delivery and review record

Date: 2026-10-28. Status: **PASS within the approved M01-A scope —
SYNTHETIC_CONTRACT_PASS**. Live status: **AF_READ_COMPATIBILITY_NOT_VERIFIED**.

This report records local governance migration, two production source modules,
and offline tests. It does not approve or claim Solver execution, ODB validation,
research-goal acceptance, recovery, or original Codex Main resumption. Work stops
for review; M01-B/C and later milestones have not begun.

## Pre-change baseline and preserved state

The M00-P audit was delivered in the original conversation, not a repository file.
The approved M01-A brief and relevant local kickoff material were read. Global
Python policy and the environment registry were consulted before Python work.

| Repository | Before and after |
| --- | --- |
| GD-CAE | `main`, `488e0a1597b703dc86ce36158836d1b7a7fa07ab` |
| AbqJobPilot Develop | `Develop`, `7f4b8d8f3a2c862ed8b244d495295f5d51ea0d88`; tracked status clean |

Before M01-A, GD-CAE had only DOC-001's unstaged `README.md` and `.gitignore`
changes. Neither was edited by M01-A. No index changes, commit, push, branch
operation, or CI trigger occurred. Develop was accessed only through narrow
source reads and tracked-only status; its historical untracked tree was not
enumerated. Stable and private model contents were not accessed.

The following SHA-256 values were recorded before changes and checked equal
after implementation:

| Protected file | SHA-256 |
| --- | --- |
| `README.md` | `EBE31922B1AC9914880DFCF4E2D99CAA36AEBB322300F74606D4A5171B8661CE` |
| `.gitignore` | `F39FFDAE60D369912E56F6BF3B29B93464BA960A34D00C37BBCEE25D57769058` |
| `docs/adr/ADR-001-runtime-first.md` | `23600E64D28E6FE857399CADD063EF0A35BD1928328D0DE8FE9D388B4C14B71C` |
| `docs/adr/ADR-002-legacy-selective-migration.md` | `7776428482BBC64FF79CBA8593773CD6FF6AA7DD670BF650F1FC52EB158BE5A9` |
| `docs/baseline/AegisCAE Runtime 项目计划书.md` | `9A89A5AD661A80A69EC159124066E5B34ED6DC74DE9295336F426B17079E7448` |
| `docs/baseline/BASELINE_REGISTER.md` | `9EC1426DC4ABD3F8C3ADD8CB8F036A65A67FB70653CA2C2188DBB987AFC1F6AA` |
| `docs/baseline/LEGACY_ABQJOBPILOT_SUMMARY.md` | `F938B243FF438C6E7587F9337BE4C4730E4BDDEED78A874A5BD4E0F2A1128DFB` |
| `docs/baseline/LEGACY_ABQPILOT_SUMMARY.md` | `D1685D26A208F15AD772335FCD927C0C22F31F0FE8901613D9A7B02AC9591A43` |
| `docs/baseline/LEGACY_MIGRATION_DECISIONS.md` | `D90E35737EE86A3AA77B67AFA5D6BECF4977A371F35517317615DB351E3603C2` |

`git check-ignore -v -- 'Kickoff_Docs/' 'CAE models/'` confirmed root-anchored
rules at `.gitignore:32` and `:33`. `git ls-files -- 'Kickoff_Docs' 'CAE models'`
returned no entries. Model contents were not enumerated. Existing root
architecture documents, package markers, dependency metadata, and baseline
documents have no M01-A diff. Test scratch data used unique directories beneath
the already ignored `.pytest_cache`; no cleanup or ignore-rule edit was performed.

## Architecture decision and invariant migration

[ADR-003](../adr/ADR-003-codex-native-delegated-execution.md) and
[ADR-004](../adr/ADR-004-execution-evidence-research-verification.md) are
**ACCEPTED for the approved architecture principles and M01-A scope only**.
Historical ADR-001/002 remain unchanged and apply outside the explicit conflicting
scope. Acceptance is neither an execution Grant nor deployment qualification.

Codex owns the agent harness; GD-CAE owns future research contracts and independent
verification; AF owns authorized Abaqus execution and its recorded facts. No new
agent framework, execution manager, ResearchProject store, or verifier was built.
V0 provenance, V1 model integrity, V2 Solver/numerical health, V3 goal acceptance,
and V4 physical validation remain distinct; the bridge creates no V0–V4
VerificationRecord. Reviewer opinions remain advisory.

The [current authority register](../architecture/CURRENT_AUTHORITY.md) maps all
11 stable invariants, including enforcement limits:

| Invariant | Current treatment |
| --- | --- |
| INV-EXEC-001 | Internal Unified Executor exclusivity superseded for Abaqus; GD process launch remains forbidden |
| INV-WORKSPACE-001 | Future research writes controlled by GD; AF owns its writes; this bridge has no writes |
| INV-SOURCE-001 | Retained: immutable sources and baselines |
| INV-LEGACY-001 | One exact public AF read seam exception; private AF and all abqpilot coupling prohibited |
| INV-ADAPTER-001 | Retained: no subprocess, uncontrolled writes, client exposure or raw forwarding |
| INV-LLM-001 | Retained: agents propose; cannot self-authorize or create authoritative verdicts |
| INV-VERDICT-001 | AF recorded execution facts separated from future deterministic GD research verdicts |
| INV-EVIDENCE-001 | Retained: reports are views |
| INV-FIXTURE-001 | Retained: fixtures are not physical evidence |
| INV-CWD-001 | Retained: explicit Project/root/instance; no Recent or CWD fallback |
| INV-FAILCLOSED-001 | Retained: unresolved identities, states and evidence cannot become success |

## Exact file changes

Nine new files and three existing test files constitute M01-A; the two DOC-001
files remain separate pre-existing changes. No files are staged.

| Action | File |
| --- | --- |
| New | `docs/adr/ADR-003-codex-native-delegated-execution.md` |
| New | `docs/adr/ADR-004-execution-evidence-research-verification.md` |
| New | `docs/architecture/CURRENT_AUTHORITY.md` |
| New | `docs/architecture/M01_EVIDENCE_BRIDGE.md` |
| New | `docs/milestones/M01-A_DELIVERY_REPORT.md` |
| New | `src/aegiscae/contracts/af_evidence.py` |
| New | `src/aegiscae/adapters/abaqus/af_evidence.py` |
| New | `tests/architecture/test_af_read_boundary.py` |
| New | `tests/unit/test_af_evidence.py` |
| Modified | `tests/architecture/test_package_skeleton.py` |
| Modified | `tests/architecture/test_forbidden_legacy_dependencies.py` |
| Modified | `tests/architecture/test_forbidden_surfaces.py` |

The three existing test diffs are respectively +22/-9, +75/-2, and +4/-1 lines.
The legacy dependency guard's tuple traversal omission was repaired with negative
cases in that already impacted file. No safety test was removed or marked xfail.
The package remains `aegiscae==0.0.0`, with unchanged dependency metadata.

## Bridge and DTO delivery

The complete field, limit, error and consistency contract is in
[M01_EVIDENCE_BRIDGE](../architecture/M01_EVIDENCE_BRIDGE.md).

| Public method | Fixed AF source | Bound/meaning |
| --- | --- | --- |
| capabilities(binding) | discovery's authenticated health | Read-method intersection; execution_authorized always false |
| list_runs(binding, cursor=None, limit=32) | project_view | Descending keyset; per-page source read time; missing continuation field is malformed |
| get_run(binding, run_id) | run | Identity, status and bounded backend/Plan provenance |
| get_receipt(binding, key) | receipt | Original key; request_id retained; key and private namespace omitted |
| list_events(binding, cursor=None, limit=64, run_id=None) | events | Project-wide raw high-water mark before Run filtering |
| get_validations(binding, run_id) | validations | At most 64 unpaged records; recorded verdict plus policy/validator provenance |
| get_diagnostic(binding, run_id) | diagnose | Recorded Run/validation summary; digest retained as unverified |

Five frozen DTOs: `ProjectBinding`, `SourceIdentity`, `ReadCursor`, `ReadError`,
`ReadEnvelope`. Envelope schema is `gd-af-read-v1`; it carries safe authenticated
source identities, local read time, optional source time, completeness,
consistency, projected data, cursor and typed error. Nested projected dictionaries
are detached but not deeply immutable; they are not signed evidence records.

The sole external import is the lazy
`from abqjobpilot.service_discovery import discover` inside adapter `_discover`;
its only invocation is `discover(explicit_project_root)`. No source import reaches
private AF implementation modules. Every operation rediscovers and checks the
expected Project/instance/context/owner and protocol; no client is cached or
publicly returned. The constructor performs no discovery.

Unknown fields remain null or incomplete. Optional provenance absent from native
Project pages is not inferred from backend names. COMPLETE means complete required
read projection, not complete scientific provenance. Read calls are explicitly
non-atomic across calls. Unknown event types can be omitted only with INCOMPLETE
and advancement of the raw cursor. Invalid/oversized responses fail without data.
Tree bounds are depth 12, nodes 8192, aggregate characters 262144 before encoding,
and serialized response bytes 262144. Arbitrary nested fields and exception
messages are never echoed.

## Actual verification

Selected existing interpreter:
`D:\XianLab\envs\LangChainEnv\Scripts\python.exe`, Python **3.12.10**, pytest
**9.1.0**. Ruff is the existing standalone
`D:\ProgramData\anaconda3\Scripts\ruff.exe`, **0.12.0**. Ruff is not installed as
a module in LangChainEnv; no install was attempted.

Commands used from the GD-CAE root (variables are process-local):

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
$env:PYTHONPATH='D:\Projects\Goal-Driven-CAE-Orchestrator\src'
& 'D:\XianLab\envs\LangChainEnv\Scripts\python.exe' -B -m pytest --collect-only -q -p no:cacheprovider
$testTemp = Join-Path (Get-Location) ('.pytest_cache/m01a-full-' + [guid]::NewGuid().ToString('N'))
& 'D:\XianLab\envs\LangChainEnv\Scripts\python.exe' -B -m pytest -q -p no:cacheprovider --basetemp $testTemp
& 'D:\ProgramData\anaconda3\Scripts\ruff.exe' check --no-cache .
git diff --check
```

Focused runs used the same options and unique basetemp, adding
`tests/architecture` or `tests/unit/test_af_evidence.py`.

| Check | Actual result |
| --- | --- |
| Before-code baseline | 31 passed in 0.27s; Ruff all checks passed |
| Migrated architecture suite | 76 passed in 0.29s |
| Final collection | 138 tests collected in 0.15s |
| Final full suite | **138 passed in 0.60s**, no failed/skipped/xfail tests |
| Final bridge-only suite | **61 passed in 0.16s** |
| Final repo-wide Ruff | **All checks passed!** |
| git diff --check | Exit 0, no whitespace errors; Git prints existing LF-to-CRLF normalization warnings |
| Protected hashes / ignored assets / index | Nine hashes equal; both local areas ignored and untracked; index empty |

Initial invocations are not hidden: without PYTHONPATH, collection failed because
the package is not installed in the selected environment. With PYTHONPATH,
baseline collection succeeded (31), but the default Windows Temp directory caused
24 passes/7 fixture setup errors; the architecture agent likewise saw 68 passes/8
setup errors with that default. Unique repository-local basetemp resolved these
without permission/environment changes. The first bridge collection also caught
an unterminated test string; it was fixed before the 47-test initial bridge pass
and final 61-test suite. These were local development failures, not a claim of
successful CI. CI was not run or triggered.

## Acceptance matrix

| ID | Evidence | Result |
| --- | --- | --- |
| A-01 | Exact lazy seam AST positive; private/eager/wrong-location imports, dependency additions and raw subprocess negatives | PASS, synthetic/static |
| A-02 | Wrong Project/instance/context/protocol, changed owner, offline/legacy/credential failures; single discovery and zero queries/fallback on failure | PASS, synthetic |
| A-03 | Import/constructor traps for AF import, process calls and writes; failure path; default lazy seam exercised using synthetic sys.modules only | PASS, synthetic/static |
| A-04 | 70 Runs in 32/32/6 pages; cursors 0/39/7; 70 interleaved events; distinct page times and non-atomic declaration | PASS, synthetic |
| A-05 | 64 filtered-out known or unknown events yield empty visible page and cursor 64; following event 65 remains readable | PASS, synthetic |
| A-06 | 65 unpaged validations, malformed records/identity, excessive bytes/depth/nodes/cycles, missing pagination marker fail without data | PASS, synthetic |
| A-07 | Nested credentials, paths, Grant, namespace, key and exception-message injection removed from serialized outputs | PASS, synthetic |
| A-08 | Health advertises writes; facade still exposes exactly seven reads; generic/writing attributes absent and static bypass cases rejected | PASS, synthetic/static |
| A-09 | NOT_FOUND/COMMUNICATION_UNKNOWN on original receipt key causes one lookup only; no new key, retry, submit or no-side-effect inference | PASS, synthetic |
| A-10 | 76 architecture tests retain controlled-negative coverage, frozen hashes, import DAG, no write/process/CWD/verdict authority | PASS, synthetic/static |
| A-11 | README/.gitignore before/after SHA-256 match; original unstaged edits preserved | PASS, byte comparison |

An independent read-only subagent found four issues: missing pagination marker
interpreted as terminal; insufficient Run provenance; incorrect Standard status
allowlist; late aggregate-byte checking. All four were fixed with regression
coverage. Its second review found no remaining blocking issue. That review is
advisory; the actual test executions above are the validation evidence.

## Risk register and limits

| ID | Risk / remaining limit | Handling and next gate |
| --- | --- | --- |
| R1 | No real AF import, discovery or IPC occurred; Python source inspection is not runtime compatibility | M01-B at pinned AF revision; no AF_READ_COMPATIBILITY_VERIFIED claim now |
| R2 | Ordinary AF credentials support writes; same-user Python can bypass a facade or AST guard | Facade-only restriction stated explicitly; hard read-only credentials/RBAC require separate AF work if required |
| R3 | Native validations are unpaged; oversized runs cannot be read through this bounded API | Fail unavailable, never truncate; scalable paged validation API would require separately approved AF modification |
| R4 | Separate read pages/calls are not atomic; owner changes invalidate cursors | Explicit identities/times/cursor binding; no automatic rebinding or snapshot claim |
| R5 | Projection omits diagnostic prose/artifacts; optional provenance may be unknown; digest is not verified or a signature | Downstream verification must require its needed fields; no scientific or artifact verdict from COMPLETE |
| R6 | Frozen DTOs have mutable nested dictionaries; IDs/hash-shaped values are not anonymization or cryptographic authenticity | Treat as transient read views, not persisted trusted VerificationRecords |
| R7 | Static guards detect known patterns, not all reflection/dataflow; trusted discovery injection can execute arbitrary test code | Injection is test infrastructure, not user plugin surface; no sandbox claim |
| R8 | Source-version/schema/status changes can return INCOMPLETE or unavailable | Keep compatibility test keyed to AF revision; never broaden fallback silently |
| R9 | Python temporary-directory permissions and absent project install affect test invocation | Document process-local PYTHONPATH and unique ignored basetemp; no shared environment repair |

Existing AF capabilities used by design: explicit attach-only discovery, identity
checks and seven read RPCs. Implemented here: GD DTO projection, bounds, cursor
semantics, error sanitization, governance and offline guards. Proposed only:
ResearchProject state, independent numerical verification, professional roles,
MCP/Skills and Event Bridge. Strong server-side read-only identities, additional
paged evidence retrieval, or missing future execution operations cannot be supplied
by hiding private AF access; they require separate AF scope and review.

## M01-B proposal — separate approval required

Proposed reserved root:
`D:\Projects\Goal-Driven-CAE-Orchestrator\.pytest_cache\m01b-af-read-20261028-01`.
It was not created or inspected in this stage. Treat it as an exact future
allowlist entry; if it exists at approval time, stop and select a new explicitly
approved empty root rather than reuse or delete it. Project, Runtime, connection,
Recent and logs must all have explicit isolated paths beneath that boundary.

Requested M01-B permissions must explicitly cover creating a no-Solver AF TEST
Project, starting one identified TEST-only owner, using its private local
credentials, and stopping only that owned process. No production root, real
Abaqus backend, process-fixture backend, license/Grant, ODB access or Stable access
is implied. GD remains a read-only consumer. Test seeding belongs to an approved
AF operator/test harness, not the bridge: if synthetic Run/receipt/validation data
requires fake submissions or validation writes, authorize that setup separately
and confine it to this TEST root. Do not manufacture data by direct DB edits.

Preflight before any start: re-read environment policy and applicable AGENTS;
verify both source revisions, interpreter/import dependencies without installation,
resolved root boundaries and no reparse escape; inspect existing public AF TEST
bootstrap/owner API; confirm simulation-only configuration, no real backend/Grant,
explicit credential location and operator ownership. If current public setup
cannot satisfy these conditions, report BLOCKED rather than adding private
coupling or modifying AF under M01-B's read-compatibility scope.

Compatibility steps after approval: independently establish Project/instance/
context/owner expectations; execute the seven reads using the actual lazy seam;
compare safe DTOs and cursor/error semantics with trusted operator-visible
records. Test empty and populated data, 70-run traversal, filtered-empty events,
original receipt NOT_FOUND, missing capability, unavailable owner, and stale owner
binding. Observe connection/read behavior without issuing writes through GD.
Archive sanitized test metadata and source versions; never export credentials or
models. Only this evidence can support AF_READ_COMPATIBILITY_VERIFIED.

Abort on identity/root mismatch, non-TEST backend, unexpected process/write,
credential leakage, implicit Recent use or incompatible source drift. Disconnect
the reader; stop only the separately authorized TEST owner after confirming its
identity. Preserve logs and test data for review. Do not kill unrelated processes,
delete directories, restart, repair, rebind a stale cursor, or alter production.
Any recovery or rerun requires a newly explicit binding and appropriate reviewed
permission. End with a compatibility report and stop for M01-C approval.

## M01-C proposal — no implementation

After M01-B, propose an allowlisted MCP wrapper around these seven methods and a
Codex Skill explaining explicit binding, evidence levels, uncertainty and when to
stop. Keep raw client objects, arbitrary command/tool dispatch, submit, Grant,
owner lifecycle and recovery out of that wrapper. Add protocol-level negative
tests for malformed schemas, secret projection, cross-Project cursors, writes and
unknown evidence. Skills guide native Codex Main/Subagents; they are not a second
agent harness or security boundary. Server startup/configuration and any additional
dependencies require their own approval. SDK/app-server event continuation is a
separate future feasibility task and remains unimplemented.
