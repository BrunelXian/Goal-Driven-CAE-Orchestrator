# M03-A — Persistent Two-Step Synthetic Research Workflow

Status: **PASS — M03A_SYNTHETIC_WORKFLOW_PASS**, 2026-10-28.
This is the bounded offline qualification only. No M03-B implementation.
AF_WORKFLOW_COMPATIBILITY_VERIFIED=false; SCIENTIFIC_VERIFICATION_AVAILABLE=false;
ABAQUS_PARAMETERIZED_EXECUTION_VERIFIED=false;
CODEX_AUTOMATIC_MAIN_CONTINUATION_VERIFIED=false. Stop for architecture review.

## G0 actual starting point

Date: 2026-10-28. Branch `main`, HEAD
`6c549dc98c25a12dcb9c93baa4fbf8d629c80ec1`. Index initially empty, tracked tree clean;
the sole untracked item was `docs/milestones/M01-C_SOURCE_DIFF.patch`. Its SHA-256:
`52232088439a097ed814dfcd9005cc7d2e7d3af5e716bfe7e71ea7aebc764859`.
An 80-file non-ignored content manifest was captured before implementation.

Read the complete M03-A taskbook, applicable global Python policy/environment registry,
M02 contracts/store/mutation/budget source and corresponding tests, M02-A/B1/B2 reports
and architecture, M01 bridge contracts/source and accepted ADR-003/004. Prior M02-G
review and source evidence remain in this conversation; no report path was treated as
proof without actual content inspection. No real-model/private-directory traversal.

Existing absolute interpreter: `D:\XianLab\envs\LangChainEnv\Scripts\python.exe`,
Python 3.12.10, SQLite 3.49.1, pytest 9.1.0, mcp 2.3.0. Existing Ruff:
`D:\ProgramData\anaconda3\Scripts\ruff.exe`, version 0.12.0. No installs or environment
file changes. G0 rerun: **487 passed, 2 skipped in 60.81s**.

## Implemented scope and persistence

See [state, protocols, compatibility and authority design](../architecture/M03_SYNTHETIC_WORKFLOW.md).
Two product modules implement a fixed A/B definition, typed synthetic request/receipt/evidence,
deterministic checks and explicit bounded advancement. There is no generic graph, service,
dispatcher, Agent loop, AF adapter or automatic Turn continuation.

No frozen DTO, SQL table or Project metadata schema change/migration was necessary.
`WORKFLOW_RECORDED` / `workflow-event-v1` extends the existing owned audit table. Explicit
writes atomically update Project revision and audit UTC/transaction metadata. Readers replay
mixed freeze, Candidate, budget and workflow events and recompute stored decisions. Old readers
reject this new event kind; old binaries must not write the extended Project. No on-open repair.

The versioned definition freezes two Candidate templates and all four contract digests,
Project/Bundle/Goal identities, independent synthetic source ID, two budget slots and BLOCK
unknown policy. PREPARE binds the current revision. Mutation Guard publishes/rechecks files;
BudgetLedger reserves and commits the original key/request intent. Only the newly committed
CLAIM winner may invoke synthetic acceptance. A reopened or competing caller only queries the
original key. Even query NOT_FOUND cannot permit another accept or restore budget.

Matched synthetic receipts move to OBSERVED; the existing reservation is charged once.
DECIDE rechecks live candidate bytes and independently evaluates frozen objective, all hard
constraints, complete metric selector/unit/frame coverage and separate synthetic protocol health.
Decision records bind rule version/digest, original revision, request/receipt/evidence identities,
evidence digest, budget reservation/effect and deterministic reason. Arbitrary chat or a stored
PASS field cannot substitute. BLOCK and terminal decisions are not automatically reopened.

## Actual synthetic A/B evidence and scientific limits

The positive fixture uses a fixed synthetic baseline `LOAD_N 10`, Candidate A `LOAD_N 20`,
Candidate B `LOAD_N 30`, distinct Candidate/stage/request identities and the existing bounded
text grammar. The independent TEST port produces A displacement 2 mm and B displacement
0.5 mm from a fixed test table. This table is not a physical simulation or load-response law.
Frozen objective is displacement <= 1 mm with 0.01 mm tolerance; the separate hard limit is
10 mm. A therefore has valid synthetic evidence and a genuine objective miss while satisfying
the hard constraint. B satisfies the same unchanged synthetic objective and hard constraint.

The port's separate TEMP fixture database counts its own effects and accept/query calls.
It is not AF Store or production GD-CAE state. Its source, attempt, receipt and evidence IDs
have synthetic prefixes; every response embeds TEST_ONLY/SYNTHETIC/NOT_ABAQUS_QUALIFIED and
physical_evidence_eligible=false. It never uses M01 discover/EvidenceBridge to forge authenticated
IPC. M01 production files and seven-tool behavior remain unchanged.

Actual machine-checked positive sequence: after A, one effect, charged 1, available 1;
after B, exactly two effects and two accept calls, held 0, charged 2, available 0, two durable
decisions. Baseline, original frozen bytes and earlier audit records stay unchanged.

V0/V1 are synthetic checks; V3 is a synthetic metric result. Real V2 is NOT_RUN, V4
NOT_ASSESSED. Both decisions preserve missing_real_checks=[V2,V4] in the positive fixture;
real_goal remains INCONCLUSIVE and acceptance_eligibility SIMULATED_ONLY. No physical,
ODB, human approval, actual Grant consumption or actual Solver launch is established.

## W-01–W-20 acceptance evidence

The functional tests below are in `tests/unit/test_synthetic_workflow.py`. All W-01–W-20
rows passed in the completed final suite; the scope is synthetic-only throughout.

| ID | Test / evidence |
|---|---|
| W-01 | test_w01_w02_definition_is_fixed_scoped_and_revision_checked; test_w01_wrong_frozen_identity_cannot_create_workflow; different-definition conflict |
| W-02 | Fixed two templates, max_steps/budget_units=2 and no RETRY policy; strict definition negative cases |
| W-03 | test_w03_w06_w07_w08_w17_complete_fixed_two_step_research_loop; original source/frozen/audit bytes and live mutation inspections |
| W-04 | test_w04_intent_and_budget_are_committed_before_every_external_like_effect independently observes CLAIMED plus exact durable ledger intent before port accepts |
| W-05 | test_w05_w12_bad_receipt_or_evidence_blocks_b_and_final_claim, exact typed request/receipt/source/digest identities |
| W-06 | Positive A valid 2 mm objective miss with hard limit passed, one effect and one charge |
| W-07 | test_w07_b_requires_fresh_mutation_recheck_after_valid_a; hard-constraint and exhausted-budget negatives |
| W-08 | Positive B 0.5 mm under identical frozen criteria; real V2/V4 remain unresolved |
| W-09 | test_w09_terminal_replay_and_third_reservation_never_add_effect, including terminal two-process calls |
| W-10 | test_w10_independent_fixture_exact_key_replay_and_content_conflict; C/false source and different-content negatives |
| W-11 | test_w11_response_loss_reopens_with_query_only_and_no_duplicate_effect; test_w11_unresolved_query_never_refunds_retries_or_starts_b |
| W-12 | Parametrized receipt/evidence corruption: source/Project/candidate/step/key/attempt/digest/receipt, missing/protocol/unit/frame/metric failures |
| W-13 | Invalid model, hard-constraint failure, stale frozen criteria, exhausted or released budget; real V2/V4 missing-check assertions |
| W-14 | test_w14_two_processes_race_for_claim_only_one_calls_accept; stale revision refusal |
| W-15 | 13 committed-boundary hard exits; fixture accepted-before-death; two transaction hard exits; four exceptions; preserved existing journal |
| W-16 | test_w16_separate_python_reconstructs_decision_and_continues_only_eligible_b |
| W-17 | test_w17_persisted_decision_cannot_be_replaced_by_chat_or_local_snapshot; rehashed decision/verification/receipt corruption rejected |
| W-18 | Dedicated synthetic prefixes/ports and unchanged M01 files; no AF discover injection |
| W-19 | test_w18_w19_no_af_network_process_or_physical_authority_during_workflow; exact source/SQL/fixture guards and private AF/process negatives |
| W-20 | 560 passed/2 inherited live skips; whole-repo Ruff and tracked/new-file diff checks; independent Reviewer 104 passed and no blocking findings |

## Interruption, concurrency and availability boundaries

The two-process race synchronizes actual Python children before competing on the same current
revision. New CLAIM is transactional; only its successful caller can call accept. All later
actors are query-only. An immutable in-flight claim may finish after a concurrent contract
freeze, but subsequent advancement is CONTRACT_STALE, with no B or new-contract conclusion.
Historical inspection is explicitly labelled HISTORICAL_WORKFLOW.

Hard exits cover after_candidate, before/after_reserve, before/after_intent, after_claim,
before/after_effect, after_evidence, before/after_decision, before_b_admission and after_charge.
Claim-before-effect death leaves no fixture effect but remains UNKNOWN rather than resubmitting.
Accepted-before-reply death leaves one independently counted effect and uses original-key query.
Workflow transaction-before/after-commit hard exits distinguish durable continuation from
journal-blocked availability. No existing journal is deleted, forced open or auto-repaired.

All data is newly generated in isolated TEMP roots. Existing M02-A regression includes its
explicit synthetic SQLite integrity inspection; it is not a workflow recovery feature and does
not touch retained historical test databases. New workflow crash tests preserve journal blocks.
No AF Owner, Supervisor or Abaqus process is started. Child processes are ordinary fixture
Python only; normal successful runs need no process-kill fallback.

## Tests and development observations

All runs use the verified absolute interpreter, process-local PYTHONPATH=repository/src,
PYTHONDONTWRITEBYTECODE=1, PYTEST_DISABLE_PLUGIN_AUTOLOAD=1, live flags unset, cacheprovider
disabled and a fresh `%TEMP%/gdcae-m03a-<purpose>-<UUID>` basetemp.

```text
python.exe -B -m pytest -q -p no:cacheprovider --basetemp <fresh external TEMP>
G0 full baseline:                  487 passed, 2 skipped in 60.81s
M02 functional + architecture:    364 passed in 46.87s
Initial workflow test snapshot:   44 passed in 178.10s
Expanded workflow test snapshot:  63 passed in 356.76s
Final identity/port assertions:    8 passed, 55 deselected in 3.68s
Final A/B rule/value assertions:   1 passed, 62 deselected in 15.77s
Independent workflow + guards:   104 passed in 387.57s
Final full suite:                 560 passed, 2 skipped in 438.63s
Ruff check --no-cache .:          All checks passed!
git diff --check and six new paths: PASS, no whitespace diagnostics
```

Initial architecture run: 2 failed / 138 passed because workflow.py was still covered by the
old blanket forbidden filename despite its exact module allowlist. Added only the authorized
research/workflow.py exception and a wrong-location second-workflow negative; no old guard was
disabled. Corrected architecture plus M02 regression passed as above. A test subagent capacity
interruption (`Selected model is at capacity`) did not damage files; it resumed saved work.

The two retained skips require separately authorized live AF Owner lifecycles:

- tests/integration/test_af_read_live.py:403:
  `Explicit M01-B approval, fresh TEMP root and isolated invocation required`.
- tests/integration/test_mcp_read_live.py:228:
  `M01-C fresh TEST root and explicit live opt-in required`.

They do not qualify live AF in M03-A; no mandatory offline workflow safety case was skipped.
The final actual commands used the following existing tools (fresh TEMP chosen for each run):

```powershell
& 'D:\XianLab\envs\LangChainEnv\Scripts\python.exe' -B -m pytest -q -p no:cacheprovider --basetemp $m03temp
& 'D:\ProgramData\anaconda3\Scripts\ruff.exe' check --no-cache .
git -c core.safecrlf=false diff --check
```

Each of the six new files was separately checked with `git diff --no-index --check -- NUL <file>`;
exit 1 without diagnostics means it differs from the empty file, not a whitespace failure.
The new document's local architecture link resolves. No external-link fetch or CI was performed.

## Exact change scope, independent review and preservation

| Path | Purpose |
|---|---|
| src/aegiscae/research/workflow_rules.py (new) | Typed synthetic protocol, strict fixed definition, rule evaluation and audit reducer |
| src/aegiscae/research/workflow.py (new) | Explicit create/inspect/advance and single-claim effect boundary |
| src/aegiscae/research/project.py | Exact versioned workflow audit/revision integration, unchanged tables/frozen DTO |
| tests/fixtures/synthetic_workflow_port.py (new) | Independent durable TEST fixture effects/queries and injection |
| tests/unit/test_synthetic_workflow.py (new) | W acceptance, races, hard exits, negatives and separate-process continuation |
| tests/architecture/test_fixture_evidence_policy.py | Exact helper allowlist and unapproved fixture negative |
| tests/architecture/test_package_skeleton.py | Exact two modules, wrong-location workflow rejection |
| tests/architecture/test_research_boundary.py | Exact Project helper SQL and AF/process/second-store negatives |
| docs/architecture/M03_SYNTHETIC_WORKFLOW.md (new) | Implemented data/protocol/compatibility/limits |
| docs/milestones/M03-A_DELIVERY_REPORT.md (new) | This scoped evidence and risk record |

Independent native reviewer `/root/m03_review` is read-only and owns no implementation files.
Its early review found no mandatory schema blocker or duplicate-accept path; it required
separation of synthetic eligibility from mandatory real V2, hard constraints from objective
miss, live candidate rechecks at CLAIM/DECIDE, query-only post-claim behavior and deterministic
decision replay. All are explicitly implemented. It requested expanded fault/tamper/race tests.
Independent Reviewer executed workflow tests plus test_research_boundary.py in its own fresh
TEMP: **104 passed in 387.57s, zero skipped/failed**. It independently verified the interpreter,
kept live flags disabled, made no repository edits and found no blocking code/guard/test issue.
It supports scoped acceptance conditional on the final full regression and document closeout.
After the final full regression, its read-only review of both completed documents returned
**no blockers**, supporting `M03A_SYNTHETIC_WORKFLOW_PASS`. It confirmed the distinction between
the independent 104-case run and the full 560-pass run, the retained live skips, ten-file scope,
UNKNOWN and journal limits, synthetic scientific claims and M03-B proposal-only boundary.
Reviewer has stopped; no further source or test changes were requested.
Preservation comparison confirms
76 of the original 80 non-ignored files byte-identical; the four scoped existing modifications
and six new files are exactly the table above. README, .gitignore, all M01 files, frozen
contracts, old ADRs, baselines, prior functional tests/reports and the excluded review patch
remain unchanged. Index empty, original Checkpoint retained; no commit/push/CI.

The three root-anchored exclusions still match Kickoff_Docs, CAE models and .codex/config.toml;
Git tracks none of their contents. Only the explicitly supplied taskbook was read in Kickoff_Docs.
Private-model/credential/runtime areas were not inventoried or hashed. Scoped high-confidence
secret/binary scanning of the ten changed/new paths returned no findings; this is not comprehensive
DLP. AbqJobPilot Develop HEAD remains 7f4b8d8f3a2c862ed8b244d495295f5d51ea0d88, tracked status
clean; historical untracked materials were not scanned. No Stable/production access occurred.

## Remaining risks

| Risk | Boundary |
|---|---|
| Files + DB + synthetic effect atomicity | Separate resources; no distributed exactly-once/power-loss guarantee. Claim-before-effect may deliberately strand a held slot. |
| STORE_BUSY | Blocks reads too; preserves journal and requires separate administrative approval. No recovery or refund API. |
| Trusted local fixture / same user | Typed provenance is not cryptographic AF authentication or OS isolation; direct trusted Python can bypass a facade. |
| Scientific validity | Arbitrary synthetic response table; real V2 not run, V4 not assessed, model NOT_ABAQUS_QUALIFIED. |
| New frozen criteria / old readers | No silent rebind/migration; old binary rejects new event; stale workflow blocks and retains exposure. |
| Bounded storage/performance | Single Project audit replay, 1024-event and 64-MiB limits; not a scheduler or scalable distributed service. |
| Historical private material | M01-B/C retained credential/runtime risks unchanged; files not opened, reused, copied or cleaned. |
| Historical documentation | README and earlier authority/phase reports retain original wording; current capability requires this scoped report. |

## M03-B proposal — real AF TEST_ONLY integration, NOT IMPLEMENTED

1. Separately approve and audit the exact AF revision/public APIs, fresh TEST_ONLY/Fake Project,
   at most one owned lifecycle and bounded two-Fake-run evidence preparation. No production
   Project, existing retained credentials, real Solver, Standard or ODB permission is implied.
2. Define an explicitly different AF_TEST_ONLY execution/evidence binding with actual Project,
   instance, owner, original request namespace/key, Plan/Run/Receipt identities and digest semantics.
   Do not relabel M03-A synthetic IDs or reuse its fixture Oracle as authenticated evidence.
3. Review whether current public AF TEST APIs support two scoped plans/requests and reliable
   idempotency/original-key receipt lookup. If not, report the backend prerequisite; never reach
   private Store/Operator or silently add AF writes through the seven-tool MCP interface.
4. Retain intent-before-effect, one claimant, original-key query and UNKNOWN hold. Use M01's actual
   read bridge only for genuine authenticated IPC reads; trusted fixture provisioning is a
   separately authorized write phase. Two stores do not create a cross-system atomic transaction.
5. Acceptance must independently count actual TEST runs/receipts, test lost acknowledgement,
   mismatched identities, stale owner, competing coordinators and no duplicate execution. Verify
   lifecycle exit via retained owned-process evidence and document credential retention separately.
6. Any AF Fake success remains non-physical. Keep real V2/V4 unresolved and no auto Codex Turn
   continuation, MCP writes or M03-B implementation without new explicit approval.

Stop after the final M03-A report and await architecture review.
