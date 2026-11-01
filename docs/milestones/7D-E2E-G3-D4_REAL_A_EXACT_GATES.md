# G3-D4 — exact real-A gates (not an execution request)

**REAL_A_NOT_READY. No executable approval or real Grant is generated.**
Missing identity, host and authority fields below must not be filled using fixtures.

| Field / gate | Actual D4 state |
|---|---|
| GD code baseline | main `69b144cea9aecc515e15cc830368972b09258af9` plus reviewed D4 overlay; not a release ref |
| AF code baseline | Develop `7f4b8d8f3a2c862ed8b244d495295f5d51ea0d88` plus reviewed D4 overlay |
| Internal bundle | SHA-256 `ec81b296d753391ec13dbf0017f12d5f3ad7f8a4e2347b8adb0e711bc61ffde1`; NOT_RUN_EXTERNALLY |
| New GD ResearchProject | Created through the real API in the private D4 root; revision 3, no AF Plan, no Grant, no B |
| Frozen bundle digest | `sha256:74ba06e9c34db518f45c33a5cf41e66fb1b5ed21ec2b85eb8d8d996f95194a38`; read-only reopen in a separate tool-invoked Python process left DB bytes unchanged |
| Frozen goal | U1 at node 2 / Step1 / final increment in [0.019, 0.021] mm; frozen Decimal tolerances and actual implementation hashes |
| Model | Declared external T3D2, length 10 mm, area 1 mm², E=1000 MPa, Poisson 0.3; physical verification NOT_ASSESSED |
| Only permitted edit | Node 2 DOF1 CLOAD within [0.5, 2.5] N; A=1 N; remaining geometry/material/mesh/BC/step/output/units fixed |
| A input | 420 bytes; SHA-256 `e2f91730b68f3af72b8054bc168d31b72a3f21ae186e899d64ab4b6b761523a3` from deterministic API |
| Actual AF Project/Instance/Plan/revision | **NOT PREPARED for real execution**; offline fixture identities are not substitutes |
| Resources | Frozen policy: 1 slot, 1 CPU, 0 GPU, 2048 MB, observation 300 seconds, one launch budget; actual host availability NOT_QUALIFIED |
| Working/scratch/output | Exact fresh paths and output identity still PENDING; must be outside AF Project metadata and bound in actual Plan |
| Operator | Research / human reviewer / issuer must be distinct appropriately restricted principals; actual protected deployment BLOCKED |
| Protected AF state | Exact AF Project/DB, capability, decision audit and mutable run/output roots must be under approved issuer control; research cannot mutate them through ordinary shell or DB access |
| Host / Abaqus / license | Executable identity, version, license access, process containment and closeout NOT_QUALIFIED; no probing Solver invocation |
| Human A-only decision | NOT_ESTABLISHED; must bind exact Project/contract/input/Plan/resources/output/expiry/nonce/one attempt |
| Source and result verification | Original record/DAT acquisition implemented and tested with fixtures; source authentication NOT_VERIFIED; V2 NOT_VERIFIED, V3 INCONCLUSIVE, V4 NOT_ASSESSED, ODB NOT_VERIFIED |
| Budget | Frozen max two Solver calls; UNKNOWN reservation held; no third attempt or new-key retry; successful real-B admission remains unimplemented |
| Stop/reconcile | Use existing AF managed-scope/PAUSED/UNKNOWN logic and only original owned handles; no blind retry or unknown-process cleanup |

The operator must separately approve A and, if eventually warranted, B. B cannot
be an analytical 2 N preset: accepted original A evidence, native Inverse handoff,
deterministic admission and a distinct exact Plan must precede it. Current code
rejects B; completing its authenticated positive admission is remaining software
work, not something a chat approval can unlock.

The AF source reader permits up to 1 MiB DAT and 512 events, whereas the current
GD persisted parser/observation format permits 16 KiB DAT, 512 lines (1024 chars
each), and 64 events. Larger outputs fail closed. Actual output compatibility must
be resolved/qualified before claiming complete real-A readiness. Hash consistency
does not authenticate a publisher or provide tamper-proof history.

## At most three necessary human actions

1. **First decision:** approve the single protected-Operator proposal in
   `7D_G3_D4_OPERATOR_APPROVAL_ONE_PAGE.md`, including a non-privileged research
   subject and separately mapped reviewer/issuer, exact protected AF state and
   deployment scope. This is approval for a future deployment phase, not a Grant.
2. Approve one independently initiated disposable Windows qualification of the
   exact internal bundle. Do not start it from the blocked Codex execution host;
   no GitHub push/hosted run is authorized by this report.
3. In one fresh disposable project, perform one official Plugin authentication/
   activation and confirm the provided `@GDCAE` smoke result. Do not supply a
   private thread ID or credentials to this chat.

These actions do not approve A. After engineering, source, host and OS gates have
closed, a new fully populated A-only request must receive separate exact approval.
