# G2-LONG progress

Date: 2026-10-30. Status: COMPLETE — PARTIAL_WITH_ACTIONABLE_GATES; stopped for architecture review. Real A/B NOT_RUN; public release NOT_AUTHORIZED.

## Entry evidence

- GD-CAE main at 184245cc8a67859484406d70fb1e2d1cf2e347c7; G1 4 modified + 26 new files retained.
- AF Develop at 7f4b8d8f3a2c862ed8b244d495295f5d51ea0d88; G1 2 modified + 7 new files retained.
- Both indexes empty. Exact G1 whitelist content hashes saved before edits.
- Task root: `C:\Users\wuxia\AppData\Local\Temp\gdcae-m03f1p1-g2long-20261030-060116`.
- Root ancestry checked for symlinks/junctions before creation. Entry snapshot: `g1-entry-snapshot.json`.
- Selected existing interpreter: `D:\XianLab\envs\LangChainEnv\Scripts\python.exe`, Python 3.12.10, pytest 9.1.0, PyYAML 6.0.3, pip 25.0.1. Ruff 0.12.0.
- setuptools/wheel absent from that environment. First dependency probe failed on missing setuptools; bounded inventory confirmed absence. No install or shared-environment change performed.

## Exclusive ownership

| Owner | Writable scope | Status |
|---|---|---|
| AF Engineer | AF Develop product/execution profile, public adapter, HIL interface, corresponding tests and new G2 documentation | Inert product/HIL/evidence implemented; Fake IPC integration testing |
| Core/Verification Engineer | GD-CAE research adapters/verifier and corresponding unit tests; new Core G2 architecture documentation | Versioned bridge/evidence implemented; focused tests underway |
| Product Engineer | GD-CAE plugins, marketplace, four roles, README, installer/doctor/initialization, distribution tests and current product documentation | Source complete/stopped; 41 focused passed; CLI auth blocked; final snapshot pending Main freeze |
| Main | Shared cross-repository integration tests, privacy runner, interface contract, milestone reports, canary isolation audit, authorization draft and final assembly | Active |
| Independent Reviewer | Read-only; current G2 sources, boundaries, final evidence | Active |

Workers must not edit another owner's files. Main owns any shared architecture-test allowlist adjustment after explicit coordination. No worktree, staging, branch change or history cleanup.

## Work packages / next actions

- A/B: agree minimal public PlanRef / ExecutionBinding / EvidenceEnvelope / VerificationRecord, then implement persistent inert rod and isolated Fake IPC seams; no Standard execution.
- C: exact TEST_ONLY approve/reject and canary-only isolation inspection. Real Operator isolation and consent remain unverified.
- D: package closure and four actual custom-role probes; Desktop activation is separate and may need human action.
- E: build explicit source allowlist snapshots, install outside the development checkout, run no-Solver rehearsal, prepare candidate and non-executable real-A request.
- Final: freeze source hashes, enumerate disjoint node IDs, run applicable regression, independent review, privacy/diff/process closeout.

## Current dependencies

- Entry verification complete: P1 privacy 34 passed (1.38 s); Project/import smoke 66 passed (4.38 s), both exit 0.
- HIL actual same-user canary complete: non-elevated parent/child have the same Windows process user; child could read capability and read/write code canary. Owned child exited 0. No real secrets or ACLs accessed/changed. `HIL_ENFORCEMENT_NOT_VERIFIED`; see `docs/architecture/7D_G2_HIL_BOUNDARY.md` for the single deployment request.
- Product reports current local CLI 0.166.0-alpha.5.1; this supersedes G1's measured version only for this run. No CLI Main smoke started yet.
- Main added explicit node inventory on top of unchanged P1 capture: 7 boundary cases passed (0.78 s), including sensitive/duplicate/foreign-node rejection. Final regression will prove node union and disjointness, not merely sum file counts.
- Two new Core module paths added to the exact architecture allowlist; 38 package/dependency/private-access/execution guards passed (3.34 s). No broad rule relaxation.
- Product focused result: 40 passed (7.92 s). Initial fixture aliasing error retained and fixed. Actual fresh temporary venv installed an original fixture wheel offline and confirmed installed origin/resources; final product snapshots still pending freeze.
- AF inert product/HIL/evidence result: 40 passed (21.562 s), no Owner in that test selection. First Fake IPC test failed before Owner startup because the wrapper used nonexistent output_key instead of the existing output_policy; corrected with no-Owner construction coverage and retained failure evidence. Live retest pending.
- Main canary/inventory helper Ruff: exit 0, no findings.
- Product final: 41 passed, 0 failed/skipped (8.06 s); three source files Ruff exit 0, both Skills validation exit 0. Real package closure test added after detecting the scanner's own literal URL-pattern false positive; actual private URL rejection retained.
- The single independent CLI Main smoke ended `PENDING_TEST_AUTH`, exit 1, zero custom-role spawns and zero completed Turns. One thread/Turn start event occurred; no IDs or raw JSONL copied. Owned CLI and its one observed descendant exited; zero survivors, no timeout/overflow/unknown cleanup. No auth/global fallback. This does not prove custom-role loading or Desktop activation.
- Core first focused run: 127 passed/3 failed; duplicate-phase proposal guard fixed and two store-error test expectations aligned with the existing public wrapper. Follow-up 130 passed/0 skipped (11.08 s). Further versioned schema checks are still in progress.
- AF first live correction reached and normally closed A, then B setup failed because a fixture directory was used instead of the actual AF Project root. No unknown process remained; exact context-root correction and new-scene retest pending. Prior failure records retained.
- AF live-3: 73 passed (72 offline + 1 explicit Fake live), 21.312 s, zero failures/skips/errors. A and B each used one serial Fake-only Owner, normal exit 0 and signaled native handles. These source-based results are not installed-package proof.
- Core expanded focused: 158 passed (82 new + 76 G1), zero failures/skips, 11.86 s. Versioned future-real schema checks still cannot authenticate source or grant real V2.
- Four current Main actual custom types completed native probes; see `7D_G2_NATIVE_CUSTOM_ROLE_PROBES.md`. No default substitute. Overall new-install role gate remains PARTIAL because the fresh CLI scene is auth-blocked; Desktop NOT_TESTED.
- Main is implementing installed-snapshot rehearsal and public cross-repository tests; no additional Owner has been started by Main yet.

- Build dependencies missing in selected environment: packaging must use only audited available local resources or explicitly record a partial installation result. No network dependency download.
- No permission to deploy OS identities/ACLs, change global Codex configuration or approve real execution. Block only the dependent branch.

## Recovery

On interruption, verify the current source snapshot and task-owned processes before continuing the unfinished package. Do not recreate roots, replay unknown submissions or rerun all completed work. History reports and private credentials remain outside read/copy scope.

## Integration checkpoint — installed snapshot complete

- AF final applicable regression: 300 passed, 0 skipped/failures; 42 owned handles across 30 lifecycle records exited/signaled (32 exit 0, 4 intended exit 77, 6 expected rejection exit 2). AF changed-file Ruff: 9 inherited findings, 0 new versus HEAD; diff check 0.
- Core final focused run: 162 passed. Cross-repository integration exposed a real tolerance contract mismatch (3 versus 5 fields); Main added the existing balance/zero thresholds to the serialized tolerance map. Core+cross then 98 passed/1 test assertion mismatch; exact idempotent replay assertion corrected and 13 cross-repository tests passed.
- Product final focused run: 43 passed. Snapshot export initially rejected the necessary AF source file local_credentials.py by name; an exact product+path exception retains digest/stable-read/content checks and eight rejection cases. No credentials copied.
- build_02 exported GD58/AF57 allowlisted files, installed two reviewed local wheels into a fresh task-only venv with no index/dependencies/build hooks. Independent imports came from the installed site-packages. Installed initialization verified distribution RECORD hashes.
- Installed-snapshot Fake rehearsal PASS: inert rod Plan persisted/reopened, separately identified Fake IPC A completed and closed normally, separately generated SYNTHETIC_DAT read through AF public stable evidence API and independently recomputed. Real A/B NOT_RUN, Grant NOT_ISSUED, real B Plan NOT_PREPARED. Separate-process read-only Project reopen matched the saved summary.
- Reopen capture wrapper initially used an incorrect dictionary key after child completion; corrected only the invocation and repeated read-only reopen successfully. No Owner or write replay occurred.
- Full GD collection safely blocked before output/storage of node identities; Core owns diagnosis and narrow inventory fix, then disjoint full regression. P1 boundary unchanged.
- Remaining: complete full regression/source freeze, native suggestion on installed A evidence, final Reviewer, exact manifests and NOT_READY real-A request. HIL deployment, fresh CLI authentication, Desktop activation and public license/ref remain blocked.

## Final regression in progress

- Collector root cause: 5 existing parameterized nodes exceeded the original 512-character node bound; after safe projection, the full inventory also exceeded P1's 64KiB record decoder. The G2 helper now projects only AST-whitelisted file/function + per-function ordinal to bounded JSONL, keeping parameter text in memory only and retaining P1 unchanged. 18 synthetic boundary cases passed. No private value was output.
- Final collection: 1125 nodes / 43 files. Four file-disjoint groups cover 282/281/281/281 nodes. 95 src/tests Python files frozen; final proof will compare before/after hashes and exact union.
- First completed group: 261 passed / 20 skipped, 169.45s. Skips are old explicit live opt-ins (M01B one, M03B nineteen); no unclassified skip. Other groups still running.
- Whole GD Ruff: exit0, zero findings. Both Git diff checks exit0. New-doc bounded privacy scan: 8 docs, zero private-ID/token-pattern matches; historical body not read.
- Current Main custom Inverse independently derived 2N from installed synthetic A; installed Core admitted scalar with current causal/contract/revision bindings. No B Plan/Grant/binding/execution. Native response status did not grant authority; receipt separate from original rehearsal.
- Reviewer rehashed 115 snapshot files and examined collector/privacy, native admission and NOT_READY request. No new P0/P1/P2; final test counts still pending.

## Final handoff

- Completed all bounded offline work packages; no pending automated test/process. Final report: `7D-E2E-G2_LONG_DELIVERY_REPORT.md`; non-executable real-A draft: `REAL_A_AUTHORIZATION_REQUEST.md`.
- First full GD run 1103 passed / 1 failed / 21 skipped over1125 nodes, unchanged95-file source/test freeze. Failure was three validated string replace calls misclassified as file writes. Main added exact AST block recognition and 1 positive/9 negative tests, without changing production or package bytes. Affected file14/14passed;1135-node collection and two-freeze transition prove1114passed/21skipped/0unresolved failures. This is full run + affected-file revalidation, not a second full green run.
- AF final300passed. AF all-run fixture accounting51ownedhandles/39lifecycle records exited; installed rehearsal adds1normalexit. GD regression parents/children, canary and CLI owned processes closed; no unknown cleanup.
- Final GD Ruff zero findings; both diff checks0; AF9 inherited findings, zero new. Independent Reviewer accepted source, package115files, privacy boundary and exact guard correction; no newP0/P1/P2, no claim of independent test execution.
- build_02 contains independently hashed GD/AF archives/wheels, installation/rehearsal/reopen/native-admission receipts, four operating/release instructions and supplemental manifest134files. Installation verified actualsite-packages/RECORD; dependency environment reused. No actual uninstall/cleanup.
- Both baseline branches/HEADs unchanged; indexesempty. GD50 cumulative reviewedfiles (22G1unchanged,8extended,20G2new/adjusted), AF18. Five unrelated GD untracked historicalitems preserved. No commit/push/publication.
- Gates remaining: independent protectedOperator deployment, authenticatedreal source and controlledStandard dispatcher qualification, finalreal AProject/resource tuple, freshCLI authentication/custom-role proof, Desktopactivation and release license/ref. RealA/B NOT_RUN; realGrant NOT_ISSUED. CurrentMain fourcustomroles and native2N scalar admission do not satisfy these gates.
- Exact next authorized action: architecture review of this delivery and NOT_READY request; no auto-run, auth retry, newMain, BPlan or F1 work. At mostthreehuman actions are consolidated in the request/report.
