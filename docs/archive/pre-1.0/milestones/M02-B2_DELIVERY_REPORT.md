# M02-B2 — Delivery report

Status: **PASS — BUDGET_LEDGER_SYNTHETIC_PASS, 2026-10-28.**

Completed G0–G3 for local synthetic accounting only. No REAL_AF_GRANT_INTEGRATION,
SOLVER_CALL_BUDGET_ENFORCED or AUTONOMOUS_WORKFLOW_VERIFIED claim is made. Stop for architecture
review; M03-A is a proposal, not an implementation.

## G0: actual baseline and environment

Actual branch `main`, HEAD `af3cfd90821cddf65ef93827a20fc2b26d98f0fc`, empty index. The dirty
worktree contained earlier M01/M02-A/B1 work; no local artifact is assumed to exist remotely.
Read global environment policy, complete B2 taskbook, actual A/B1 design and reports, ADR-003/004,
SQLite/freeze/candidate code and relevant architecture/MCP tests. The pre-change manifest below
captures 75 non-ignored files before B2 edits. Private model and ignored credential areas were
excluded from inventory, hashing and scanning.

Verified existing interpreter `D:\XianLab\envs\LangChainEnv\Scripts\python.exe`, Python 3.12.10,
SQLite 3.49.1, pytest 9.1.0, mcp 2.3.0. No dependencies or environment settings changed. Baseline
full safe suite: **410 passed, 2 skipped in 27.22s**; Ruff `All checks passed!`.

## G1: semantics recorded before code

See [BudgetLedger design, state graph and implemented API](../architecture/M02_BUDGET_LEDGER.md).
One slot means one conservative attempt allocation. Cost is exactly integer 1, governed by the
frozen Goal's max_solver_calls; zero cannot allocate. It is not a count of observed Solver launches.
The invariant is `available = limit - held - charged >= 0`.

| State | Held | Charged | Permitted transition |
|---|---|---|---|
| RESERVED | 1 | 0 | explicit pre-intent release or record exact intent |
| SUBMISSION_INTENT_RECORDED | 1 | 0 | UNKNOWN or bound synthetic acceptance |
| ACCEPTANCE_UNKNOWN | 1 | 0 | further unresolved observations or bound synthetic acceptance |
| ACCEPTED_OR_CHARGED | 0 | 1 | terminal, exact replay only |
| RELEASED_PROVEN_NO_ACCEPTANCE | 0 | 0 | terminal, exact replay only |

Release requires unused **pre-intent** protocol state and a checked transaction; it is not evidence
about an external action that bypassed the protocol. Post-intent release is deliberately refused
throughout B2. Timeout, response loss, missing Receipt, expiry, process death and a later Turn do
not restore availability. Synthetic acceptance converts the held slot to charged once, never
increments an inferred launch count and never implies actual Grant consumption.

The first reservation pins one Project-wide account to exact Bundle/Goal IDs/versions and all
four frozen digests. A later freeze cannot reset its limit or hide previous exposure. Other scopes
cannot allocate or inspect a fresh pool; original-scope settlement remains possible. A downstream
`fake_` business key is immutable and unique for account lifetime, including released reservations.
Changing operation key or Candidate cannot recycle it. Candidate membership/output digest and
NOT_ABAQUS_QUALIFIED status are checked within reservation's SQLite transaction; staged-file
qualification or actual execution remains a separate concern.

All results deny execution authority, real acceptance, real Grant consumption and Solver start.
General Project.inspect reports LOCAL_SYNTHETIC_ALLOCATION_ONLY after ledger events, with
budget_real_execution_enforced=false. Proposal, auto-Turn and wall-time accounting are deferred.

## G2: persistence, compatibility and source changes

Implemented `BudgetScope`, strict ReservationRequest, pure event reducer, BudgetLedger service
and an explicit in-memory SyntheticOracle. Typed observations bind fixture ID, reservation ID,
business key, downstream digest and outcome. The ephemeral HMAC rejects changed payloads or
another issuer; raw dictionaries and agent prose are rejected. Its key/seal is not persisted,
and this is not production receipt authentication or protection against arbitrary same-user code.
Stored observations stay SYNTHETIC_ONLY and cannot assert a real AF fact.

No immutable contract or SQL table schema changed; no on-open/on-disk migration runs. New
`BUDGET_RECORDED` events carry `budget-event-v1` payloads in the same audit table. Each mutation
uses the existing BEGIN IMMEDIATE authority to atomically append budget evidence and update
Project revision plus shared UTC/transaction stamp. Ledger revision advances independently once
per budget event. Every read reconstructs states and sums from validated audit order; it does
not trust a free-standing counter or conversation memory.

Necessary explicit revision extension: Project revision now orders contract **and budget** changes.
Historical values remain unchanged; candidate observations still use audit sequence without an
extra Project revision. Freeze rows may have gaps explained by budget events. Candidate admission
matches the latest frozen Bundle rather than mistaking a budget revision for a new contract.
Outputs distinguish frozen contract revision, Candidate creation revision and current revision.
Mutation request revision bounds expand to the existing 1024-event bound; old request bytes do
not change. Regression tests cover Candidate creation and later freezes interleaved with budget
events, preserving original frozen bytes and unknown holdings. Old readers reject new event kinds;
do not use old writers once B2 events exist.

Replay returns `ORIGINAL_OPERATION_RESULT`: state and counters are **historical**, alongside the
original and current Project revisions. `inspect_budget()` is the current balance/state API.
Allocation always checks reconstructed current state; replaying an old UNKNOWN result after a
charge does not restore credit. Strict revision types remain enforced even on exact replays.

| B2 file | Purpose |
|---|---|
| `src/aegiscae/research/budget_rules.py` (new) | strict scope/request, state transitions, bounded deterministic event/counter replay |
| `src/aegiscae/research/budget.py` (new) | explicit transactional APIs, replay and synthetic-oracle capability |
| `src/aegiscae/research/project.py` | new versioned audit kind, atomic budget revision writer, full mixed-event validation and accurate inspect marker |
| `src/aegiscae/research/mutation.py` | latest-frozen-parent checks and separate revision/scope reporting after budget writes |
| `src/aegiscae/research/mutation_rules.py` | bounded Project revision range aligned with mixed audit capacity |
| `tests/unit/test_budget_ledger.py` (new) | 74 functional/process/failure/negative tests |
| `tests/architecture/test_package_skeleton.py` | exact two-module allowlist |
| `tests/architecture/test_research_boundary.py` | exact Project revision UPDATE allowance plus three negative cases |
| `docs/architecture/M02_BUDGET_LEDGER.md` (new) | G1 semantics, graph, APIs, compatibility and limits |
| `docs/milestones/M02-B2_DELIVERY_REPORT.md` (new) | results, BL matrix, preservation, risks and M03-A proposal |

Existing frozen DTO code, historical ADRs, reports, README/.gitignore, M01 source and prior
functional tests remain unchanged. No second database, Grant issuer, AF client, process launcher,
MCP write tool, scheduler or workflow was added.

## G3: BL-01–BL-18 acceptance matrix

Named functional evidence is in `tests/unit/test_budget_ledger.py`; all mutable fixtures are
synthetic and isolated outside the repository in fresh TEMP directories.

| ID | Result | Observed machine-checked evidence |
|---|---|---|
| BL-01 | PASS | limit 2 snapshot is held 0/charged 0/available 2; DB bytes/mtime unchanged |
| BL-02 | PASS | one reservation produces held 1/available 1, stable IDs and atomic revision/audit increment |
| BL-03 | PASS | zero/exhausted budget and invalid cost types/values refuse without state changes |
| BL-04 | PASS | exact operation replay returns original reservation/result, no new bytes or charge |
| BL-05 | PASS | changed Candidate/digest/cost/Plan/business key or contract scope with same operation conflicts |
| BL-06 | PASS | two actual child Python processes race for final slot; exactly one winner, no oversubscription |
| BL-07 | PASS | wrong Project/Goal/Model/Verification refs and stale or invalid-type revisions reject |
| BL-08 | PASS | explicit unused pre-intent release restores capacity once; replay cannot double-refund or recycle business key |
| BL-09 | PASS | five UNKNOWN causes retain held slot; release and operation-key substitution cannot recover it |
| BL-10 | PASS | bound synthetic acceptance charges once; replay/conflicts cannot double charge or downgrade; never asserts Solver start |
| BL-11 | PASS | exceptions before_begin/after_event/before_commit/after_commit leave absent or once-committed durable accounting |
| BL-12 | PASS | actual os._exit(73) at four points and independent interpreter reopen; UNKNOWN reconstructs unchanged, no auto retry |
| BL-13 | PASS | existing or crash-retained journal blocks reads/writes without deletion, repair or optimistic refund |
| BL-14 | PASS | synthetic Candidate remains non-runnable; real-style business key/execution surfaces refused; audit-hook test sees no AF/process/network effects |
| BL-15 | PASS | raw notes/dicts, forged seal, wrong issuer and unbound observations cannot become acceptance/Grant/Solver evidence |
| BL-16 | PASS | changed sums/revisions/source/schema and removed event detected, including rehashed payloads; no positive fallback credit |
| BL-17 | PASS | M01 seven-tool, M02-A and M02-B1 suites pass; mixed freeze/Candidate/budget revision and new-contract no-reset cases pass |
| BL-18 | PASS | full suite 487 passed/2 inherited skips; whole-repo Ruff, tracked and new-file diff checks; independent Reviewer 74 passed |

## Actual commands, first failure and retests

Commands used the absolute registered interpreter, `PYTHONDONTWRITEBYTECODE=1`, explicit `src`
PYTHONPATH, `-p no:cacheprovider` and fresh `%TEMP%\gdcae-m02b2-<purpose>-<UUID>` basetemp.
No dependency installation or global configuration change was needed. Live opt-in variables
were removed only from the test shell process environment.

```text
python.exe -m pytest -q -p no:cacheprovider --basetemp <fresh external TEMP>
G0 complete baseline:                 410 passed, 2 skipped in 27.22s
M02-A/B1 + architecture regression:    277 passed in 19.15s
Initial budget test suite:             61 passed in 22.11s
Expanded budget suite:                 74 passed in 25.96s
Final tightened scope/inspect checks:   2 passed in 0.73s
Final full suite:                     487 passed, 2 skipped in 50.73s

D:\ProgramData\anaconda3\Scripts\ruff.exe check .
All checks passed!

git -c core.safecrlf=false diff --check
exit 0; no whitespace diagnostics
```

The test author reported one intermediate fixture failure after adding the no-external-effects
child test: a fixture digest lacked its `sha256:` prefix (61 passed/1 failed at that intermediate
snapshot). Corrected the test data and reran the expanded suite successfully. No product failure
was hidden by changing or skipping acceptance cases. Review tightened revision type validation
before replay, explicit same-key/different-scope conflict reporting and general Project.inspect's
local-budget label; dedicated assertions and final full regression cover those changes.

Three new architecture negatives ensure the budget revision UPDATE cannot be borrowed by a
readonly method, moved into budget.py, or changed to DELETE. No old guard was disabled.
New untracked source/test/docs are separately checked via `git diff --no-index --check -- NUL <file>`;
exit 1 without diagnostics is the expected “different from empty file” result.

Exact inherited skips:

- `tests/integration/test_af_read_live.py::test_g1_g2_real_authenticated_fake_only`, line 403:
  `Explicit M01-B approval, fresh TEMP root and isolated invocation required`.
- `tests/integration/test_mcp_read_live.py::test_real_stdio_codex_native_review`, line 228:
  `M01-C fresh TEST root and explicit live opt-in required`.

Both require separate AF TEST Owner authorization. No mandatory offline budget safety case was
skipped, and this report does not recertify live AF compatibility.

## Process, crash and UNKNOWN evidence

The last-slot race launches two actual `sys.executable -B` children, waits for both ready markers,
then releases them through separate stdin pipes. Both use the same Project with distinct operation
and business keys. Exactly one reservation exists afterward; the losing process returns a clean
domain refusal/busy result. Only those fixture-owned child processes may be terminated on a test
failure. No Supervisor or Solver is involved.

A separate fresh child reconstructs frozen scope, original budget/audit identifiers and pending
UNKNOWN state through readonly opening; hashes and mtimes are unchanged. Four `os._exit(73)`
faults test hard exits around durable writes. Where a journal survives, product access is blocked
and the files are preserved. Where safe reopening succeeds, state is absent or committed once;
lost acknowledgements can be queried/replayed explicitly without another debit. The ledger has
no automatic retry, journal cleanup or recovery path.

Mixed-sequence tests reserve, release, record intent, hold UNKNOWN, charge and replay while
checking held+charged never exceeds limit. New frozen policy/limit cannot create a replacement
pool or conceal old UNKNOWN. Missing Receipt and elapsed-time explanations are only synthetic
UNKNOWN reasons, never negative-acceptance proof. No AF Run, real Receipt or Grant is created.

## Independent Reviewer

Native `/root/m02b2_review` performed readonly compatibility, implementation and test-body review.
It confirmed no mandatory frozen-contract Schema blocker and no blocking accounting defect,
including pinned scope, lifetime business keys, mixed-event revision validation and synthetic
evidence limits. It independently verified the environment and ran the stable budget suite:

```text
python.exe -B -m pytest tests/unit/test_budget_ledger.py -q
  -p no:cacheprovider --basetemp <fresh external TEMP>
74 passed in 30.90s
```

Its non-blocking request was to state explicitly that replay counters/state are historical and
inspect_budget is the current accounting view. Both design and this report now do so. Reviewer
made no repository edits, visited no AF Project and inspected no real model. This review is not
independent physical validation or production AF evidence authentication.

Final readonly review of both completed documents returned **no blockers**. Reviewer confirmed
the synthetic-only label, event/revision compatibility explanation, BL matrix, resolved historical
replay note, Git whitelist and M03-A proposal boundary; it also independently confirmed unchanged
HEAD and empty index. Review is complete; stop for next-stage architecture approval.

## Read-only Git checkpoint readiness audit

Against the 75-file pre-B2 manifest: **70 byte-identical, five scoped existing files modified,
zero missing; five new files**. Exact B2 whitelist is the ten paths in the source table above.
The existing modifications are project.py, mutation.py, mutation_rules.py and two architecture
guards; earlier M01/DOC changes and all A/B1 functional tests and reports are preserved.

Final Git state: `main@af3cfd90821cddf65ef93827a20fc2b26d98f0fc`, **6 tracked modified files,
29 untracked files**, empty index. Those Git-vs-HEAD counts include inherited milestones and
must not be confused with B2's manifest-relative delta. Many earlier source files were already
untracked; neither their original presence nor current status proves remote publication.

Readiness checks:

- Kickoff_Docs, CAE models and .codex/config.toml remain ignored at .gitignore lines 32/33/34.
  `git ls-files` for these areas returned no tracked entries. No ignored contents were scanned.
- Scoped non-ignored text scan found no private-key header or high-confidence AWS/GitHub/OpenAI
  credential pattern. No values were printed. Test keys/evidence are explicit fake data; the oracle's
  ephemeral runtime key is not persisted. This is a bounded heuristic scan, not comprehensive DLP.
- Existing retained M01 encrypted credentials/test evidence were not reused, inspected, exported
  or deleted; the earlier retention risk remains outside this checkpoint.
- A future checkpoint should review the explicit B2 whitelist alongside the captured inherited
  M01/A/B1 inventory, tests and untracked reports, exclude all private/runtime directories and
  verify frozen-baseline hashes again. Do not use a broad add operation or silently include old
  test-owner artifacts. Recommend a separately authorized local M01–M02 checkpoint review.

Checkpoint status: **ready for human scope review, not staged or committed**. No commit, push,
PR, CI trigger, cleanup/reset/stash, dependency installation or environment change occurred.

## Risks and technical debt

| Risk | Current boundary |
|---|---|
| Unknown acceptance | Held indefinitely after intent unless bound synthetic acceptance charges; post-intent release not implemented |
| Journal recovery | STORE_BUSY may block readonly inspection too; no hot/cold journal classification, repair or forced unlock |
| True AF binding | No authenticated receipt/Grant/Run/attempt integration; fake_ keys and synthetic observations cannot substitute |
| Oracle / host authority | Local capability and hashes are not protection against arbitrary same-user code or coordinated database rewriting |
| Cross-resource atomicity | Future external side effects cannot share the SQLite transaction; intent-before-effect and explicit reconciliation remain necessary |
| Cost and policy changes | Fixed one-slot conservative attempt policy, pinned first scope; no refunds after intent, account reset, multi-resource costs or policy migration |
| Capacity / performance | At most 128 lifetime reservations and existing bounded audit/store; full deterministic replay is not a scalable distributed ledger |
| Historical results | Replay counters are old snapshots; allocation must use current inspected/reconstructed state |
| Old binaries | Unknown budget event kinds fail closed; old writers must not modify projects containing new events |
| Model/authorization validity | NOT_ABAQUS_QUALIFIED persists; no physics, numerical, Goal or execution-authority promotion |

## M03-A minimum Fake two-step loop — proposal only

Propose one deterministic offline driver with exactly two approved synthetic stages, no general
workflow/DAG or autonomous Agent loop. Codex remains the sole harness. Use a frozen limit of two
attempt allocations and explicit Fake-only downstream keys:

1. Create/read one permitted synthetic Candidate A; reserve its slot, record the intended Fake
   request digest/key, then let a controlled in-process Fake adapter produce a synthetic acceptance
   transcript. Reuse the existing seven-method EvidenceBridge with an explicit synthetic discovery/
   transport double to read attributed Fake Run/Receipt/validation data. Charge the matching slot;
   never reinterpret fake validation as physical or real Solver success.
2. Only after step-one evidence resolves without required UNKNOWN, deterministically propose a
   second permitted scalar Candidate B under the same frozen research scope. Reserve the second
   slot, record its exact distinct key/digest, produce/read a second Fake transcript and end with
   a bounded two-step research summary. Any unresolved acceptance blocks stage two and retains
   exposure; it cannot be refunded or retried under a fresh key.

Before implementation, specify the bridge-to-oracle evidence binding and two-step state contract.
Minimum independent tests: exact two-stage order; third slot refused; crash/lost response after
intent leaves UNKNOWN and stage two blocked; exact replay creates no duplicate Fake acceptance
or charge; wrong Candidate/key/digest/source evidence fails; counts survive a separate interpreter;
the seven MCP tools remain readonly; no Supervisor/Abaqus/ODB/SDK/app-server is started. An actual
TEST Owner or production bridge connection would require separate explicit authorization.

No driver, Fake dispatcher, AF call, extra MCP tool, Codex Turn continuation or M03 implementation
was added in B2. **Stop here and wait for next-stage architecture review.**

## Pre-change manifest

```json
{
  "branch": "main",
  "HEAD": "af3cfd90821cddf65ef93827a20fc2b26d98f0fc",
  "status": " M .gitignore\n M tests/architecture/test_af_read_boundary.py\n M tests/architecture/test_dependency_direction.py\n M tests/architecture/test_forbidden_direct_writes.py\n M tests/architecture/test_forbidden_surfaces.py\n M tests/architecture/test_package_skeleton.py\n?? .agents/skills/gdcae-evidence-review/SKILL.md\n?? .codex/agents/gdcae_evidence_analyst.toml\n?? .codex/agents/gdcae_independent_reviewer.toml\n?? docs/architecture/M01-C_READ_INTERFACE.md\n?? docs/architecture/M02_MODEL_MUTATION_GUARD.md\n?? docs/architecture/M02_RESEARCH_PROJECT_AND_CONTRACTS.md\n?? docs/milestones/M01-B_DELIVERY_REPORT.md\n?? docs/milestones/M01-C_DELIVERY_REPORT.md\n?? docs/milestones/M01-C_SOURCE_DIFF.patch\n?? docs/milestones/M02-A_DELIVERY_REPORT.md\n?? docs/milestones/M02-B1_DELIVERY_REPORT.md\n?? src/aegiscae/contracts/research_contracts.py\n?? src/aegiscae/interfaces/mcp_read.py\n?? src/aegiscae/research/__init__.py\n?? src/aegiscae/research/mutation.py\n?? src/aegiscae/research/mutation_rules.py\n?? src/aegiscae/research/project.py\n?? tests/architecture/test_research_boundary.py\n?? tests/integration/test_af_read_live.py\n?? tests/integration/test_mcp_read_live.py\n?? tests/unit/test_mcp_cleanup.py\n?? tests/unit/test_mcp_read.py\n?? tests/unit/test_model_mutation.py\n?? tests/unit/test_research_project.py\n",
  "files": {
    ".agents/skills/gdcae-evidence-review/SKILL.md": "076540096f1741a36a02ef90145b17b06c14939337d46400803de38c1499ac4a",
    ".codex/agents/gdcae_evidence_analyst.toml": "2027843f8cd76e528318ea6d1000157963f6abbe54e504ac04539abac00679c8",
    ".codex/agents/gdcae_independent_reviewer.toml": "09b9f681f96729a6b02578e80b387f9fe8204598034d62ff56f77a5d1a81f68f",
    ".editorconfig": "18585eca8767e0886ef3d0a2bd1d7464a165500ee7c2284e58a55611655f2a8c",
    ".gitattributes": "1a1dbe176bc233b499d35a57db7513f2941c99ab9759f177830c9149be99005b",
    ".github/workflows/ci.yml": "e230a76883b9f1dd229f7e45445b6bc26fd09812b0905299028ccd5c70062dec",
    ".gitignore": "41e243b05a6cbad08ad5252f7fb7ce35de61be34abe6c25abc91ab84d46bed24",
    "ARCHITECTURE.md": "ebc33f8fd0cbc9eb8203960df062f81c7964b2fc7f6e2695d82a8d07ed026e08",
    "LICENSE": "17de84ce8b605a18699d04d6d9371da2aacc0e2af58f2128e87f75e6d190f901",
    "MIGRATION_FROM_LEGACY.md": "3778e3db77d42d0fbe642d1cbac3c0d515e79e735875eda56c57ddb4eeb48093",
    "README.md": "ebe31922b1ac9914880dfcf4e2d99caa36aebb322300f74606d4a5171b8661ce",
    "RUNTIME_INVARIANTS.md": "b6440ea1229728e7eedd706f7e7486cec2acd4703524aa99da2db4b8555e20e4",
    "THREAT_MODEL.md": "832aef9e7da7f069fe7d6bc4238c49c1481816ff16da349bc5d0a0e3bc64ac43",
    "docs/adr/ADR-001-runtime-first.md": "23600e64d28e6fe857399cadd063ef0a35bd1928328d0de8fe9d388b4c14b71c",
    "docs/adr/ADR-002-legacy-selective-migration.md": "7776428482bbc64ff79cba8593773cd6ff6aa7dd670bf650f1fc52eb158be5a9",
    "docs/adr/ADR-003-codex-native-delegated-execution.md": "b3347ce62130638c42d108434173312869981fcb864efe47d86843b5030756eb",
    "docs/adr/ADR-004-execution-evidence-research-verification.md": "63e029b1bbdea3a1905d11259143639530f8f840e4d31403034beb90b1463e68",
    "docs/adr/README.md": "52490bf00587c54300b7a9fbace5752f22be123b0f79abf06135b9d34c65d5d6",
    "docs/architecture/CURRENT_AUTHORITY.md": "980b86142a881bb9d1a2283eaea3be38ffb7b00281764932d3300d88560f4a34",
    "docs/architecture/M01-C_READ_INTERFACE.md": "f606677e8f91132da0c4f1c67a61e27ef81d1728f20793e78a76e7628011415f",
    "docs/architecture/M01_EVIDENCE_BRIDGE.md": "88b0af9ccad3a1d993e9157fe9da895c74a4ae89eee852cb303e499aed32ef11",
    "docs/architecture/M02_MODEL_MUTATION_GUARD.md": "5ab88297b56f30a3a8791c6ad0b2bf4e59f920f22a57aec920db9c6b7162665c",
    "docs/architecture/M02_RESEARCH_PROJECT_AND_CONTRACTS.md": "bb1c74ba7ffc82a18324778dd82414cfff1deabef3c547caad637b6470165e90",
    "docs/baseline/AegisCAE Runtime \u9879\u76ee\u8ba1\u5212\u4e66.md": "9a89a5ad661a80a69ec159124066e5b34ed6dc74de9295336f426b17079e7448",
    "docs/baseline/BASELINE_REGISTER.md": "9ec1426dc4abd3f8c3add8cb8f036a65a67fb70653ca2c2188dbb987afc1f6aa",
    "docs/baseline/LEGACY_ABQJOBPILOT_SUMMARY.md": "f938b243ff438c6e7587f9337be4c4730e4bddeed78a874a5bd4e0f2a1128dfb",
    "docs/baseline/LEGACY_ABQPILOT_SUMMARY.md": "d1685d26a208f15ad772335fcd927c0c22f31f0fe8901613d9a7b02ac9591a43",
    "docs/baseline/LEGACY_MIGRATION_DECISIONS.md": "d90e35737ee86a3aa77b67afa5d6becf4977a371f35517317615db351e3603c2",
    "docs/milestones/M01-A_DELIVERY_REPORT.md": "eaa87b9ed4d1ced4b7cb0acf24b7d7a76d6a0100864c073507497b853ded8a47",
    "docs/milestones/M01-B_DELIVERY_REPORT.md": "54875e0c3838443a53e0ef9ce03999a3aa9e02c782165d36d33f78ee54f1f8d1",
    "docs/milestones/M01-C_DELIVERY_REPORT.md": "1ae1d2867c930031df4ee4884748f21115b3dd47b1d1ecc95794738162b8e0e5",
    "docs/milestones/M01-C_SOURCE_DIFF.patch": "52232088439a097ed814dfcd9005cc7d2e7d3af5e716bfe7e71ea7aebc764859",
    "docs/milestones/M02-A_DELIVERY_REPORT.md": "76708c488046d4cb67071c1b5ba66c0626a3e9c9ecf05e7944d019cc63ef8cfa",
    "docs/milestones/M02-B1_DELIVERY_REPORT.md": "20080f65ff3336a26d8a4314c1d4c09a820b9a07e7625e4c62063b3edc3372c1",
    "docs/milestones/MILESTONE_00_IMPLEMENTATION_PLAN.md": "9bf3a2b11d2b13f9f7e9d1b6b5947aa18b4701a23b935bacd262facc348d0771",
    "pyproject.toml": "9fc0d3c6c8939cbfb72dc9b88673e3c100e79782da317cce57a81912eecd1c8a",
    "src/aegiscae/__init__.py": "03cad15b185a6b873f497355a7f349e3c2771b7a13a84e913c05187d7333e910",
    "src/aegiscae/adapters/__init__.py": "802176739638c040953157b3632ea16c4c06505a3a95a68538d3469350996551",
    "src/aegiscae/adapters/abaqus/__init__.py": "5ecb6d3606d6312a2897a304a0cbace18d8858343d7bebc679d66ac83740af90",
    "src/aegiscae/adapters/abaqus/af_evidence.py": "8b7a1cdd57dd0d4a067bc32037ac8893aa1662348f9d94baec01b34e670a88b0",
    "src/aegiscae/contracts/__init__.py": "9f3e24fec4f6884cf63b3b585e5f041a43fbfac800ef40f87bb1d320c79e4b92",
    "src/aegiscae/contracts/af_evidence.py": "401ecb551591376f854247b7e64cc4d13f82cd54c17c098bdba2b26943d5f012",
    "src/aegiscae/contracts/research_contracts.py": "8f8fb5017fa9b9f0bfcdd827dab6915da8af93d488b81500bd6a440167fcff16",
    "src/aegiscae/interfaces/__init__.py": "4bf573cf307c6f457faaff35a385e4e9da78fd9d111964a1d2cfac92ee072586",
    "src/aegiscae/interfaces/mcp_read.py": "10d69706b58b1fdec77b21cd8df56a558111c4469ee3b75b143f84480274085d",
    "src/aegiscae/research/__init__.py": "865f21faca277a7de68665865ba9ea2cffa6537464594cd526ac148b5b6654f6",
    "src/aegiscae/research/mutation.py": "85bf7a8ed9606317a8842530678fb0f46a0e4ae0366d161b2497a11caae293ea",
    "src/aegiscae/research/mutation_rules.py": "0635ffe3d85f66919c62560fbff0cd60adafb4f6bdc27119033a200e1ba8bf9b",
    "src/aegiscae/research/project.py": "7392ef0d3a5cd037c965c0f43e00a13a7a5e5e5b2e4d2fb51476d594be297cbf",
    "src/aegiscae/runtime/__init__.py": "2c15584b91a9468f50e5fa9fbbc1d11532d20140cab576a44219ba22a82b96d8",
    "src/aegiscae/validation/__init__.py": "e518637e4813de20fadc7d268e288ec739625692ef156a86324a275ac754e042",
    "tests/architecture/test_af_read_boundary.py": "5ea98c4295df7a1ea97280fe57e6a822cf0a97d14745c41d69140c55f435f1fe",
    "tests/architecture/test_baseline_integrity.py": "a564da95cc8ab8531aec0e8f1efb477ac94285efbd6ea37f2893bd3e12ea172d",
    "tests/architecture/test_dependency_direction.py": "3e0f850934735fa17a1cd412b97ecd25ffec6cb9124b2380005ffbe5a4316377",
    "tests/architecture/test_fixture_evidence_policy.py": "98d7247eaeff18a8b383d53fb582bcb4db91b23b15b096a5f0c8c4db06b9c498",
    "tests/architecture/test_forbidden_direct_writes.py": "29bae2845487766cc6e4751d8ad5e30ac0a38615edf36987f1af13f6f601fcd9",
    "tests/architecture/test_forbidden_execution_calls.py": "ec6b8fec7fac7cfc5b6d4a546fa9784d1021ff004f8f7d16011ab49fcf5f1af3",
    "tests/architecture/test_forbidden_legacy_dependencies.py": "fdfb6a2501c5419bab5dbf0e0b95dfeb6454b26b5b2db08790777daeae70fe3e",
    "tests/architecture/test_forbidden_paths_and_cwd.py": "e2b68493c83a1f2d320afbc77c02c98de7b37329888d4f79aa5d9ef45ef0dfe3",
    "tests/architecture/test_forbidden_surfaces.py": "d4e77b8f04027d033118332852f75f0cb8a0c6bafb66815c5556c77a5e90d6bb",
    "tests/architecture/test_no_symlinks.py": "d3d6199a82eb319ba0c374aed61dc1a0f464b3fed4fd78b39396ea5eb233e659",
    "tests/architecture/test_package_skeleton.py": "09f483ff64aa80ffc0e8545a5b8c7e1c27b215862299a523f3984d6a2c48fc75",
    "tests/architecture/test_research_boundary.py": "4780e3abe0037f5388b44993c7442d3f3951f61bf16f0cb192206e8a469da146",
    "tests/architecture/test_verdict_authority.py": "bd2ec5582bb21caf3ebd601bbb39f4b7e218225ca9901fd043752e5517e6d322",
    "tests/conftest.py": "6635df5d72f131657d6e472e72d6ffc91e294c1ed0e9801ce308e9056b66f14d",
    "tests/fixtures/README.md": "97e2adca2c7f6aed8e37adacbf30339a3ffaa1245e982f10781c190f3327b425",
    "tests/integration/README.md": "49de8f43d078c336d4e8e279aa15ba5cc4b78e9d5acf71696103506bb1a939d3",
    "tests/integration/test_af_read_live.py": "3ccf5d5242688a954599a3e2e5623758579ef34bb44f3da8c95800cfd448852f",
    "tests/integration/test_mcp_read_live.py": "ff2c29176cc4571771b710fb4c694fdf34f85f3909aedfef6798f11505c13aaf",
    "tests/unit/test_af_evidence.py": "d7be2b0fae158ab3b5e604c65d4ea99548cc859d70add18644b222615829dd68",
    "tests/unit/test_mcp_cleanup.py": "5bedef4ce2ce757ae3fff29e6513e6b8f2b831d38e588845d041a2ab7a8513da",
    "tests/unit/test_mcp_read.py": "4fadf2d2e7f5c8e0860c9a7d57fa9bc9a2ca6727800a0b648963512677b07c53",
    "tests/unit/test_model_mutation.py": "df6b5f03541897908611e0cf176d8d70c270521f7b9e3bb80baa6c23a099ca08",
    "tests/unit/test_package_import.py": "bed78fa82cdc7ea1bb2110296da0e8519eba8bcc98680ba4deebbfdb71003241",
    "tests/unit/test_research_project.py": "49fd300f00c6432a767e57060b09c4dc1a1ba6c0c2d6076e8fd82f9c636d52e9"
  }
}
```
