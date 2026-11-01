# A-only readiness closure — 2026-10-31

Disposition: **OFFLINE_MECHANISM_LIMITED_PASS; REAL_A_NOT_READY**.

This is an offline engineering delivery and a non-executable approval request.
No real Grant, Owner, Solver, ODB, deployment, account/ACL change, installation,
commit or push occurred. D6-P role attestation remains frozen/BLOCKED. Earlier
build_04/B1/D2 UNKNOWN or BLOCKED findings remain unchanged.

## 1. Real-A gates

| Gate | Result | Actual evidence and remaining boundary |
|---|---|---|
| Existing single production execution route | PASS — offline | Public RodProduct preparation, ProductStandardControl, ExecutionService and original Supervisor/StandardBackend remain the only route. No new launcher. |
| Exact decision, one Grant/Plan, one dispatch, denial and replay rules | PASS — offline | Existing authority tests plus new Supervisor-method tests; protected custody and issuance are explicit TEST_ONLY substitutions, not actual HIL or real IPC. |
| Candidate/Plan input identity, frozen load-only model and output scope | PASS — offline | Existing D4–D6 checks rerun; wrong input/entity/material/output/identity are rejected. A real Project/Plan/output tuple has not been provisioned. |
| One A hold, revision, UNKNOWN stop and no B | PASS — offline | GD hold and Project event replay tests; no repeat execution after response loss/worker failure. GD hold is not an AF kernel-validated budget field. |
| DAT/STA/MSG acquisition mechanism | PASS — offline | AF original collector/intent/Run/Receipt/input checks; additive public local read method returns all three byte streams and collector records. |
| Independent V0/V1 consistency and V2/V3 calculation/rejection rules | PASS — offline mechanism only | Strict type-sensitive comparison, independent numerical recomputation and completion-text rejection tested with synthetic bytes. This is not an actual scientific V0–V3 verdict. |
| Actual Solver artifacts and numerical/goal verdict | BLOCKED | No real A run or real DAT exists yet. Pre-run mechanism qualification does not fabricate artifacts. Actual V2 remains NOT_VERIFIED; V3 remains INCONCLUSIVE. |
| Protected Operator identity, runtime and effective rights | BLOCKED | Named proposed accounts could not be resolved; protected roots absent; current token is admin/linked-admin associated. No deployment performed. |
| Protected issuer to research evidence transfer and authentication | BLOCKED | read_real_artifacts is a local file/SQLite reader, not an authenticated cross-principal IPC export. Current protected-state ACL design excludes research readers. Do not share capability or loosen protected-state ACL to bypass this gap. |
| Three-artifact persistent observation and real budget reconciliation | BLOCKED | New verifier is a pure API. Existing observation persistence remains v1, ACCEPTANCE_UNKNOWN stays held, and B is rejected. Receiving DAT alone will not settle the real budget or qualify A. |
| Execution host, original handles, unique Owner and resource conflict qualification | BLOCKED | No native process experiment or host qualification this round. Existing per-store slot rules do not establish host-wide absence of competing Solver work. Earlier host limitations are not cleared. |
| Model engineering acceptance and exact human execution approval | BLOCKED | Model remains CODE_DECLARED/DECLARED_ONLY, with physical scope needing human acceptance. No exact deployed A Plan, protected human decision, or execution approval exists. |

### Implementation and test evidence

Repository starting HEADs: GD main `69b144cea9aecc515e15cc830368972b09258af9`;
AF Develop `7f4b8d8f3a2c862ed8b244d495295f5d51ea0d88`. Existing dirty work was retained.
This turn changed only these source/test files, plus this report:

| Repository / file | Change |
|---|---|
| AF `abqjobpilot/execution/rod_trusted.py` | Add optional `af-rod-owner-artifact-set-v1` envelope containing original launch intent and DAT/STA/MSG bytes, identities and collector records; default old v1 result unchanged. |
| AF `abqjobpilot/product_rod.py` | Add `read_real_artifacts`, a local read-only facade; no new IPC operation or execution authority. |
| GD `src/aegiscae/research/rod_real_verify.py` | Type-sensitive canonical comparison and pure `verify_owner_artifact_set`; no origin/physical-validation promotion. |
| GD `src/aegiscae/research/rod_real_project.py` | Reject bool/integer confusion in INITIALIZE frozen numerical-policy replay. |
| GD `tests/unit/test_aonly_evidence_closure.py` | Synthetic policy/type, identity, hash, completeness, collector/time, text contradiction, oversized input and persisted-observation negative tests. |
| GD `tests/integration/test_aonly_public_chain_offline.py` | Eleven public-method/Supervisor-routing tests, TEST_ONLY fixture Grant and synthetic runner, lost-response replay, worker UNKNOWN, denial and artifact pollution. |

Root cause of type fix: Python dictionary equality accepts `True == 1` and
`False == 0`. Canonical serialization preserves types and prevents altered frozen
policy/candidate/check results from qualifying through that equality. No historical
contract migration was performed. Validator source hashes change; existing frozen
validator identities must not be silently refreshed or historical Projects migrated.

The new artifact-set checks preserve `source_authentication=NOT_VERIFIED`,
`V2=NOT_VERIFIED`, `V3=INCONCLUSIVE`, `V4=NOT_ASSESSED`, `ODB=NOT_VERIFIED` and
`execution_authorized=False`. Matching hashes/timestamps are consistency evidence,
not a signature, a trusted publisher identity, or tamper-proof provenance.

The integration tests do not invoke Supervisor.__init__, serve, native processes,
or socket IPC. They construct a routing shell and call existing `_invoke`/`_work`
methods synchronously. Protected-context qualification is synthetic; the trusted
test framework prepares a TEST_ONLY Grant before a fixture-only issuer adapter
returns it inside the real management transaction. Real qualified/require_decision
logic is retained; real issuer/check_grant and backend execution are substituted.
Public Plan preparation is separately covered by existing D5/D6 tests; the new
test's preparation helper is not mislabeled as full real public IPC acceptance.

Tests used the existing absolute interpreter
`D:/XianLab/envs/LangChainEnv/Scripts/python.exe` (3.12.10), pytest 9.1.0 and
pywin32 312. No shared environment changes. Existing `g3_d6_offline_checks.py`
captured private output and emitted only P1 whitelist counters. Its audit hook is
a regression tripwire, not an OS sandbox. All fixtures used fresh isolated roots.

| Actual run label | Result |
|---|---|
| `aonly-baseline-01` | 187 passed; 0 failed/error/skipped; 26.16 s |
| `aonly-routing-01` | 9 passed, 2 failed: test requested an event page above the public maximum; fixed to use MAX_EVENTS |
| `aonly-routing-02` | 11 passed; 0 failed/error/skipped; 7.45 s |
| `aonly-evidence-v1-20261031-a04` | Final focused worker run: 160 passed; 36.16 s |
| `aonly-regression-gd-01` | 345 passed; 0 failed/error/skipped/deselected; 76.70 s |
| `af-aonly-regression-01` | 199 passed; 0 failed/error/skipped/deselected; 53.47 s |

Final GD selection: D6 a_only/operator; D5 real_preflight/operator; D4
real_verify/real_project/operator; D3 real_evidence; new evidence closure; all
D3–D6 cross_repo_offline modules and new aonly_public_chain_offline module.
Final AF selection: test_d4_rod_trusted, test_d5_rod_preflight,
test_d6_rod_authority, test_rod_preview, test_rod_plan_adapter.
These are related no-Solver regressions, not a claim that every repository test ran.
Counts across runs overlap and must not be summed as unique test coverage.

All reported final runs recorded zero denied native/network attempts. Safe JSON
receipts are retained under the D6 task's `gdcae-m03f1p1-g2long-d6` evidence root;
raw logs remain private. The worker's first run was refused by the output-size
boundary because a synthetic oversized parameter produced an enormous pytest ID.
Short fixed test IDs resolved it; no private/raw log was displayed or deleted.

Ruff passed on all six changed source/test files. Both repositories' `git diff
--check` passed; existing LF/CRLF warnings are not errors. The changed files are
untracked inherited development files or new tests, so tracked diff alone is not
a content audit; their contents were explicitly reviewed. Installed Core and old
candidate wheels were not rebuilt or changed and do not contain this new overlay.

Independent Reviewer: source-level **OFFLINE_MECHANISM_LIMITED_PASS**, no new
blocking code defect identified; actual A stays NOT_READY. Reviewer explicitly
identified the three unresolved boundaries: cross-principal evidence transfer,
persistent real observation/budget reconciliation, and actual OS/host deployment.
Reviewer did not independently execute tests and does not grant execution authority.
Final independent document review also returned **LIMITED_REPORT_REVIEW_PASS**,
with no required correction; it does not change REAL_A_NOT_READY.

Final worktree check: both branches and HEADs above unchanged; both staging areas
empty. GD has 9 tracked dirty files and 79 untracked files; AF has 12 tracked dirty
files and 59,625 untracked files in the current complete inventory. These counts
include inherited material and are not this turn's change list. Nothing was cleaned
or staged. A bounded scan of the six changed source/test files and this report
found zero UUID-pattern/thread-link/private-key-header hits and no trailing
whitespace; this is not a whole-repository secret-scanning claim.

## 2. Concrete Operator deployment approval request

Status: **REQUEST_ONLY / NOT_AUTHORIZED**. Current D6 two-principal human issuer
console design supersedes older single-Operator/named-pipe and three-principal
proposals for this A-only request; old documents remain historical, unchanged.

Read-only host observations in this turn:

- Current process: elevated=false, admin_or_linked_admin=true. It is not accepted
  as an isolated research or issuer principal.
- Exact `GDCAEResearch` and `GDCAEIssuer` account lookups did not resolve. This is
  not a broad account inventory or proof about all possible identities.
- `C:/Program Files/GDCAE Operator` and `C:/ProgramData/GDCAE Operator` do not exist
  in the observed host view. Therefore actual destination DACL/rights are untested.
- No raw SID, host-private identity, credential or capability bytes were printed.
  No account, group, ACL, token privilege or global configuration was changed.

Requested deployment-only scope, to be approved separately and executed by a human
administrator outside the Agent session:

1. On one explicitly selected Windows execution host, create the two named local
   standard-user accounts (or stop for identity review if either already exists).
   No Administrator membership, no service, no changes to existing accounts or
   global security policy. Record actual host/SIDs privately and bind them to the
   installation manifest. Credentials remain human-managed and are never sent to
   the Agent. Current admin-linked identity is not a substitute.
2. Create only the new code/state roots above. Administrator owns code/config;
   SYSTEM/Administrators have full control. Research receives code READ_EXECUTE
   only, with no capability/Project/input/output write or protected-state read.
   Issuer receives code READ_EXECUTE, config READ, and only the exact new private
   state/input/output/audit subtrees needed for AF modification. Inspect every
   ancestor and reparse point. Do not modify existing ancestor ACLs to force PASS.
3. Stage one reviewed, fully hashed AF/GD/runtime snapshot under protected CODE_ROOT,
   including Python, stdlib, DLL/PYD and dependencies; no shared LangChainEnv
   modification or credential copying. Resolve installed dependency/license rights
   before approval. Use isolated no-bytecode startup; Agent-writable imports are
   rejected. Bind the actual `config/rod-a-only.json`, original AF private
   `standard-operator.json`, SQLite, input and output paths, not the old canary
   filenames. Runtime/config hashes are pending and may not be invented.
4. In the issuer context, provision fresh issuer-bound capability only after its
   exact non-execution provisioning operation is reviewed. Do not copy existing
   DPAPI secrets, start an Owner or sign a Grant under this deployment request.
   Test both real identities' read-only effective rights against actual paths:
   research capability read, code/config/dependency write, Project/output write,
   issuer-account/service control must all be denied. Wrong SID and elevated or
   admin-linked issuer tokens must be rejected. Measure ordinary-shell Solver
   access without launching Solver; do not assume OS-wide exclusivity.

Deployment must stop if protected-root import closure or exact identity/permissions
cannot be demonstrated. Actual host lifecycle qualification and a reviewed,
authenticated read-only evidence-delivery path are separate remaining gates; this
request does not authorize a Windows Runner, Owner/Job test or Solver execution.

Risks: administrator bypass is not resisted; the trusted issuer can mutate AF
state/audit (not append-only or tamper-proof); bearer IPC does not attest peer SID;
license access may differ for the new account; old canary tests do not qualify the
actual layout; broad account rights or a writable import root invalidate custody.

Rollback: first disable new intake and unused capability/authorization through the
reviewed issuer mechanism; preserve UNKNOWN holds, Project state and audit. Only
reconcile processes using original known-owned handles under separate authority.
Human administrator may disable only the newly created accounts and restore only
the recorded newly created-root security descriptors. Do not delete evidence,
claim old UNKNOWN cleared, kill unknown processes, or alter existing global ACLs.

## 3. A-only execution approval draft (not executable)

Status: **NOT_READY_FOR_SIGNATURE**. Do not approve this draft as a Grant. After
the blocked gates close, automation should fill the exact private identity tuple
and return one reviewable application; the user need not manually copy IDs/hashes.

Known proposed A parameters from current code:

- Backend `abaqus-standard-rod-cload-v1`; one original Standard execution route.
- Frozen T3D2 axial rod, length 10 mm, area 1 mm², E=1000 MPa, Poisson=0.3;
  fixed node 1 and node 2 transverse constraints. Only node 2 DOF1 CLOAD scalar
  may vary in the declared 0.5–2.5 N family; this application is **A=1 N only**.
- Current code-declared A input: 420 bytes, SHA-256
  `e2f91730b68f3af72b8054bc168d31b72a3f21ae186e899d64ab4b6b761523a3`.
  This is a prospective input identity, not a real executed file/result or physical
  model verification. The actual staged file must match before Plan creation.
- One slot, one CPU, zero GPU, memory 2048 MB, observation bound 300 s, launch
  budget 1. One unique output/scratch identity; no overwrite or automatic retry.
- Goal Node2 U1 at Step1/increment1: 0.019–0.021 mm. Analytical A prediction
  is 0.010 mm; it is not measured and cannot replace actual DAT verification.
- One A budget hold under frozen total maximum two; held UNKNOWN is not released
  or retried using a new key. B is neither prepared nor authorized by this request.

Required exact fields still unbound: selected host and issuer/research SIDs;
protected code/Python/dependency/config/manifest hashes; ResearchProject identity,
frozen bundle and validator hashes, revision and A hold identity; actual AF
Project/instance, Plan ID/digest/scope, prepared input path/hash, runtime binding,
engineering/scratch/output paths, owner identity, request key/nonce, fresh approval
not-before/expiry (maximum 600 s) and dispatch start window (maximum 30 s).
Do not fill missing fields with synthetic identities, historical Plans or a grant
expiry chosen before the real review. GD hold/revision is explicitly reviewed by
the human issuer; it is not automatically enforced as an AF budget field.

The later human decision must be APPROVE_EXACT for that one tuple, or DENY_TERMINAL.
It may permit only the original Plan→Grant→ExecutionService→Supervisor route and
one A run. The owner must recheck input, approval, resource conflict and freshness
immediately before creation. UNKNOWN means query/reconcile, never re-submit or
release budget without evidence. Collect actual DAT/STA/MSG after execution;
independent provenance/numerical/goal review is then required. No B Plan or Grant
may be prepared from the analytical prediction; B requires accepted real A evidence
and a separate exact human approval.

This round ends here. No deployment or real execution follows from this report.
