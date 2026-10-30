# G2-LONG HIL boundary and deployment request

Date: 2026-10-30. `HIL_ENFORCEMENT_NOT_VERIFIED` / `BLOCKED_HIL_DEPLOYMENT`.
No real approval, real capability, Grant, Operator process or ACL deployment occurred.

## Actual canary evidence

Main ran `tests/integration/g2_hil_canary.py` under the selected existing Python
with P1 bounded capture and an explicit output-field allowlist. It created only
two fresh canary files under this task's `hil-canary/` directory. Windows process
token user SIDs were compared internally using a salted hash; no SID, user name,
capability bytes or hash was projected. The owned child exited normally (code 0).

| Boundary | Observation | Interpretation |
|---|---|---|
| Actual Main tool process / owned Python child | Same process-user token; neither elevated | Separate processes do not supply independent Operator identity |
| Fresh canary capability | Child read succeeded | This task's ordinary user-writable canary directory is not an Operator secret boundary |
| Fresh canary Operator-code file | Child read/write succeeded | Putting trusted code beside ordinary task files would permit indirect self-approval |
| Actual Operator code/config/secrets | Not accessed; deployment not established | No claim about existing protected locations or real credentials |
| Native role restrictions | Configuration/tool restrictions are distinct from OS tokens | They cannot establish strong HIL isolation by themselves |
| MCP service identity / network / elevation paths | NOT_INSPECTED / NOT_TESTED | No assertion of protected network channel, service principal or resistance to elevation |

This is a negative finding for the tested same-user canary arrangement, not an
exhaustive host penetration test. No real secret was read, no permissions changed,
and no unowned process was stopped. Original and mutated canary states are
bounded test artifacts; they are excluded from source snapshots and packages.

## Single minimal deployment request (not executed)

Have the authorized host administrator approve and deploy one independently
controlled Operator environment/security principal. Its credential, signer,
executable and configuration must be unreadable or non-modifiable as appropriate
by ordinary research Main/subagents, including their tools and inherited users.
The research side may submit only a bounded exact approval request; the operator
must inspect and explicitly approve or reject one immutable Plan/input/resource/
output/time/attempt tuple. Denial, expiry or altered fields require safe refusal.

Before real A, repeat canary challenges across the actual two principals for
secret read, trusted-code/config write and signing/dispatch access; review the
communication path and execution account. Record both allowed operator behavior
and denied research-side behavior. A prompt restriction or one denied file alone
does not close this gate. This request does not authorize account creation,
password/ACL/service/firewall changes, elevation, signing or a real Solver run.

Interface negative tests and TEST_ONLY canary approvals can pass independently
of this deployment gate. Actual human consent and exact real-A authorization
remain separate prerequisites.
