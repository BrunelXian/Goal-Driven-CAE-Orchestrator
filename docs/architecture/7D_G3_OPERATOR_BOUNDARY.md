# G3 Operator boundary — offline validation only

The new `research/operator_deployment.py` contains a pure static review contract.
It imports no AF runtime, credential, OS-token, process or IPC implementation and
performs no filesystem access. It does not create a signer, launcher, service,
approval store or alternative authorization mechanism. Existing AF exact approval
request and single-use semantics remain the referenced protocol.

`deployment_review_template(code_digest, config_digest, *, code_root, state_root)`
requires both roots as explicit caller inputs and returns a fresh original
synthetic configuration. There is no default machine drive, CWD or environment
path authority. `validate_deployment_contract(raw)` checks exact fields,
strict primitive types, bounded canonical JSON, synthetic principal aliases,
protected-path declarations, exact resource permissions, local request transport,
one-attempt/600-second maximum approval policy, denial/replay/UNKNOWN policies,
audit and ordered rollback. Its result includes a local contract digest and
`HIL_PROTOCOL=PASS_OFFLINE`; it always retains
`HIL_OS_ENFORCEMENT=BLOCKED_HIL_DEPLOYMENT`, with host identity, installed code,
deployment permission, real Grant issuance and execution authority all false.

This is a new untrusted design-review record, not a modification or migration of
ResearchProject contracts, an AF Grant schema, or the true authorization model.
Even a valid configuration is not proof that permissions exist on the host.
Hashes are consistency references, not authenticated publisher or principal proof.
The validator rejects caller claims that SID mapping, reparse-point inspection or
installed bytes have already been verified. Actual deployment needs separate
authorized measurement, not a new optimistic value in this offline fixture.

## Narrow proposed deployment

Use one independent non-administrator local Operator principal. A host
administrator installs the reviewed implementation/configuration under
`C:/Program Files/GDCAE Operator`; the Operator has read/execute but no write
access. `C:/ProgramData/GDCAE Operator` contains separately protected capability
and append-only-to-Operator audit storage. The research principal may read public
code, but cannot read protected configuration/capability or write trusted code,
configuration, audit, Grant or dispatch endpoints. Administrators retain recovery
authority; this design does not claim to defend against a malicious administrator.

The minimum lifecycle uses a human-started protected Operator process, not a
Windows service or a continuously running new agent framework. A proposed local
named-pipe request endpoint verifies the actual client Windows token, rejects
remote clients, caps payloads at 64 KiB and accepts only the exact
`af-rod-approval-request-v1` object. It does not accept a shell command, arbitrary
input/output path, credential or caller assertion of approval. The operator must
inspect and approve or reject the complete immutable tuple through the qualified
AF mechanism. This document does not implement that endpoint or qualify its
security. Future code/configuration and exact artifact digests remain prerequisites.

| Resource/action | Research principal | Operator principal |
|---|---|---|
| Trusted executable | Read only | Read/execute, cannot modify |
| Trusted configuration | No access | Read, cannot modify |
| Capability | No access | Protected read/use; never export |
| Audit | No direct write/delete | Append only; immutable request digest |
| Request endpoint | Submit exact request/read own sanitized receipt | Serve exact request |
| Grant/dispatch | No access | Qualified AF path only, still not deployed |

The current research SID and proposed Operator SID are not published here. Actual
SID-to-role mapping is `PENDING_PRIVATE_ADMIN_MANIFEST`; no Operator account has
been created. Synthetic aliases in tests are not host identities. The Program
Files/ProgramData paths are the proposed one-host layout, not asserted existing
directories. Runtime validation checks the explicit roots against the abstract
same-volume Program Files/ProgramData layout; it does not hard-code the example
drive or resolve these paths. `PureWindowsPath` validation rejects path escape, UNC/device paths,
alternate data streams and malformed roots; it cannot observe junctions or ACLs.
Deployment must inspect each ancestor and reject reparse points before provisioning.

## Actual host observation and limits

On 2026-10-30 the HIL worker read only TokenElevation and TokenElevationType of
its current tool process: Windows version 10.0, build 26300; elevation false,
type LIMITED. Its token handle was closed. No SID, account name, credential,
DPAPI value, ACL, service, registry or global configuration was read or changed.
The safe receipt is the task root's `hil/host-readonly.safe.json`.

This does not establish another security principal, deny rights, secure IPC,
code integrity or resistance to elevation. G2's same-user canary finding remains
an accepted historical reason to block deployment; this task does not rerun the
same arrangement and claim a stronger result.

## Qualification and rollback

Before deployment is usable, an authorized administrator must resolve the private
SID mapping and qualified Operator artifact/config hashes, inspect effective
rights including inherited/group rights and reparse paths, then test cross-token
denial of capability reads, trusted code/config writes, audit deletion and direct
Grant/dispatch access. Positive Operator review and explicit human denial must
also work. Unknown submit/exit holds the ResearchProject allocation; no new-key
retry or replacement Owner is permitted.

Rollback order: disable new requests; revoke the capability; reconcile/stop only
the identified owned process; preserve audit and unknown Run evidence; then have
the administrator restore recorded prior security state. Never blindly remove
directories/accounts, erase evidence or restore permission inheritance. No rollback
commands are generated or executed in G3.

Targeted synthetic tests and final results are recorded in the G3 delivery
report. They exercise declarations and rejection behavior, not effective Windows
access checks or real human consent.
