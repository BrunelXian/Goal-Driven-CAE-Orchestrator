# D7-A01 Expired Plan Recovery — development candidate

Date: 2026-11-02. Status: DEVELOPMENT CANDIDATE; independent Testing & Validation pending.

## Scope and baseline

GD HEAD: `06edabc7fa64f943c704de38f81d56cf47d9b40b`.
AF Development HEAD: `7f4b8d8f3a2c862ed8b244d495295f5d51ea0d88`.
Both repositories had existing uncommitted work. This delivery changes only
`src/aegiscae/research/rod_local_project.py`, adds
`src/aegiscae/research/rod_expired_recovery.py` and its developer unit tests,
plus this handoff and the candidate manifest. AF Development is not modified.
No installation, dependency change, Stable edit, Git commit/push, Owner start,
production Grant/Run, Abaqus invocation or mutation of the actual experiment
was performed.

Global instructions read: `C:/Users/wuxia/.codex/AGENTS.md` and
`D:/XianLab/envs/ENVIRONMENTS.md`. There is no repository-root AGENTS.md.
Developer interpreter: `D:/XianLab/envs/LangChainEnv/Scripts/python.exe`,
Python 3.12.10, pytest 9.1.0, explicit checkout source import. Its default
installation is not the candidate. The original env02 installation was
separately inspected read-only: both distributions are `0.0.0+d7r2f`.
The manifest records actual paths and code digests; HEAD alone is not identity.

## Bounded architecture

`prepare_expired_a(workspace, old_source_root, new_runtime, config, expires_at)`
is the explicit new Python preparation entry. It reuses original AF
`RodProduct.prepare_real` and `LocalReadPort`; there is no additional executor.
The old plugin CLI is unchanged and continues to reject a changed workspace
runtime with `WORKSPACE_RUNTIME_MISMATCH`. The new entry verifies the original
workspace against the frozen research state, compares actual old/new Core
sources, and qualifies the actual AF/runtime through the existing AF checks.
`WORKFLOW_CODE_CHANGED` remains enforced against the effective runtime.

Compatibility schema: `d7-expired-a-compatibility-v1`; implementation and new
validator version: `d7-expired-a-recovery-v1`. The record binds project,
frozen bundle digest, unchanged A Candidate digest, old and new runtime maps,
old validator version/SHA, new validator version/SHA, both source inventories,
exact changed-file list and independently reproducible equivalence evidence.
The original validator SHA continues to mean the whole original Core.
The new validator SHA is the whole new Core; no identity aliasing is used.
The old source tree is input data for comparison, not a second live validator.

Only the two Core modules named above may differ. All other Core Python bytes
must match. The actual acceptance-code AST must also match after removing
exactly the new recovery dispatch and runtime-projection adapter. The proof
includes the reducer's numerical verdict, policy, candidate construction,
acceptance checks, imports and constants. All other verification modules,
contracts, parsers, output template and numerical policies remain byte-identical.
The project class is orchestration and is subject to explicit diff review,
not an assertion of complete program equivalence. AF, plugin, interpreter and
dependency version changes are rejected by this v1. A version-only equivalence
assertion is insufficient. The real old installed Core comparison passed;
Testing & Validation must independently reproduce it using the manifest.

The frozen policy, Goal/Model/Verification bundle, and stored Candidate are
never rewritten. `execution_candidate` makes a transient execution projection
with the new runtime. Subsequent preflight and observation checks use that
projection. The Compatibility Record explains this mapping explicitly.

## Nonexecution proof and atomic budget transition

The bounded adapter reads original AF format-3 records through the existing
read-only store opened by `RodProduct._reader()`. This internal reader seam is
intentional and version-pinned; it is not a caller-supplied boolean proof or
a general migration interface. In one snapshot it requires exactly one Plan,
verifies its digest and instance, observes expiration, PAUSED gate and empty
slot, and requires zero grants, runs, receipts, consumption, execution events,
management receipts and reconciliations. Missing tables/records and ambiguous
or nonzero evidence fail closed. Public preflight alone cannot establish this.
The original expired Plan bytes and count snapshot are retained in the event.

Only original A=HELD, unaccepted, unstarted, with no B and no previous recovery
can proceed. INTENT, UNKNOWN, ACCEPTED and every other status are rejected.
An expired old Plan cannot acquire renewed eligibility through this entry:
its expiry and AF records remain unchanged. A fresh AF Project/Plan is prepared
under `expired-a-recovery-v1/af-A`; the same ResearchProject and Candidate remain.
New AF project/instance, Plan ID/digest, request key/nonce and output identity
are required. New validity is independently bounded to 600 seconds.

One `REBIND_EXPIRED_A` workflow transaction archives the old attempt as
`EXPIRED_UNEXECUTED` and installs the new HELD attempt. The original HOLD event
remains in the journal. There is no intermediate budget release or second
reservation. The result is held=1, charged=0. Replay uses the recorded snapshot,
not wall-clock expiry or the current filesystem. Old HOLD idempotency keys
continue to return their original binding/preflight. A write-once preparation
intent permits retry of the same request and rejects changed expiry/config.
Before-commit failure rolls back; after-commit retry returns the committed
state without a second Plan. An incomplete intent directory fails closed.

This is TRUSTED_LOCAL_HIL record custody, not protection against malicious
same-user record editing, clock rollback, or a replacement AF implementation.
No scientific acceptance or actual solver result is claimed by this delivery.

## Developer checks

The candidate manifest contains exact test counts, safe-run records and SHA256s.
Tests cover synthetic recovery, immutable contract/candidate, identity reuse,
zero-evidence checks, pending/accepted refusal, expiry, validator/source/AST
mutation, optimistic revision conflict, duplicate recovery, budget conservation,
history replay, before/after-commit failure and preparation-entry crash retry.
The synthetic entry test substitutes AF preparation; it is not real AF acceptance.

Final safe command (absolute interpreter, no dependency installation):

```powershell
& D:\XianLab\envs\LangChainEnv\Scripts\python.exe -B tests/integration/g3_d6_offline_checks.py gd-expired-a-dev05 tests/unit/test_d7_expired_recovery.py tests/unit/test_research_project.py tests/unit/test_d6_a_only.py tests/unit/test_d7r2f_plugin.py -k 'not independent_process_reopen and not reparse_point and not process_crash and not import_create_read_have_no_process'
```

Earlier broad selection: 158 passed, 13 failed. Eight failures were process
operations blocked by the no-native audit hook; five were AF fixtures refusing
`E1_GUARD_NOT_ACTIVE`. No boundary was disabled. These are not reported as
passing integration tests. The final selection excludes eight process cases
and omits that integration file. A later run (`dev04`) passed 141 tests but
failed the unchanged D6 concurrent-HOLD test with `STORE_BUSY` at
`project._check_root` while another writer's journal was present. The new
recovery tests all passed. The result is retained in the manifest; a fresh
rerun is recorded separately and does not erase this concurrency limitation.
Initial default pytest temp directory was
inaccessible; subsequent runs used dedicated fresh directories.

## Independent acceptance handoff

1. Recheck repository HEADs, dirty status, exact manifest file SHA256s and old
   installed distribution/source identity. Package the new Core under a distinct
   candidate version (suggested `0.0.0+d7a01recovery1`); do not overwrite the old
   installation or relabel its SHA. No wheel was installed by Development.
2. Independently review the two-module diff and reproduce old/new inventory and
   acceptance AST comparisons. Keep the original source archive as evidence.
   Verify new installed Core `code_digest()` equals the candidate manifest.
   Retain exactly the old AF/plugin/dependency identities; using dirty AF
   Development in place of the frozen installed AF must fail.
3. Use a disposable copy and separately authorized test boundary to exercise
   real AF inert preparation, snapshot concurrency, failed-preflight/orphan
   preparation, stale keys, commit crash and read-only replay. Do not treat the
   developer mock preparation test as completion of these checks.
4. For a separately authorized recovery of the original workspace, construct
   `new_runtime` from the frozen map with only `gd` set to the verified new Core
   digest. Reconstruct StandardConfig from the old af-reference config with only
   `research_runtime` replaced, retaining all existing materials/plugin pins.
   Call the explicit `prepare_expired_a` entry with the archived old Core source
   directory and a fresh <=600-second expiry. Do not call the old plugin prepare
   entry and do not rewrite d7-v2.json or old prepare-intent/af-reference/preview.
5. Verify original ResearchProject ID, Candidate ID, frozen contract bytes and
   old AF records are unchanged; new binding/expiry/output identity are distinct;
   old attempt is retained, and only one active HOLD exists. Review the new
   binding and Compatibility Record returned by the new API. Any new approval
   preview must be constructed for that binding via original AF APIs and saved
   separately; the old approval-preview is never valid for the new request.

Stop here for independent Testing & Validation. No execution authorization is
conveyed by the manifest, Compatibility Record, developer tests or this handoff.


