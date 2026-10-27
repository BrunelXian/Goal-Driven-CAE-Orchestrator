# M01 Agent-first Evidence Bridge contract

Status: accepted M01-A offline implementation scope, 2026-10-28. This document is a
read-interface contract, not a real execution permission or a runtime qualification
report. See [ADR-003](../adr/ADR-003-codex-native-delegated-execution.md),
[ADR-004](../adr/ADR-004-execution-evidence-research-verification.md), and the
[current authority register](CURRENT_AUTHORITY.md).

## Public facade and single integration seam

`EvidenceBridge` exposes exactly seven read operations. Each receives an explicit
Project binding; none obtains a default Project from CWD, GUI Recent, directory
scanning, or an implicit creation routine.

The only admitted AF import is the lazy
`from abqjobpilot.service_discovery import discover` inside `_discover` in
`src/aegiscae/adapters/abaqus/af_evidence.py`. Discovery returns a client, context,
and health view. The bridge keeps the client private and uses fixed method calls.
Every public read performs discovery again; no client or owner identity is cached
between calls. Construction stores the supplied discovery function or the default
lazy wrapper; it does not import AF or connect to anything.
Synthetic discovery/transport doubles are used for all M01-A tests. No actual
discovery, Project connection, or Supervisor startup is authorized in M01-A.

| GD-CAE operation | Existing AF read | Required behavior |
| --- | --- | --- |
| `capabilities(binding)` | `discover` and `health` | Confirm explicit identities and read availability; advertised write operations never become permissions |
| `list_runs(binding, cursor=None, limit=32)` | `project_view(before_row, limit)` | At most 32 rows; retain source read time and descending keyset cursor; successive pages are not an atomic snapshot |
| `get_run(binding, run_id)` | `run(run_id)` | Whitelist execution/provenance fields and verify requested identity; do not return the raw Run |
| `get_receipt(binding, key)` | `receipt(key)` | Query the supplied original business key; AF's receipt identifier is `request_id`; no resubmit or key replacement |
| `list_events(binding, cursor=None, limit=64, run_id=None)` | `events(after_sequence, limit)` | At most 64 raw events; optional Run filter applied after reading; ascending exclusive-after Project sequence; advance by the raw page's high-water mark |
| `get_validations(binding, run_id)` | `validations(run_id)` | Source is unpaged; all records must fit bridge limits or the read fails as unavailable/incomplete |
| `get_diagnostic(binding, run_id)` | `diagnose(run_id)` | Return only selected recorded fields; no current OS-liveness or full-artifact assertion |

`validations` reads existing records. `validate_run` creates a new validation and
is forbidden. `export_diagnostic` writes a file and is forbidden. Submit, Grant,
dispatch, service start/stop, recovery Apply, private Store access, and generic
`call(operation, ...)` are outside the facade.

## Binding and read-envelope semantics

A binding must identify the explicit local Project root and expected Project,
instance, context, and owner identities. The root is connection input, not a field
to echo into the public read result. Identity mismatch, stale owner, unsupported
format, unavailable credentials, or failed discovery must return a typed failure
without fallback, repair, or automatic restart.

The DTOs are defined in `src/aegiscae/contracts/af_evidence.py`:

| DTO | Fields and meaning |
| --- | --- |
| `ProjectBinding` | `root` (excluded from repr), `project_id`, `project_instance_id`, `context_digest`, `owner_id`; all source identity expectations are explicit |
| `SourceIdentity` | `project_id`, `project_instance_id`, `context_digest`, `owner_id`; identifies the authenticated read source |
| `ReadCursor` | `source`, `operation`, `position`; continuation is bound to that identity and operation |
| `ReadError` | Safe `code` and `stage`; no arbitrary exception message or traceback |
| `ReadEnvelope` | `schema_version="gd-af-read-v1"`, `operation`, `source`, `read_at`, `completeness`, `consistency`, `data`, optional `source_read_at`, `next_cursor`, `more_possible`, `error` |

`root` accepts an explicit local Windows absolute path and rejects UNC paths and
`..` components. This lexical contract is not a replacement for AF discovery's
real filesystem/Project safety checks. A cursor from a different source or
operation is invalid; it cannot silently retarget a read.

Every public result has a versioned read envelope carrying:

- source Project, instance, context, and owner identities, or explicitly unknown
  values when no source was authenticated;
- read/observation time, keeping source read time distinct from bridge observation;
- completeness and consistency flags for the declared scope;
- bounded, method-specific projected data and any continuation cursor;
- typed error information with safe code/stage metadata and no free-text description.

In the implemented envelope, `source` is `None` until all four source identities
have been verified. `read_at` is the bridge's local observation time in
milliseconds; `source_read_at` is retained separately when the AF response supplies
it in Project-view or diagnostic-view metadata. Other current reads do not supply
that field. `completeness` is `COMPLETE`, `INCOMPLETE`, or `UNAVAILABLE` for the declared
scope. `data` contains only projected dictionaries/tuples, never a transport or
client object. The capability projection can report only the constant
`execution_authorized=False`; it cannot grant execution authority.

Successful projections use consistency
`recorded_read; successive_calls_not_atomic`; failures use `no_successful_read`.
Frozen DTO attributes do not make nested dictionaries deeply immutable or turn a
returned projection into persisted research evidence.

Unrecognized Run status values become `None` and mark the response `INCOMPLETE`;
the recognized source value `UNKNOWN` remains recorded as `UNKNOWN`.
Missing fields remain unknown; the bridge must not invent artifact hashes, a common
revision across calls, a successful validation, or a completed process. A read
success describes transport/projection success only, never a research verdict.

## Bounded projection and disclosure

The bridge uses fixed field allowlists, including nested structures. Supported
identifiers, enum values, hashes, counters, and timestamps are checked before
output. Arbitrary unknown nested objects and free-text payloads are not passed
through. Invalid identity, structure, or pagination data causes a typed failure.
Unknown/missing Run statuses, Run revision/time/backend/plan identity, validation
verdict/time/scope/policy/validator identity or version, and event time remain
`None` with `INCOMPLETE`; they do not become success facts.

| Projection | Exact retained data fields |
| --- | --- |
| Capabilities | `read_operations`, `simulation`, constant `execution_authorized=False` |
| Run | `run_id`, `queue_state`, `execution`, `solver_conclusion`, `artifact_validation`, `reconciliation`, `revision`, `created_at`, `backend_id`, `plan_id`, `simulation`, `validation_scope`, `plan_digest` |
| Receipt | `request_id`, `run_id`, `request_status`, `accepted_at`; original key and AF namespace are checked, not returned |
| Event | `event_id`, `run_id`, `project_sequence`, `type`, `recorded_at`; no payload |
| Validation | `validation_id`, `run_id`, `recorded_verdict`, `recorded_at`, `scope`, `policy_id`, `policy_version`, `validator_id`, `validator_version`; `recorded_verdict` projects AF's existing `verdict` |
| Diagnostic | Projected `run`, projected `validations`, `source_recorded_digest`, constant `digest_verified=False`, `artifacts_revalidated=False`, `current_os_liveness_verified=False` |

Validation scope is restricted to the source values `simulation` and
`fixed_standard_dat_only`; neither a recorded `PASS` nor a Solver status becomes a
GD-CAE research verdict. Diagnostic identity/view metadata is checked or placed in
the envelope; raw identity/view/facts objects are not returned.

Run `backend_id` and `plan_id` are required for projection completeness. The
optional `simulation`, `validation_scope`, and `plan_digest` remain `None` when
absent or explicitly null; that absence alone does not mark the Run incomplete.
If an optional field is present and non-null but invalid, it becomes `None` and
marks the Run `INCOMPLETE`. No optional value is inferred from `backend_id`.
`COMPLETE` therefore covers the declared required read fields, not complete
scientific provenance. Any later decision requiring an unknown optional field
must still fail closed, even when the read envelope is `COMPLETE`.
Backend, policy, and validator identifiers must match the fixed source allowlists;
validation policy/validator versions must be nonnegative integers. Missing or
invalid validation provenance remains `None` with `INCOMPLETE`.

Do not disclose credentials, operator tokens, DPAPI containers, private namespace,
complete Grant objects, command lines, environment variables, raw paths, process
image paths, raw exception messages, logs, tracebacks, or arbitrary diagnostic
prose. Needed business keys remain request input rather than a general export.

The source protocol is `af-local-json-v1`. Its audited request/response bounds are
65,536/262,144 bytes. The bridge additionally bounds each raw response's JSON
re-serialization to 262,144 bytes, nesting depth to 12, and nodes to 8,192;
Run/Event pages are at most
32/64 rows and unpaged validations at most 64 records. Exceeding a bridge budget
returns typed `LIMIT_EXCEEDED` with `UNAVAILABLE`, not a truncated partial success.
Before JSON encoding, the traversal counts all dictionary-key and string-value
characters cumulatively and stops above 262,144 characters. The encoded-byte
limit still applies after that early check.
No method silently truncates an unpaged validation result and reports it as
complete. Unknown error
codes/stages are mapped to safe generic metadata, not copied as arbitrary strings.

This is field minimization, not cryptographic anonymization or a same-user security
sandbox. In particular, an ordinary AF credential can address operations not
exposed by this facade. The bridge does not prevent a separately authorized or
malicious same-user process from bypassing it.

## Pagination and consistency

- Run pages use the source `next_before_row` keyset. Source `read_at` describes that
  page's transaction, not the entire multi-page traversal.
  The key must be present: a missing `next_before_row` is `MALFORMED_RESPONSE`,
  not an inferred final page. Explicit null is the source's terminal cursor.
- Event cursors use Project-wide sequence, not a filtered Run's sequence. If a Run
  filter yields no visible rows, advance from the highest raw source sequence;
  an empty filtered page must not be reported as end of history.
  The cursor binds source and operation, not the optional Run filter. Changing the
  filter continues at the same Project position and does not revisit earlier
  events. Unknown event types are omitted while marking the page `INCOMPLETE`,
  even when they would have been outside a selected Run; they still advance the
  raw sequence cursor.
- A full raw page indicates that another read may be needed. Where the source
  supplies no exact `has_more`, do not invent certainty about remaining records.
- No multi-call API composition is presented as an atomic snapshot. Preserve the
  declared consistency of each response and never synthesize a common revision.
- Native validation reads are unpaged. Oversize, malformed, or interrupted results
  return a failure/incomplete result without partial data masquerading as a pass.
- A recorded diagnostic is not a new validation. Its public-body digest is neither
  a signature nor a digest of every original record or artifact byte. Projecting
  selected fields must not present that digest as the hash of the new projection.
  Diagnostic output is restricted to projected recorded `facts.run`, validation
  summaries, and explicit evidence-limit flags. A source digest, if retained, is
  explicitly unverified; diagnostic prose is not exposed.

## Error semantics

| Condition | Required result and prohibited inference |
| --- | --- |
| Wrong Project/instance/context/owner | Identity failure; never reconnect to a guessed target |
| Legacy, incomplete, or unsupported Project/protocol | Typed unsupported/unavailable result; no migration |
| Offline owner, unavailable credential, communication unknown | Unavailable/unknown; no service startup, private database fallback, or repair |
| Receipt `NOT_FOUND` | A failed lookup only; not proof that execution never occurred |
| Malformed or oversized source data | Explicit error/incomplete status; no empty-success or truncated-success substitution |
| Unknown source state | Remains unknown or is rejected; never promoted to Solver/goal success |

There is no implicit retry, resubmission, get-or-create, reconciliation, or recovery
method. Callers must handle a typed read failure without assuming anything about
external side effects.

## Acceptance and deferred compatibility

M01-A uses synthetic data only. Its acceptance matrix covers the exact lazy import
seam and forbidden alternatives; identity/error paths; side-effect-free imports
and construction; 70-run pagination; interleaved and filtered-empty event pages;
malformed/oversized validations; nested sensitive data and exception injection;
health advertising writes; receipt lookup uncertainty; retained architecture
negative tests; and unchanged DOC-001 files.

Actual test counts and commands must be recorded in the M01-A delivery report.
This contract alone proves no test result. Passing offline tests supports
`SYNTHETIC_CONTRACT_PASS` only. M01-B must separately qualify the fixed-version AF
read seam using an explicitly approved isolated no-Solver TEST Project and owner.
M01-C may later expose a reviewed MCP/Skill surface; neither is implemented or
authorized by this contract.
