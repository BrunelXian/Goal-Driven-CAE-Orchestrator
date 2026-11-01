# G3-D4 protected Operator — one deployment proposal

**PREVIEW ONLY. HIL_ENFORCEMENT = BLOCKED. No account, ACL, service, credential,
capability or Grant was created or changed.**

| Decision | Exact proposed scope |
|---|---|
| Research principal | Existing Codex identity, privately mapped by administrator; must not possess the issuer token, administrative elevation or equivalent issuer-code rights during qualification |
| Human reviewer | Proposed distinct non-admin `GDCAE_Reviewer`; reviews the immutable tuple and records an explicit Approve or terminal Deny; no issuance capability |
| Issuer | Proposed distinct non-admin `GDCAE_Issuer`; runs the existing AF Owner/authority under reviewed protected code; no second Solver Owner |
| Code | `C:/Program Files/GDCAE Operator`; deployment admins/SYSTEM control updates; runtime subjects cannot write code or resolve imports from writable development directories |
| State | `C:/ProgramData/GDCAE Operator`; config read-only to issuer/reviewer; DPAPI capability usable only under issuer; audit append by issuer, no research delete/write |
| Transport | Reviewed local AF request/status boundary authenticates Windows token; caller role, LLM text and raw shell parameters are not authorization |
| Startup | Explicit human start of existing AF Owner under issuer after separate approval; no new Windows service proposed or installed here |
| Credentials/license | Issuer-scoped DPAPI provisioned separately; no export into prompts, logs or Agent environment; Abaqus executable/version/license access qualified separately |
| Host | Independent installation/process-lifecycle qualification first; current Codex host restriction remains; no new native experiment here |

The administrator must first approve private SID/group mapping, effective inherited
and explicit rights on every ancestor, code/config hashes, trusted import/search
path, host and rollback snapshot. Those identities are currently **not supplied**,
so this sheet is not an executable deployment authorization. SYSTEM/administrators
are trusted provisioning subjects; administrative compromise or equivalent-token
execution defeats the isolation claim.

`operator_deployment/preview.py` produces and strictly checks a typed non-executable
change proposal. It includes Project/Instance/contract/Candidate/Plan/revision,
input/backend/resources/working directory/scratch/output/deadline/nonce/one-attempt
binding. The existing AF issuer must atomically consume the nonce with the exact
decision. Expiry is bounded to 600 seconds. UNKNOWN holds authority and budget;
changing a Plan, input or resource invalidates approval. This script never issues
a Grant or validates a live human identity.

`operator_deployment/audit.py` prepares fixed-path, read-only AccessCheck queries
under each approved principal. It reads security descriptors, not capability bytes,
and never changes ACLs or impersonates another account. The protected-layout path
was **NOT_RUN** in D4. Only a fresh non-secret canary was measured: current token
not elevated, but administrator/linked-administrator risk present; the current
token has all tested rights on its own canary files. This is actual evidence that
same-user fixtures cannot establish protected Operator isolation.

Post-deployment acceptance must independently demonstrate research cannot read/use
the capability, replace code/config, forge the human identity, replay/extend a
nonce, change an approved Plan, bypass denial/expiry through a general shell, or
delete the audit. Run metadata checks under research/reviewer/issuer separately;
then perform separately approved adversarial endpoint checks. A single AccessCheck
observation, fake denial test or hash cannot establish those guarantees.

Revoke in order: disable new requests; revoke unused authority; reconcile only
original owned execution handles; preserve immutable decisions and evidence; let
the administrator restore the approved previous security state. Never clean up an
unknown historical Owner or erase receipts. Actual deployment and attack testing
require a new explicit approval; no opaque elevation command is provided.
