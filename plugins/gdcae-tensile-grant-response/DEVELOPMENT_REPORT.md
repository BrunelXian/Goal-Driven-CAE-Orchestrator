# Original Grant response recovery — Development handoff

Candidate GD `0.1.0-tensile.12`, AF `0.0.0+tensilegrant1`. Final verdict belongs to independent Testing. The original .11.1 installation, Plan, Grant, journal and all research files remain unchanged.

## Change and authority

`grant_response.py` adds one-request acknowledgement state and a read-only CLI. It verifies original user-decision packet, request/key, Candidate B, native Plan/scope/input/resources, exact Owner/start, same-user capability, namespace/request fingerprint/receipt row operation/control event/Grant, original installed scientific snapshot and held budget. It rechecks scientific and installed identity after any wait before reporting current executability. No new authorization API, permission, executor or database is introduced.

`operator_entry.py` replaces its one authorize call with `authorize_once`: exclusive request + send-intent, at most one native transmission, then only same-key read-only receipt recovery on transport uncertainty. A recovered response explicitly records its read-only source and `authorization_reissued=false`. The function never re-approves, allocates a second key for the same journal, or retries Solver. Missing or contradictory evidence stops. It does not increase the native two-second socket timeout or weaken native checks.

The standalone CLI writes nothing and never continues execution. Its `confirmed_committed` and `executable_now` are separate. Original .11.1 runtime compatibility is explicitly read-only and fully pinned; an expired original Plan remains expired. It does not append a synthesized authorize-result to the original journal. Only a future separately qualified .12 inline operation can continue its original flow after fresh complete acknowledgement and still-valid native authorization.

Windows `approval_dialog.py` is byte-identical (`c6a0ed7fa666ba5c9380f727851040784f71b7960b9ad216f4688d30b6c7c835`). All AF business Python bytes remain unchanged. Generated catalog, site-bound installation identities and package metadata change normally; the new runtime never claims the old package pin. Source/installed payload and actual pip target RECORD/provenance are verified in `evidence/INSTALLATION.json` and `PAYLOAD_VERIFICATION.json`.

## Developer evidence, kept separate

1. Coordinator tests **11/11**: explicit substitutes for recovery/native facts; one send, unknown/expired refusal, no duplicate journal transmission, read-only API and scientific state change during wait. `tests/grant_response_checks.py`, latest `evidence/COORDINATOR_*/RESULTS.json`.
2. Shared actual Standard IPC **33/33**: new isolated A native Plans, real socket/service/capability/native authorization transaction and same-key receipt; postcommit response delay and EOF injected at the existing trusted `product_control:before_response` checkpoint. These are not B scientific qualification tests. Evidence `MACHINE_TEST_GRANT_RESPONSE_2c3e196632184224a7549274f6406ea9/RESULTS.json`.
3. B actual native IPC and installed recovery `main()` **43/43**, delay22/drop21: real B native Plans, real authorization control and persistent receipt/Grant binding, unique native authorize transmission, no Run/Submit/Dispatch/Solver, repeated recovery does not write journal or native database. The original A scientific feedback/seal, accepted decision, historical compatibility/snapshot transport are explicitly modeled test boundaries; local mouse decision is MACHINE_TEST, not a human B approval. This is not an unpatched complete scientific pipeline. Evidence `MACHINE_TEST_GRANT_RESPONSE_befe3e26fd4e445ca0bfe2a498f06612/RESULTS.json`.

No pooled number is presented as independent acceptance. All four isolated test Owners were normally stopped and native worker retained handles showed exit0. No actual-site lifecycle action occurred. The delay case measured roughly 2.2-second client UNKNOWN while the postcommit checkpoint waited 3.2 seconds; original committed receipts remained readable. A timeout does not cancel or reverse a Grant.

Reproduce with absolute registered Python 3.12.10 `-I -B -S`:

```
tests/grant_response_checks.py
tests/native_grant_response_ipc.py --run --b-run --package-pin 7174ae94e46617d4934ac0ec36a92c86691cb2b26b51e7b9bf6e07ba781ec798
```

The second command starts only unique isolated native test services and creates test Grants; it never Submit/Dispatches. Fixtures and handler checkpoint are in test files, not production flags. Testing should independently run the actual installed read-only CLI on the now-expired original B journal to establish the real old scientific evidence path, saving output only in its own evidence directory. That actual-path result is NOT_TESTED by Development.

## Source and remaining boundary

New maintained overlay and recipe: `plugins/gdcae-tensile-grant-response`. Baseline .11.1 FREEZE and every source byte, two repository HEAD/dirty snapshots, exact source changes and patch are pinned. Reconstructed non-generated source is verified; a rebuild in another path obtains its own site-bound catalog/manifest. No old source tree, shared environment, existing frozen package or Git index was changed.

First actual-site blocker remains the original expired Plan/Grant, even after acknowledgement is confirmed. This task provides no renewal, Submit, Dispatch or new B execution permission. Native actual clinical/scientific results are not fabricated, and Research budget stays `2/1/1/0` until a future legitimately executed result reaches the frozen accounting boundary.
