# AegisCAE Runtime Threat Model

Status: Milestone 0 — threats and planned controls documented; controls not implemented

The future Runtime will protect execution authority, authorization state, source
artifacts, controlled workspaces, generated artifacts, deterministic verdicts, and
evidence provenance. Threat actors include malformed or hostile callers, buggy
interfaces or adapters, compromised tools, stale external state, mistaken operators,
and over-authoritative planners or report generators.

| Risk | Asset | Threat actor | Attack or failure mode | Impact | Planned control | Implementation Batch | Milestone 0 status |
|---|---|---|---|---|---|---|---|
| Command injection | Execution authority and host | Malicious caller or unsafe adapter | Untrusted text becomes a shell command or arbitrary argument | Arbitrary process execution | Typed command plans, no shell strings, allowlisted tools, Unified Executor | Batch 1 and Batch 3 | DOCUMENTED; NOT IMPLEMENTED |
| Public raw launcher bypass | Authorization and audit trail | Interface or library caller | Caller reaches an ungoverned launcher | Unapproved, unaudited execution | No public raw launcher; Runtime public facade only | Batch 1 and Batch 3 | DOCUMENTED; NOT IMPLEMENTED |
| Adapter direct subprocess | Execution authority | Buggy adapter | Adapter creates a process outside Runtime | Control-plane bypass | Unified Executor monopoly and architecture guard | Batch 1 and Batch 3 | DOCUMENTED; NOT IMPLEMENTED |
| Directory traversal | Workspace boundary | Malicious path input | `..` or equivalent escapes an allowed root | Unauthorized read or write | Canonical path validation and fail-closed scope checks | Batch 1 | DOCUMENTED; NOT IMPLEMENTED |
| External absolute path | Workspace boundary | Caller or machine-specific configuration | Absolute path targets an undeclared location | Data disclosure or uncontrolled mutation | Explicit path contracts and configured roots | Batch 1 | DOCUMENTED; NOT IMPLEMENTED |
| Symlink escape | Workspace boundary | Local actor or crafted workspace | A link resolves outside its declared root | Boundary bypass | Resolve-and-contain checks and link policy | Batch 1 | DOCUMENTED; NOT IMPLEMENTED |
| Source overwrite | Source artifact integrity | Adapter, workflow, or user error | A source artifact is mutated in place | Irrecoverable provenance loss | Immutable source, staging, atomic promotion | Batch 1 and Batch 5 | DOCUMENTED; NOT IMPLEMENTED |
| Stale artifact | Artifact validity | Solver lifecycle failure or stale directory | Old output is accepted as current output | False success or wrong conclusion | Attempt identity, timestamps, hashes, provenance checks | Batch 3 and Batch 4 | DOCUMENTED; NOT IMPLEMENTED |
| Wrong-job artifact | Artifact identity | Misconfiguration or concurrent job | Output from another job is associated with this run | Incorrect verdict and evidence | Job/run identity binding and artifact registry | Batch 3 and Batch 4 | DOCUMENTED; NOT IMPLEMENTED |
| Corrupt ODB | ODB validity | Partial solver output or storage failure | An existing ODB is unreadable or incomplete | False acceptance or extraction failure | Abaqus-mediated readability and required-field validation | Batch 4 | DOCUMENTED; NOT IMPLEMENTED |
| Authorization reuse | Authorization integrity | Caller replay | A valid authorization is used more than once | Unapproved repeated execution | Unique, single-use, consumed authorizations | Batch 1 | DOCUMENTED; NOT IMPLEMENTED |
| Authorization expansion | Authorization integrity | Caller or interface | Approved scope is widened after approval | Execution beyond reviewed intent | Bind authorization to immutable plan, tool, paths, and limits | Batch 1 | DOCUMENTED; NOT IMPLEMENTED |
| Report/verdict spoofing | Verdict and evidence authority | Report generator or client | Markdown or client-supplied status impersonates machine PASS | False trust in results | Deterministic verdict records; reports are views only | Batch 6 | DOCUMENTED; NOT IMPLEMENTED |
| Fixture-as-evidence | Evidence classification | Test author or downstream consumer | Synthetic test data is presented as physical evidence | Invalid engineering claims | Default evidence eligibility `NO` and explicit provenance | Batch 2 and Batch 6 | DOCUMENTED; NOT IMPLEMENTED |
| Legacy dependency bypass | New Runtime boundary | Developer or packaging configuration | Legacy package is imported, vendored, or depended upon | Old bypasses become production control paths | No direct dependency; selective extraction behind new contracts | Batch 0 onward | DOCUMENTED; NOT IMPLEMENTED |
| LLM authority escalation | Execution, validation, and evidence authority | Planner/client or prompt injection | LLM executes, validates, or declares evidence | Non-deterministic unauthorized outcomes | LLM remains Planner/Client only; Runtime enforces decisions | Batch 8 | DOCUMENTED; NOT IMPLEMENTED |
| Implicit CWD | Path identity and reproducibility | Process environment or developer assumption | Relative behavior changes with current directory | Wrong-file access and non-reproducible runs | Explicit Context roots; no implicit CWD | Batch 1 | DOCUMENTED; NOT IMPLEMENTED |
| Hard-coded machine paths | Portability and boundary policy | Developer or migrated code | Local repository or Abaqus paths become code constants | Machine coupling and unexpected access | Configuration contracts; architecture scans | Batch 1 and Batch 3 | DOCUMENTED; NOT IMPLEMENTED |
| Post-freeze artifact mutation | Evidence integrity | Tool, user, or later workflow stage | An artifact changes after evidence is frozen | Evidence no longer matches reviewed bytes | Hash ledger, immutable freeze, mutation detection, quarantine | Batch 6 | DOCUMENTED; NOT IMPLEMENTED |

Milestone 0 does not claim mitigation enforcement. Each planned control remains
subject to its implementation Batch, deterministic tests, authorization, and review.
