# G1 real rod preview: offline contract boundary

This is a versioned offline prerequisite, **not live execution readiness**.
The only accepted source is `OFFLINE_AF_SUBSTITUTE`. `AF_REAL` is rejected with
`LIVE_AF_SOURCE_UNQUALIFIED`; a user dictionary containing `managed_scope=true`,
an authorization digest, or `PASS` establishes no real authority or provenance.
Every public view reports `execution_authorized=false`, real goal `INCONCLUSIVE`,
`BLOCKED_LIVE_DISPATCH_UNREGISTERED`, and `BLOCKED_HIL_STRONG_ISOLATION`.

## State and compatibility

`create_preview(new_root, name, RodPreviewContract(...))` creates a **new**
ResearchProject with explicit metadata schema 2. It uses the existing
`research.sqlite3` tables, identity checks, short transactions, revision metadata,
audit hash chain, and versioned workflow-event commit path. Each new Project has
its own ordinary database; there is no additional store type/table, executor,
scheduler, automatic retry, or separate Agent harness.
Schema 1 remains the default; its synthetic contract/mutation/budget rules are
unchanged. Schema 1 cannot enter the preview adapter. Schema 2 cannot freeze a
legacy ContractBundle. No existing Project is migrated. An old schema-1 reader
must reject schema 2, not silently reinterpret it. A schema-2 Project's first
CREATED event contains an exact integer `creation_schema=2`; reopening requires
agreement with metadata. Schema-1 events retain their old format. Recomputing a
metadata digest after simply retagging either schema does not pass this check.

The frozen preview contract is a new `rod-preview-contract-v1` payload in the
Project audit, rather than a fabricated legacy synthetic ContractBundle. It
binds model/profile/baseline, a typed goal interval, units/entity, load bounds,
verification tolerances and exactly two calls. Current model qualification is
only exact-template/offline grammar qualification, not independently measured
physical validation. SHA-256 and local timestamps detect inconsistencies; they
are not signatures, trusted clocks, or tamper-proof security proofs.

## Model and evidence

The source-defined T3D2 rod is 10 mm long, area 1 mm2, E=1000 MPa. Only the node 2,
DOF 1 `*CLOAD` numeric token may differ. Rendering canonicalizes trailing decimal
zeros without rounding. All other bytes, including material, boundary, step and
outputs, match the frozen 420-byte LF template. No include or arbitrary path is
accepted. `candidate_input()` returns immutable bytes for a future approved AF
publication adapter; it does not write an input into an execution workspace.

`RealPreviewAdapter` exposes explicit admission, intent, unknown and observation
operations. It does not expose submit, dispatch, authorize or shell commands.
Intent and allocation commit together before any future sender could act;
unknown and interrupted intents retain allocation. A matching key replays;
conflicting content or stale revision is refused. A total of two distinct
bindings is permitted, with no release/retry API that could hide a third attempt.

Each binding includes AF Project/instance, exact Plan/input/resources/output,
request key and TEST_ONLY authorization evidence. The second attempt must use
distinct Project/instance, Plan, approval, request and output identities. This
tests the identity contract only. Two real AF Project lifecycle/owner closeout
has **not** been proven and remains a G2 blocker.

Observation includes the exact binding, receipt/run/attempt, original DAT bytes
(bounded hexadecimal chunks), output digest and a zero exit declaration. The
independent GD-CAE reader parses the fixed Abaqus 2024 printed layout without
calling AF's parser or trusting its verdict. It requires the exact step,
increment, node/element/integration-point and complete U/RF rows; rejects missing
completion/footer, substituted bytes, wrong units/entities, duplicate tables,
bad numeric values and re-used A output; and checks displacement, stress and
force balance against frozen tolerances. V0–V3 PASS/statuses in this offline
path describe checks of substitute input only; `real_goal` stays `INCONCLUSIVE`.
V4 is `NOT_ASSESSED`; ODB is `NOT_VERIFIED`. A contract requiring either is refused.

B is not present in the frozen contract. It is admitted only after A has a
committed valid observation and `V3=NOT_SATISFIED`. Its proposal binds A Run,
output digest, measured metric, decision digest, contract digest, observed
revision, current revision and creation order/time. A satisfied or unknown A
blocks B. A dictionary saying `reviewer_pass=true` is rejected. The independent
Reviewer may critique this evidence but cannot modify the result or grant rights.

## What is still missing for live G2

Neither changing `source` to `AF_REAL` nor removing a string guard is sufficient.
A separately reviewed public AF adapter must retrieve and cross-check immutable
raw Receipt/Run/Plan/Grant-consumption and artifacts through qualified managed
scope, verify real operator evidence and exclusive owner/closeout, and recheck
input/output files at the actual send/read boundary. Only then may a separate
versioned real-source event be admitted. The same-user Operator capability
problem remains; no OS-enforced human isolation is claimed here. Actual A and B
each require separate exact future human authorization and live acceptance.

Tests use newly generated DAT substitutes and isolated ResearchProjects. They
exercise canonical mutation, denial, stale evidence, unknown replay, response
loss, hard process exit after commit, two-process intent competition, independent
process reopen, and rehashed semantic corruption. They do not run Abaqus or
prove real IPC/solver behavior.
