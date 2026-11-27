# M03-B: real AF TEST_ONLY IPC composition

This milestone composes the existing fixed A/B coordinator with a trusted test
adapter. It adds no product executor, workflow state, contract schema, public API,
MCP tool, Agent harness or automatic continuation service. The implementation lives
in `tests/integration/m03b_support.py`; all `src/aegiscae` files remain unchanged.

## Authority and persistence

The trusted fixture setup is the only place that constructs AF ExperimentStore,
ExecutionService, plans and TEST_ONLY grants. It prepares exactly two immutable
`fake-v1` plans with separate `.txt` inputs, job IDs and exact grants. Plan action
is `emit_fixture_result`; no Standard/process-fixture configuration is supplied.
It reuses the existing AF ProcessHarness launch/identity/cleanup implementation.

Every case gets a new directory beneath a newly named direct child of user TEMP.
The manifest records interpreter, child paths, backend, process limits, finite
deadline and cleanup strategy before launch. Launch and port reads/submission
check that deadline. No historical root, credentials or project is reused.
There is one owner invocation per case, with no owner replacement or restart.

`provisioning.json` freezes the two AF requests/plans and namespace before launch.
After health confirms the newly owned endpoint, `mapping.json` also freezes that
exact endpoint, project/instance/context, original keys, candidate IDs/digests,
frozen research references and oracle digest. Only then is the unchanged workflow
created. Its `syntheticport_` source ID derives from the mapping hash. This also
prevents accepting a replacement owner merely by editing owner-binding.json.
All mapping/oracle/definition files are exclusively created, never upgraded in place.

These sidecars are **test-harness persistence**, not a new ResearchProject schema.
Original ResearchProject audit, Candidate, reservation, intent, CLAIM, receipt
projection and decisions remain in the existing SQLite store. Sidecars link that
store to AF originals; they are required to reattach the test port after reopening.
No production AF execution binding API is delivered. Old schema/contract bytes and
historical ADRs are untouched. SHA-256 detects ordinary inconsistency; it is neither
a signature nor protection against coordinated rewriting by the same OS user.

## Sources and identity

| Record | Source / meaning |
|---|---|
| AF Receipt `request_id` | Actual authenticated acceptance in original namespace/key |
| AF Run/phase/Plan | Actual Fake run and phase, separate from synthetic attempt ID |
| AF Event/Validation/Observation | Recorded simulation execution and JSON artifact evidence |
| SyntheticReceipt | Local admission projection after the full AF completion gate |
| Oracle metric | Immutable `TEST_ORACLE`: A=2 mm, B=0.5 mm, no solver measurement |
| Local BudgetLedger | Existing synthetic test accounting; not AF Grant authority/consumption |
| DecisionRecord | Existing deterministic evaluation under unchanged frozen test criteria |

The mapping binds the full AF normalized submission digest independently of the
SyntheticRequest digest. AF receipt namespace is checked exactly but not published
in delivery reports. Synthetic receipt/attempt/evidence IDs retain their distinct
prefixes; no AF identifier is passed off as one of those synthetic identities.

BudgetLedger's historical `grant_consumed=false` describes its local synthetic
observation vocabulary; it does **not** mean AF did not consume its exact TEST grant.
AF facts remain in their own namespace. Neither reservation nor test projection
authorizes Abaqus execution.

## Read-only evidence path

The test adapter calls the unchanged GD-CAE EvidenceBridge. A seven-read-only-method
wrapper captures the original return values of the Bridge's actual client calls;
discovery is the real project-scoped authenticated AF discover function. It checks
the exact owned endpoint and fresh fake-only/open-dispatch health on every read.
It has no Store, submit, grant, owner or generic RPC interface.

This capture is necessary because the public Bridge deliberately omits namespace,
phase and some validation references. Seven MCP contracts and their redaction
behavior remain unchanged. The test-only raw archive contains more information
than the MCP projection and is kept only in the newly owned test directory.
It is not exposed to Codex as an eighth tool.

The gate requires COMPLETE envelopes with exact source identity, original Receipt
key/namespace/normalized digest and matching Run Project/instance/owner, Plan/digest,
Grant/job and phase. It requires FINISHED, COMPLETED, VALID, simulation, NOT_RUN and
reconciliation NONE. Four events must occur in order: REQUEST_ACCEPTED, START_INTENT,
FAKE_COMPLETED, VALIDATION_RECORDED. A bounded unfiltered event page must be complete
and contiguous from sequence 1. This exact two-run fixture never needs general paging.

Validation must be PASS under fake-result-v1/fake-json-validator v1 in simulation
scope, bound to the same Run/phase and diagnostic Observation. The observation's
digest must equal AF's deterministic Fake JSON generated from the immutable Plan
and Run identities. Diagnostic run, receipt, plan projection, events and validations
are cross-checked with the independent original reads. Missing/contradictory data,
partial pages, unknown dispatch, stale endpoint or an unavailable owner cannot pass.
Successive calls are not an atomic AF snapshot; consistency checks do not claim one.

## Candidate input equivalence

Before launch the fixture uses the existing typed scalar editor and independent
mutation checker to prepare two predicted input copies: LOAD_N 20 and LOAD_N 30.
Each AF Plan pins its own supported `.txt` path, size and SHA-256 digest. The workflow
later publishes actual Candidates through the unchanged Mutation Guard.

Before submission and after evidence reads, actual Candidate bytes and the Plan's
input copy must both match the immutable Candidate digest and manifest. AF itself
checks the input manifest at acceptance and dispatch. The recorded validation and
artifact digest bind the Fake output to that Plan's input digests.

The supported conclusion is `PROVEN_BYTES_AT_CHECKS`. The two paths are distinct
copies with identical bytes at those checks. FakeBackend echoes digests into bounded
JSON; it does not parse or solve the engineering model. This proves neither general
Abaqus input support nor numerical/mechanical processing, and does not eliminate
malicious same-user file replacement races between checks.

## Advancement and failure semantics

The existing coordinator publishes/rechecks a candidate, reserves budget and commits
intent/CLAIM before any port accept. The adapter independently checks the committed
state and writes an exclusive per-step submission ticket before one IPC submit.
For B it also checks A's committed valid synthetic target-miss decision. Only the
new CLAIM winner reaches submit; subsequent actors and reopened processes query.

The submit response is never used as workflow evidence. Query reads the original
key through the Bridge and returns a synthetic admission projection only after the
full terminal Fake evidence gate. This conservative policy keeps a unit held while
acceptance/completion is unresolved. An accepted-but-invalid Fake run can remain
locally UNKNOWN/held rather than charged; quota is not reclaimed. Administrative
settlement is deliberately outside this milestone.

After a valid projection the existing local ledger charges once. The independent
oracle is checked against its frozen hash and exact Candidate/step/frozen selectors,
then supplies only synthetic metric values. Missing evidence at DECIDE is terminal
BLOCKED. B requires both A's valid AF completion and committed valid synthetic miss.
Real V2 stays NOT_RUN, V4 NOT_ASSESSED, real Goal INCONCLUSIVE.

Hard exits separate committed research intent, claim, actual AF acceptance, receipt
binding, charge, evidence, decision and B admission. There is no distributed transaction.
A crash after CLAIM but before IPC sacrifices liveness: it stays query-only even if
AF has no receipt. NOT_FOUND never grants a retry or refund. Effects are exactly once
**observed in the tests**, not a distributed exactly-once guarantee.

Cleanup runs even after failed assertions. Each coordinator child is registered at
Popen, its actual Python host identity is matched to the launcher and retained by a
Windows handle before it proceeds. Owner handles come from the unchanged trusted AF
harness. Shutdown first requests graceful exit; all host/launcher exits are recorded.
Unresolved child handles are not discarded. Cleanup failure blocks later cases;
forced owner fallback, if ever needed, invalidates a clean PASS. Existing journals
are retained and cause JOURNAL_BLOCKED, never automatic repair.

## Next boundary

M03-C may let Codex Main propose the already bounded B scalar using verified A
feedback and native specialist/reviewer delegation. Proposal must still pass the
same frozen contract, mutation and budget guards and a separate approval of any
new test setup. Keep real Fake evidence and synthetic metrics separate. Do not add
solver access, automatic original desktop-thread wakeup, a general Agent framework,
MCP write tools or Standard multi-plan support as part of that experiment.
