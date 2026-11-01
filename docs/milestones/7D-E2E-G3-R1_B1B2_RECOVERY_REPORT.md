# G3-R1 B1/B2 Recovery — BLOCKED after native fixture

Date: 2026-10-30. Scope: the approved isolated-root qualification and bounded harmless-family experiment only.

**B0 passed afresh; B1 returned `FIXTURE_SCOPE_UNKNOWN`; B2 was not run.** The new owner entered its retain-handles hold path and its exact execution session remained running when polled without input. There is no successful native closeout proof. Do not terminate that owner, retry the fixture, start B2, or install build_05 on the strength of this report.

This report preserves the old G3 global stop, R0 diagnostic, R1 PARTIAL, build_04 BLOCKED and historical orphan UNKNOWN. New evidence cannot repair the old missing identities or handles.

## 1. Baseline and permitted changes

- GD-CAE: `main@69b144cea9aecc515e15cc830368972b09258af9`; AF: `Develop@7f4b8d8f3a2c862ed8b244d495295f5d51ea0d88`. Both HEADs/branches and empty indexes were checked again after the stop.
- Existing tracked changes remain five GD files and four AF files. Their binary-diff digests match entry evidence after excluding Git's line-ending warning messages from the combined stdout/stderr capture. The initial unfiltered comparison reported ten/eight lines and different digests; these were capture artifacts, not evidence of extra edits. Both `git diff --check` commands returned 0.
- The three historical G3/R0/R1 reports retain their entry SHA-256 values. No historical report was rewritten.
- Repository deliverable added: this report only. No production source, AF source, controller source, index, existing ACL or global configuration was modified by this recovery task.
- New task-local objects reside under alias `PRIVATE_TEST_ROOT_A`: six exact reviewed R1 source/test copies, task wrappers `b1_owner.py` and `b2_checks.py`, fresh B0 evidence, root/ancestor qualification records, and the single native attempt's private ledger and safe failure receipt. No historical materials were deleted.
- Python: the registered LangChainEnv interpreter, Python 3.12.10, pytest 9.1.0 and existing pywin32 312. Harmless fixture image: the registered Python312 base interpreter. Ruff 0.12.0. No dependency installation or environment change.

## 2. Root qualification and its limits

The old root was rejected because additional ordinary writable trustees included unresolved identities. This is `ROOT_REJECTED_UNTRUSTED_WRITER` for selection purposes; it is **not** proof that an unknown person actually wrote there. Foreign-token effective rights remain `ACL_EFFECTIVE_RIGHTS_UNKNOWN`.

One new root was created directly beneath the current user's LOCALAPPDATA path with a protected restricted DACL supplied to CreateDirectory at creation. The allowlist is the confirmed current owner, SYSTEM and local Administrators. No permissive create-then-repair sequence, elevation, account creation or existing-object ACL edit occurred. The new root and inherited source/evidence/fixture objects were checked for the expected owner and three allow entries.

The actual current token was a process token, not an AppContainer, with zero restricted SIDs. Native AccessCheck was applied using its duplicated impersonation token. The logical ancestor chain and, subsequently, the actual resolved-root ancestor chain were inspected without recursive scans. No applicable extra ordinary allow entry granting delete-child, delete, WRITE_DAC or ownership replacement authority was found in those chains. Extra ordinary read/execute entries were not classified as writers merely because their names were unfamiliar. Applicable/inherit-only entries were distinguished.

App capability entries were assessed as conditional AppContainer grants, not standalone ordinary-user grants. Microsoft documents that AppContainer access depends on both the user/group and package/capability access checks. This is a structural qualification plus an actual-current-token check; it is not an executed cross-account attack test. See [Microsoft AppContainer implementation guidance](https://learn.microsoft.com/en-us/windows/win32/secauthz/implementing-an-appcontainer) and [file security/access rights](https://learn.microsoft.com/en-us/windows/win32/fileio/file-security-and-access-rights).

The current owner and OS administrators remain inside this local threat model. SHA-256 and ACL snapshots are integrity correlations, not tamper-proof security attestations. Original read handles denied share-write/delete for the six source files, owner wrapper and fixture image during the native attempt; this does not protect against arbitrary privileged or same-owner code generally.

### Pre-native path refusals

Two wrapper invocations refused before durable owner intent, attempt directory or native fixture creation. The first compared a resolved path with a noncanonical environment path. The second compared actual resolved ancestors against the logical five-entry ancestor table. A stopped-before-intent diagnostic reproduced the second failure at the parent-descriptor comparison. No family or native attempt existed at either refusal.

Read-only follow-up found nine actual resolved-root ancestors versus five logical ancestors. All nine were checked; no new ordinary replacement authority or reparse point was found. The wrapper now binds both chains explicitly, requires the actual table length to match, and compares each descriptor. The physical reason for the different path representations was not established and is not asserted here.

The fixed zero-process preflight reached the injected stop immediately before owner-intent persistence. Independent Reviewer renewed the prefixture approval for this exact wrapper SHA-256:

`31e42f183d8d2261f5c6eea3f5fdba3ddfe7f72d3dbae8b2017a67346faa8853`

No controller redesign or change to the six B0 source files was made. After the native stop, both logical and actual ancestor descriptors still matched their respective snapshots.

## 3. Fresh tests and native evidence

### B0: actual fresh result

Task-local `g3_r1_safe_checks.py b0-run02`: **93 passed, 0 failed, 0 skipped, 0 errors**. Forbidden-operation traps: 0; native fixture families during B0: 0; all six copied source digests unchanged. Evidence: `evidence/b0-run02.safe.json`.

These zero-process tests cover the existing intent/ledger ordering, failure refusal, duplicate/UNKNOWN handling, original-handle lifecycle mocks, accounting checks and redaction guards. They do not prove native Windows closure. Exact post-COMMIT response-loss injection remains an earlier unclosed coverage limitation; it is not newly claimed here.

The final owner wrapper and prepared B2 wrapper each passed Ruff. The B2 wrapper initially had E402 import-order diagnostics; task-local import loading was corrected and the repeat check returned 0. No repository source was changed for that correction. Full B2 Ruff/regression was not run after the safety stop.

### B1: one native attempt, no accepted closeout

Only one native family attempt proceeded beyond the gates. The source specifies one fixed Python root and one fixed sleeping child, without shell/network/install/AF/Solver work. The Job is created before spawn, bound through the at-create suspended Job-list path, with an active-process limit of three, no breakaway and no kill-on-close. A separate observation guard rejects a reported lifetime total above three; this is not a kernel-enforced lifetime creation cap. The owner retains the original handles. A ten-second execution deadline is configured; the subsequent retain-handles hold is an unresolved safety state, not a successful timeboxed closeout.

Read-only verification of the exact private attempt ledger passed SQLite integrity, digest-chain and flow validation. Its event sequence was:

1. `ATTEMPT_CREATED`
2. `SCOPE_PREPARED`
3. `SPAWN_INTENT`
4. `ROOT_REGISTERED`
5. `RESUME_INTENT`
6. `OWNED_SCOPE_ACTIVE`: root not signaled, active 1, total 1, terminated 0, in Job true
7. `OWNED_SCOPE_ACTIVE`: root not signaled, active 2, total 2, terminated 0, in Job true
8. `UNKNOWN`

The safe receipt is `BLOCKED`, code and cleanup code `FIXTURE_SCOPE_UNKNOWN`, primary code null, scope_closed false, root_exit null, stage_count 0, owned_total 2, active_processes 2. **Those counts are the last accepted observation, not a current OS-process query.** No `STAGE_EXIT`, `ROOT_HANDLE_EXIT`, `CLOSEOUT_REQUESTED` or `CLOSEOUT_ACCEPTED` was recorded.

The owner emitted a safe stop receipt stating original handles retained and new launches disallowed, then remained running in the exact tool session when polled without input. This supports entry into the designed hold path; there was no independent inspection of its current handle table. No process enumeration, PID lookup, guessed takeover, termination, new attempt or old-orphan reconciliation was performed.

Known evidence gap: the failed native observation/exception site and the rejected raw observation were not recorded. Several native checks and exception paths can produce the same code. Therefore the evidence does **not** establish a particular Win32 failure, process escape, handle loss, timeout, root exit or child exit. Root cause and current scope occupancy remain UNKNOWN. Do not infer that the harmless sleeps have elapsed and therefore closure must have occurred.

Key task-local safe records: `root-creation.safe.json`, `parent-qualification.safe.json`, `actual-root-ancestor-qualification.safe.json`, `source-snapshot.safe.json`, `b0-run02.safe.json`, `b1-canonical-preflight.safe.json`, `b1-stop.safe.json`, `b1-stop-ledger.safe.json`, `stop-integrity.safe.json`, and `stop-diff-warning.safe.json`. The native public receipt is the attempt's `review.safe.json`; private identities remain in the private ledger and are not reproduced here.

### B2: NOT_RUN

The independently reviewed selection was prepared but never executed: `tests`, ignoring `test_af_read_live.py`, `test_mcp_read_live.py` and `test_af_workflow_live.py`, and deselecting these two installation nodes:

- `tests/unit/test_g2_distribution.py::test_real_offline_wheel_install_has_no_development_import_fallback`
- `tests/unit/test_g3_product.py::test_two_installed_fixture_distributions_have_distinct_record_identity`

Both deselected tests perform actual venv/pip work and are prohibited even with synthetic wheels. The remaining selection includes ordinary Python subprocess tests; it is not a zero-process suite. No fresh collection count, full-suite result or source-to-node coverage claim is made. The prepared wrapper reuses the unchanged P1 output capture and G2 inventory hooks and refuses execution without a B1 clean-closeout receipt.

## 4. Acceptance matrix

| Gate | Result | Evidence / limitation |
| --- | --- | --- |
| B1R-01 | PASS, limited local threat model | Old unresolved root rejected; current token and both ancestor chains checked; foreign-token rights not tested. |
| B1R-02 | PASS | No existing ACL changes; before/after ancestor descriptor equality. |
| B1R-03 | PASS | One root, restricted protected DACL at creation; descendants checked. |
| B1R-04 | PASS | Six exact source copies; fresh 93/0/0/0 B0; post-stop source equality. |
| B1R-05 | PASS | Independent prefixture review of exact final wrapper, image/fixture pins and owner hold policy. |
| B1R-06 | PASS for initial binding only | Durable registration and resume intent, original-handle backend, Job observation 1 then 2; does not imply closure. |
| B1R-07 | FAIL | Required delayed-child/root-exit and final empty-scope closeout evidence absent; UNKNOWN receipt. |
| B1R-08 | UNKNOWN | No escape proven; no successful closure or current handle/scope proof either. |
| B1R-09 | NOT_RUN | B1 gate failed; B2 selection prepared only. |
| B1R-10 | PARTIAL | Wrapper Ruff and two-repository diff checks passed; independent stop review completed; full B2 checks not eligible. |

```text
G3_R1_B0_FRESH_STATUS=PASS_93
G3_R1_B1_NATIVE_FIXTURE_STATUS=BLOCKED_FIXTURE_SCOPE_UNKNOWN
G3_R1_B2_FULL_REGRESSION_STATUS=NOT_RUN
ROOT_EFFECTIVE_WRITE_CLASSIFICATION=QUALIFIED_CURRENT_OWNER_AND_OS_ADMIN_LOCAL_MODEL; FOREIGN_TOKEN_EFFECTIVE_RIGHTS_UNKNOWN
NEW_TASK_ROOT_DACL_CHANGED_EXISTING_PATHS=FALSE
BUILD_04_INSTALL_ACCEPTED=FALSE
OLD_ORPHAN_CURRENT_STATE=UNKNOWN
BUILD_05_INSTALL_AUTHORIZED=FALSE
REAL_A_READY=FALSE
PUBLIC_RELEASE_AUTHORIZED=FALSE
```

## 5. Independent review and remaining action

The native Independent Reviewer approved the final prefixture wrapper, then independently confirmed GLOBAL STOP / B1 BLOCKED from the new safe receipt, ledger projection and controller source. Reviewer explicitly rejected treating active=2 as current liveness, inferring escape or exact root cause, killing the owner, retrying the family or running B2. Reviewer corrected the report's initial description of the active-process limit versus the observed lifetime-total guard; that correction is incorporated above. Reviewer did not run native probes, tests, process queries or modifications.

The report's bounded privacy scan found zero UUID, raw SID, thread-URI, credential-pattern or private profile-path matches. The report has no trailing whitespace and the repository diff check returned 0. This is a scan of this deliverable, not a new scan or certification of historical private materials.

The retained owner currently has no reviewed external diagnostic/closeout command channel. Do not assume it can be safely reattached or retrofitted by a new Python process. **The single next action is a separately reviewed, narrowly authorized diagnostic/closeout procedure for this exact still-owned attempt**, preserving the original owner/handles and collecting a bounded failure-site/Win32-status projection before any recovery decision. If the original-owner capability cannot be retained or proved, keep UNKNOWN; never substitute PID reopening or a fresh test for the missing proof. No such intervention was executed in this task.

## 6. Sole build_05 qualification request — HELD, NOT SUBMITTED FOR EXECUTION

The task permits a runnable build_05 request only after B1/B2 succeed. That prerequisite is unmet. This is the single deferred request record, not installation authority:

- Requested future scope: one exact internal offline installation candidate, in a newly approved isolated environment, using reviewed lifecycle control and exact source/wheel digests; no AF Owner, Solver/ODB, real Grant or scientific execution.
- Prerequisites: resolve this owned UNKNOWN without guessing identities; obtain a valid B1 native closeout; run the precise permitted B2 suite and static/privacy checks; final independent review.
- Candidate identity, installation command allowlist, installation-specific controller extension and expected outputs must be freshly pinned and reviewed at that point. The current backend accepts the harmless fixture only and is not an approved pip/install runner.
- Stop conditions: identity/source mismatch, ambiguous receipt, unexpected descendant, lost original handle, privacy exposure or nonempty/unknown scope. Never retry UNKNOWN automatically.

No build_05 command is authorized or executed. Real-A authorization remains separately dependent on protected Operator deployment, real DAT provenance and exact Project/Plan/Grant approval. No commit, push or public release occurred.
