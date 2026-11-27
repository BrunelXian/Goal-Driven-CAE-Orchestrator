# G2-LONG shared interface contract

Status: implemented offline interface agreement, 2026-10-30. Main owns this file. Existing frozen records are not migrated; real dispatch remains disabled.

| Object | Required binding and authority |
|---|---|
| PlanRef v1 | Explicit AF Project/instance, versioned profile/backend, immutable Plan ID/digest, Candidate/input digest, exact resources/output identity, NOT_AUTHORIZED for inert rod. Public prepare/persist/inspect/reopen, bounded query and conflict rejection. |
| ExecutionBinding | Existing ResearchProject/contract/revision and Candidate chain plus exact PlanRef. Distinguish INERT_ROD_PLAN from FAKE_TEST_ONLY IPC; no fake Grant for an inert rod Plan. |
| EvidenceEnvelope v1 | Explicit source class, Plan/Receipt/Run/attempt/output identities, candidate/input digest, bounded stable read and DAT digest/selector/unit metadata. Raw output bytes stay in deterministic adapters, never general LLM tool output. Fake IPC evidence and synthetic rod numeric evidence remain separate. |
| ApprovalRequest v1 | Immutable exact Plan/input/model/goal, load/resources/paths, one-use limit, validity window, nonce and request version. TEST_ONLY canary decisions are not human consent, real Grant or Operator isolation proof. |
| VerificationRecord | Independently recomputed provenance/numerical/goal statuses, source classification and audit linkage. No real V2 without real Solver evidence; synthetic checks separately labeled. V4 NOT_ASSESSED and ODB_NOT_VERIFIED remain explicit. |

AF owns its persistence and public API. GD-CAE production code must not access AF private Store/SQLite. Fixture setup may use AF internals only in the AF-owned test harness. One ResearchProject has a global two-attempt budget; A/B use distinct explicit AF Projects and a serial policy, without a claim of machine-wide exclusion. Unknown holds allocation and blocks B. Real B is neither prepared nor approved.

Workers may refine field names compatibly through messages; Main records the final actual API here. No generic shell bridge, new orchestration framework, F1 Runtime expansion or frozen-contract rewrite.

## Final concrete implementation

- AF `product_rod.RodProduct.create`, constructor reopen, `prepare`, `inspect`,
  `disconnect` persist inert execution Plans using existing AF storage. GD-CAE
  injects that public object into `RodBridge.prepare_a`; no private AF SQL reads.
- `RodBridge` writes explicit `rod-preview-event-v2` through ResearchProject's
  existing short transactions. Old v1 records are preserved; old readers reject
  unknown v2 rather than silently migrating them. Mixed v1/v2 writes are refused.
- The tolerance map contains displacement_mm, stress_mpa, reaction_n, balance_n
  and zero_mm. Cross-product testing found the original three/five-field
  mismatch; serialization now includes the same existing balance and zero rules
  already used by the independent Core verifier. No frozen threshold changed.
- AF `rod_evidence.read_synthetic_dat` confines bounded stable reads to the
  registered test artifact and verifies metadata/digests. Core `verify_envelope`
  independently parses and recomputes numerics; neither consumes the other's PASS.
  Future-real source schema validation is not authenticated real acquisition.
  `read_real_dat` remains fail-closed.
- AF `rod_review.request_approval` binds the exact composite frozen contract
  digest as goal_digest and frozen input digest as model_digest. Its local
  TEST_ONLY canary control exercises approve/reject without a real Grant.
- AF-owned `FakeRehearsal` supplies a distinct Fake PlanRef. Core commits its
  intent before start/submit and requires exact ordered events, Receipt, Run,
  Validation, input identity, import-origin consistency and owned closeout.
  B's Fake predecessor check also acquires the original A Owner lock; a claimed
  exit boolean while A is alive is insufficient. This is not global host locking.
- Installed-source A observation supports a current Main custom-Inverse scalar
  suggestion and deterministic B admission. That admitted B has no inert real
  Plan, binding, Grant or execution. Native labels/digests do not confer authority.
