# Operator deployment approval request — NOT_AUTHORIZED

**Decision requested:** approve or reject the following design. Design approval
does **not** authorize account/ACL changes, deployment, a real Grant or Solver A/B.
No OS change has occurred. `HIL_OS_ENFORCEMENT=BLOCKED_HIL_DEPLOYMENT`.

**Proposed minimum:** one independent, non-administrator local principal named
`GDCAEOperator`; a human-started protected Operator process, no Windows service.
Actual research/Operator SIDs are `PENDING_PRIVATE_ADMIN_MANIFEST`; do not put
SIDs, passwords or capabilities in chat. The current research tool process was
observed non-elevated, but same-user isolation is not sufficient.

| Item | Exact intended boundary / unresolved prerequisite |
|---|---|
| Trusted code | `C:/Program Files/GDCAE Operator`; administrator-installed, research read only, Operator read/execute only |
| Trusted configuration | Same protected installation; Operator read only; no research write or secret access |
| Capability/audit | Separate protected subdirectories of `C:/ProgramData/GDCAE Operator`; capability generated only inside Operator context, never copied/exported; audit append-only to Operator, no research delete |
| Artifact identity | Qualified Operator implementation/configuration SHA-256 **pending**. The G3 static validator hash is not an Operator executable qualification |
| Request channel | Proposed local-only named pipe; actual Windows-token peer check, 64 KiB limit, exact `af-rod-approval-request-v1`, no arbitrary command/path or signing endpoint |
| Human review | Approve/reject exact Project/Plan/input/goal/model/resource/output/nonce/window tuple; one attempt, at most 600 seconds; change/expiry/denial cannot be bypassed with a new key |
| Failure | UNKNOWN keeps allocation and blocks later events; reconcile exact Receipt/Run; stop only known owned process |

**Separate OS-change approval required before any implementation:** after the
private SID mapping, final artifact digests and existing security-state inventory
are ready, explicitly authorize (1) creation of the named non-admin principal,
(2) installation into these two exact roots and protected per-resource ACLs with
unsafe inheritance removed, and (3) one bounded cross-principal canary session.
This request does not authorize those actions now. No service, firewall, registry,
system environment, global Codex authentication or group-policy changes are needed
by the minimum design; any such need requires another reviewed permission.

**Acceptance before real A:** research token must be denied capability read/use,
trusted code/config write, audit deletion and direct Grant/dispatch; actual
Operator token must pass exact review/denial without self-modifiable trusted code.
Inspect inherited/group access and every path ancestor/reparse point. Record
private evidence and publish only bounded results. The offline permission-matrix
tests cannot substitute for these effective-access measurements.

**Rollback to approve together with deployment:** disable request intake, revoke
capability, reconcile/stop the known owned process, preserve all audit/UNKNOWN
evidence, then administrator restores the recorded prior ACL/account state.
No broad deletion, uncontrolled process kill or automatic audit cleanup.

**User choices:** APPROVE_DESIGN_ONLY / REJECT_DESIGN. A later explicit
APPROVE_EXACT_OS_CHANGE_PLAN is a separate decision after the pending manifest and
qualification fields are complete. Real A still requires its own fresh exact
authorization; B is never included.
