# D7-A01 expired pre-execution A recovery v2

2026-11-03 — DEVELOPMENT COMPLETE / INDEPENDENT ACCEPTANCE PENDING.
Next owner: Testing & Validation. This is not operator-ready and grants no execution authority.

Evidence root: `D:\Projects\GDCAETEST\D7-RECOVERY-20261103-9439a9ec78`.
Use `MANIFEST.json` there for exact file hashes, distribution artifacts, source roots,
test records and archive SHA. The accepted development source snapshot is `candidate02`;
`candidate01` is a superseded packaging attempt, not the acceptance candidate.
No new runtime was installed. Candidate version label: `0.0.0+d7a01recovery2`.

## Identity and bounded change

Development HEAD: `82bbec0fd8ed739f689b5f3ea3a065f38c558e3e` (initially clean).
AF Development HEAD: `7f4b8d8f3a2c862ed8b244d495295f5d51ea0d88` (pre-existing dirty work untouched).
The current checkout also contains AOO code; its whole-Core digest is NOT the D7
candidate identity. The candidate copies original installed D7 Core bytes and
overlays only `research/rod_local_project.py` and `research/rod_expired_recovery.py`.
It does not remove AOO modules from the development checkout or broaden compatibility.

| Identity | SHA256 (without `sha256:` prefix) |
|---|---|
| Original Core / frozen validator | `7857b4bdf3aa89093bb5f4d8c2fb19c04fbe878af8861d0a024acc59042c02dc` |
| Candidate Core / new validator | `5b1083f2e787f58f286c1ec317ff7c94e428451a9b3c3802536218422533a28a` |
| Unchanged AF | `b4bb09432c678b097977afe162070862564931f6b58545d4ea670e70b3257722` |
| Acceptance AST projection, both sides | `0f395730aa7d11778720d9b8978a37408972184cf0b5c1f6819d022e10362d24` |

`COMPATIBILITY_RECORD.json` contains the actual project/candidate/contract identities,
both complete source inventories, old/new runtime maps and validator versions,
exact difference list, reproducible closure/AST equality evidence, and
`execution_authorized=false`. Schema stays `d7-expired-a-compatibility-v1`;
implementation/new-validator version is `d7-expired-a-recovery-v2`.
This is developer-produced evidence for independent reproduction, not independent sign-off.

Every other Core Python source must be byte-identical. The acceptance AST comparison
permits only the exact recovery-dispatch/runtime-projection adapters. It compares
the remaining top-level functions, imports and constants; the project class and
new recovery module require explicit orchestration review. It is not a proof of
arbitrary whole-program equivalence. Frozen Goal, Model, Verification Criteria,
policy and stored A Candidate are retained. Runtime projection is transient and
explicit; the original validator SHA is never relabeled. AF/plugin/Python/version
changes remain rejected. `WORKFLOW_CODE_CHANGED` and `WORKSPACE_RUNTIME_MISMATCH`
are retained. The old source archive is comparison data, not a second live executor.

## Recovery behavior

`assess_expired_a(workspace, old_source_root, new_runtime)` is read-only readiness
assessment. It creates no Plan, intent, expiry or budget transition. Its snapshot
is informational and is never substituted for fresh reads at preparation time.

`prepare_expired_a(workspace, old_source_root, new_runtime, config, expires_at)`
is the exact later JIT entry. It still calls frozen AF public `RodProduct.prepare_real`
and the existing `LocalReadPort`. It creates a separate `expired-a-recovery-v2/af-A`
with new Plan, AF project/instance, request nonce/key, output identity and validity.
It writes a fixed intent and permits only identical retries. TTL is at most 600 s.
An incomplete intent, changed config/expiry or existing v1 preparation fails closed.
An expired uncommitted replacement is not silently rolled over: stop for reconciliation.

Proof schema `d7-original-af-expired-empty-v2` requires the expired exact original
Plan, one Plan in its store, PAUSED gate, empty slot, `supervisor_started='0'`, and
zero grants/runs/receipts/consumption/events/management_receipts/reconciliations/
observations/validations/management_grants/management_consumption/control_events.
All DB rows are read in one read-only transaction through the pinned AF reader.
Before and after that read, reject `owner.json`, `private/connection.json`,
`private/lifecycle-current.json` and any `private/start_*` entry. Missing evidence
fails closed. An initial `owner_id` or `project/owner.lock` is not itself a running Owner.
Fresh replacement preparation also checks startup markers before and after AF prepare;
AF's original initial-preparation lease continues to reject started/accepted stores.

Only an A-only, HELD, unaccepted, unstarted project may prepare. INTENT, UNKNOWN,
ACCEPTED, B presence and prior compatibility block new preparation. One atomic
`REBIND_EXPIRED_A` archives the old attempt as EXPIRED_UNEXECUTED and replaces its
active HOLD: held=1, charged=0, available=1, started=0. No release-plus-reserve window.
Original events/Plan/preview stay intact. Original HOLD and historical v1 recovery
events remain replayable; new v1 recovery writes are rejected. Before-commit rollback,
after-commit idempotency and repeat preparation with the same intent are covered.

This remains TRUSTED_LOCAL_HIL custody. Marker checks and DB snapshots do not create
a cross-process OS security boundary; concurrent or hostile same-user mutation is
not certified. Independent acceptance must review the pinned private-reader seam.

## Developer verification and original evidence

Interpreter: `D:\XianLab\envs\LangChainEnv\Scripts\python.exe`, Python 3.12.10,
pytest 9.1.0, `-I -B`; no dependency/environment changes.
Final frozen candidate: **173 passed, 8 deselected**, `frozen02/result.json` and
`frozen02/junit.xml`. The eight process/reparse tests are intentionally excluded;
they are not claimed as passed. Test selection, no conftest/plugin autoload,
fresh-run-only writes, SQLite path/ATTACH restrictions, no actual AF imports,
no native process/network, and negative probes are recorded in the result.
Only synthetic in-memory AF-table fixtures allow nonzero Grant rows. Persistent
Grant-table creation is refused. This guard is test hygiene, not an OS sandbox.

Earlier `dev01`: 170 passed, 8 deselected before three final assessment-refusal cases.
`frozen01`: collection failed because the snapshot omitted `test_d4_real_project.py`,
the fixture-only helper imported by D6. No guard denials. `candidate02` adds that
unchanged helper (imported, not collected); `frozen02` is the final result.
The earlier v1 142-test result remains historical and is not this candidate's result.

The read-only v2 assessment used actual original AF records and the new frozen Core.
Original 26 files match the initial reconciliation byte-for-byte. Old Plan remains
`rod_real_315a3543cd28b88cf249a46b953e1a9b`; ResearchProject remains
`rp_b2c8212dea8c4a0fb0529fa808d4bd28`; budget is still held=1, charged=0,
available=1, started=0. No original recovery transaction or replacement Plan exists.
No Owner, real Grant/Run, Abaqus/datacheck/ODB, Stable edit, install or Git commit/push.

## Independent Testing & Validation card

1. Verify `MANIFEST.json`, archive SHA, all candidate/source/reference hashes and
   unchanged frozen installation identities. Independently reproduce the closure
   comparison and AST equivalence, and review `CORE_OLD_TO_CANDIDATE.patch`.
   Review all v2 orchestration changes, legacy replay and new-write refusal.
2. Re-run the exact offline suite on a disposable copy of `candidate02`, with the
   absolute interpreter above. Create a fresh `D:\Projects\GDCAETEST\D7-RECOVERY-<test-id>`
   evidence root; pass that path as `--evidence-root`, the copied source root as
   `--source-root`, and a fresh alphanumeric `--label` to
   `tests/integration/d7_recovery_offline_checks.py`. Do not reuse an existing run directory.
3. **Separate required AF integration:** developer `prepare_real` tests substitute
   AF with a stub. They do NOT qualify the real AF public preparation interface or
   make this candidate operator-ready. The exact frozen AF source is
   `C:\Users\wuxia\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\GDCAE-D7-R2F-E2-20261101-A01\env02\Lib\site-packages\abqjobpilot`;
   its original wheel and SHA are listed in the manifest. Do not substitute dirty AF Development.
   Use the SAME candidate Core plus frozen AF in a separately controlled integration
   harness; do not disable the developer suite's AF-import guard. Allow only fresh
   fixture-root AF/GD writes, no Owner, Grant, Run, subprocess, network or Solver.
4. Build an isolated fresh synthetic old-A fixture with frozen contract values and
   one real inert AF Plan via `RodProduct.create` / `RodProduct.prepare_real`. Give it
   a short valid TTL and let it expire; do not edit timestamps/SQLite or copy a live
   AF DB whose absolute engineering/output paths still reference the original.
   The existing synthetic fixture's initial old-Core identity projection can seed
   GD history as test-only setup; report that limitation explicitly. Then exercise
   `assess_expired_a` and `prepare_expired_a` against that fixture using the actual AF
   APIs, original source archive and new runtime. The production recovery entry
   itself must run unmodified and all real runtime/identity guards must stay enabled.
5. Check positive recovery, exact retry after prepare/commit interruption, stale
   revision, expired replacement intent, wrong identity, startup/UNKNOWN/acceptance
   refusals, immutable history, distinct new output/nonce/Plan, and exactly one HOLD.
   Negative AF records may remain synthetic; never create real authority as a test.
   Validate real preflight, `a_only_application`, and new preview binding on the fixture.
6. Report PASS_LIMITED/PARTIAL/BLOCKED with source binding and gaps. Only after that
   acceptance and operator readiness may Main produce the actual A operation card.

## Concrete later JIT call sequence — DRAFT, NOT EXECUTED

Run only after independent acceptance and separate authorization for the target
workspace. First verify the manifest and every candidate file; do not import the
whole development checkout. This exact source binding avoids installing into or
changing env02. For independent integration, `workspace` MUST be the new fixture.
The eventual original-workspace call must use its unchanged `af-reference.json`.

```python
import copy, json, sys, time
from pathlib import Path
delivery = Path(r'D:\Projects\GDCAETEST\D7-RECOVERY-20261103-9439a9ec78')
source = delivery / 'candidate02'
af_site = Path(r'C:\Users\wuxia\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\GDCAE-D7-R2F-E2-20261101-A01\env02\Lib\site-packages')
sys.path[:0] = [str(source / 'src'), str(af_site)]  # launch with absolute Python -I -B
from aegiscae.research.rod_local_project import code_digest
from aegiscae.research.rod_expired_recovery import assess_expired_a, prepare_expired_a
from abqjobpilot.execution.rod_local_hil import check_runtime, source_digest
from abqjobpilot.execution.standard_contract import StandardConfig
from abqjobpilot.execution.models import canonical_json
from abqjobpilot.product_rod import RodProduct
record = json.loads((delivery / 'COMPATIBILITY_RECORD.json').read_text())
assert code_digest() == record['new_runtime']['gd'] == 'sha256:5b1083f2e787f58f286c1ec317ff7c94e428451a9b3c3802536218422533a28a'
assert source_digest() == record['new_runtime']['af']
# workspace: absolute Path chosen in the independently accepted operation card.
runtime = copy.deepcopy(record['new_runtime'])
ref = json.loads((workspace / 'af-reference.json').read_text())
value = copy.deepcopy(ref['config'])
value['research_runtime'] = runtime  # retain all material/plugin pins
config = StandardConfig(canonical_json(value))
check_runtime(config, runtime)
old_source = delivery / 'original-source/aegiscae'
destination = workspace / 'expired-a-recovery-v2'
intent = destination / 'intent.json'
# Same expiry on retry; never quietly create another request after an expiry.
expires = json.loads(intent.read_text())['expires_at'] if intent.exists() else int(time.time()) + 600
state = prepare_expired_a(workspace, old_source, runtime, config, expires)
binding, c = state['attempts']['A']['binding'], state['candidates']['A']
expected = {k: c[k] for k in ('research_project_id', 'contract_digest', 'candidate_id', 'input_digest')}
expected.update(research_revision=c['admitted_revision'], request_nonce=binding['request_nonce'])
product = RodProduct(destination / 'af-A')
product.preflight_real(binding['plan_id'], binding['plan_digest'], config=config, expected_contract=expected)
packet = product.a_only_application(binding['plan_id'], binding['plan_digest'], config=config,
    expected_contract=expected, nonce=binding['request_nonce'], not_before=int(time.time()), expires_at=expires)
preview = dict(schema='gdcae-d7-review-preview-v1', packet=packet, budget=state['budget'],
    research_revision=state['project_revision'], execution_authorized=False, human_decision='NOT_ESTABLISHED')
# Save returned state/config/expected/preview separately under destination with write-once semantics.
# Do not overwrite the original af-reference.json, approval-preview.json or d7-v2.json.
```

The draft stops at a new review packet. It contains no Owner, authorization or
dispatch command. Any expired preview, mismatch, partial preparation or UNKNOWN
requires stopping and reconciling the same identity. It must not be turned into
automatic retry/renewal. Testing must finish the real AF preparation/preview checks
before issuing a fully usable operator card; no such readiness is claimed here.
