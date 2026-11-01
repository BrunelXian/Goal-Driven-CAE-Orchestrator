# G3-D3 protected Operator deployment approval sheet

Status: **proposal only; HIL_OS_ENFORCEMENT = BLOCKED_HIL_DEPLOYMENT**.
The existing pure `operator_deployment` validator validates a declared synthetic
permission matrix. Neither its PASS nor a same-user deny test proves Windows
isolation. This document grants no deployment or execution authority.

## Exact deployment proposal

An administrator must approve a separately recorded mapping of research and
Operator aliases to distinct non-administrator Windows principals. Raw identity
values belong only in the private deployment manifest. Administrators and SYSTEM
are trusted deployment authorities, not evidence that an ordinary research user
has write access. Research running with administrative powers defeats this threat
model and cannot qualify. Compromised administrators remain a stated limitation.

Protect reviewed executable code and configuration under a fixed Program Files
root and Operator state under a fixed ProgramData root on the same approved
volume. Reject reparse points and alternate streams. Audit ancestor traversal,
effective group membership, inherited ACEs and explicit rights. Compare installed
bytes against the reviewed, hash-pinned source/wheel manifest. The manifest itself
must have a protected origin; an untrusted SHA-256 claim is not authentication.
Do not grant either runtime principal code/config write rights. Research cannot
read capabilities, invoke trusted Grant/dispatch endpoints, delete audit records,
replace executables or inject modules through environment/search paths.

The proposed local named-pipe endpoint denies remote clients and authenticates
the client's actual Windows token. A client-provided role string is not identity.
It accepts only bounded exact requests, no shell commands or arbitrary paths,
and returns sanitized receipts belonging to that requester. Endpoint ACLs, token
binding and protected capability storage require independent deployment tests.

## Human decision and single-use authorization

The human sees Project, frozen contract, candidate and input digests, model
profile/version, scalar/unit, Plan identity/revision, expected output, budget,
expiry, nonce and the single allowed attempt. Changing any bound field requires
a new decision. Denial is terminal. Expiry is at most 600 seconds; nonce use and
decision persistence are atomic. Approval is not an executable capability.
Only a qualified AF Operator may exchange an accepted exact request through the
existing trusted AF authorization path. No agent assertion, synthetic fixture,
receipt label or deployment-template PASS can mint a real Grant.

An uncertain outcome holds the request and budget for reconciliation, with no
automatic retry or fresh nonce bypass. Revocation disables new requests first;
then revoke capabilities, reconcile only owned processes, preserve the audit,
and have the administrator restore prior security state. Never kill an unknown
process or erase historical receipts as rollback.

## Required approval and qualification evidence

1. Approve principal mapping, trusted code/config hashes, exact roots and ACL
   proposal, endpoint identity policy and administrator risk acceptance.
2. Deploy on a separately approved compatible host. Independently verify effective
   rights and demonstrate research cannot modify code/config, steal capabilities,
   forge identity, replay a nonce, bypass deny/expiry or delete audit evidence.
3. Verify original-handle lifecycle qualification on that host, exact request audit
   and recovery/UNKNOWN policy. Only then assess a separate real-A authorization.

No commands in this sheet execute installation, grant rights, create accounts,
change ACLs, issue Grants or launch AF. Actual deployed identity, rights, pipe
authentication and lifecycle qualification are **NOT_RUN** in D3. The current
Codex host's Job limitation is not worked around by this design.

The eventual host manifest must pin the Windows build, Python/runtime, approved
Abaqus executable identity/version and license availability without launching a
Solver as a discovery step. Compatibility and real process closeout are currently
NOT_TESTED. The Operator UI must display the exact immutable tuple and distinct
Approve/Deny actions, retain the human decision receipt, and never translate a
view/open action into approval. These are deployment acceptance requirements,
not claims that a protected UI or executable is installed today.
