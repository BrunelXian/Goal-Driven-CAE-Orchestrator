# Development — .13 expired unconsumed Grant qualification

Candidate: GD `0.1.0-tensile.13`, AF `0.0.0+tensileexpiredgrant1`. This is a new site-bound ZIP/wheel and pip --target installation, not an alias for .11.1 or .12. Baseline freeze `.12` remains unchanged (`6cef7444156b98fac0888af5fa918825b39cc6e9149df85c0e93a273f40ebe0b`). Final acceptance belongs to independent Testing.

## Minimal implementation

- `expired_grant.py`: proposal/read never migrate schema; one explicitly requested archive transaction appends schema `expired-unconsumed-grant-qualification-v1` to `tensile_expired_unconsumed_grants` in the existing workflow DB. Operation ID, grant ID and parent operation are unique. Repeated same operation checks and returns the same row; conflict or uncertain native facts refuse. There is no new budget balance or Core revision.
- `grant_response.py`: the original live receipt recovery remains default. Explicit closed mode requires one exact expired Grant, its native authorization receipt/control, plus one exact native idle-stop receipt/control and verified lifecycle marker. It never changes Grant, Plan, Owner or capability.
- `window_history.py`: one explicit reference-schema route; existing zero-Grant paths are untouched. Fresh protected retained exits and all original native identities are checked again for every strict native admission snapshot.
- `operator_entry.py`: reference format acceptance only; no change to approval button or native authorization mechanics.
- New plugin/AF distribution identities and generated catalog bind the changed GD bytes. All 125 AF business Python files are byte-identical to .12; UI, workflow/scientific accounting, model, ODB reader, scoring and existing execution-window algorithms are byte-identical (`evidence/UNCHANGED_BOUNDARIES.json`).

The authoritative recorded history still refers to the same B request, parameters 288 MPa / 3003 MPa, contract and A result. The expired native Grant is preserved as expired, never revoked/extended/reissued. The sole B HOLD stays 2/1/1/0. A future new window gets a separate Plan/output/Grant and independent actual human approval. `retry=0` is unchanged.

## Tests and boundaries

Final installation package-manifest SHA256: `4324c14e4f9ac2598a7968166f511508e7a9f3fb282a2f4948ec84cf192e9bda`.

`tests/native_expired_grant.py`: final installation 19/19 developer checks. Real Windows native socket/capability/transaction: committed authorization response lost after 2 s timeout; same-key read recovery; natural 45 s expiry; normal native stop and actual retained-handle exits; qualified archive; independent new Plan; new native Grant exactly once; normal test Owner stop; zero Submit/Dispatch/Run/consumption/Solver. Scientific A/seal/accepted-decision/old source-history/snapshot transport are explicit test boundaries. Both native grants are MACHINE_TEST, not real user approval. The actual installed CLI `main` parser/function is exercised for propose/first archive/read under those boundaries. Its separate-process read/replay evidence is reported separately; no UI click is claimed.

Final full-chain report: `evidence/MACHINE_TEST_GRANT_RESPONSE_1daeb15ffcc3433ca25c61092cfecfeb/RESULTS.json`. Final 16/16 rejection/replay checks: same directory `rejections-9cc05e2fa39e4d86a83704e3c09bec2b/REJECTION_RESULTS.json` (wrong original authorization fingerprint/Grant, Run/consumption, missing closure, duplicate/conflict, read-only reopen and unchanged budget). Initial build 16+16 checks are historical development evidence, not added to final installation counts.

Native original .11.1 scientific read compatibility is explicit and read-only. The old reader does not whitelist SQLite table names; fingerprints retain original meta/stages/history. New qualification-table append does not grant old runtimes any new recovery privilege. After a newer window INTENT/COMMITTED, historical qualification validation does not re-enter an old current-window snapshot. Tests distinguish original evidence from modeled predecessor science.

## Reproduction and limits

Use absolute `D:\XianLab\envs\LangChainEnv\Scripts\python.exe -I -B -S`. Test scripts accept `--package-pin` and explicit isolated fixture paths; never pass the actual research workspace. `tools/build.py` builds a clean wheel and installs it with pip --isolated --no-index --no-deps --no-compile --target. Existing targets refuse overwrite. `plugins/gdcae-tensile-expired-grant/SOURCE_MANIFEST.json` records baseline repository HEAD/dirty state, exact frozen source hashes, overlay and changes; `rebuild.py` reconstructs in a new directory. No Git staging/commit/push.

No actual-site stop, archive, research write, Plan/Grant/Run, Solver or Datacheck was performed. Current real Owner remains CONNECTED according to independent evidence; its legal terminal/retained exit prerequisite is unmet. Therefore SITE_READY=false. This candidate does not automatically stop that Owner and does not obtain a new Plan on load. Future normal-stop authorization and actual qualification append remain separate applicable decisions. Future real B completion would settle the same HOLD once under the existing outcome transaction to 2/0/2/0; neither unused Grant nor MATCH/MISS changes that rule.

New UI usability/human click acceptance is NOT_TESTED by Development in this stage; unchanged UI bytes and independent Testing's isolated Windows test are separately classified. No synthetic history is called a real A/B experiment.

## Final development results (not independent acceptance)

Final payload: 19 native integration checks + 16 targeted rejection/replay checks + 9 actual SQLite transaction/concurrent/crash checks + 8 separate-process installed CLI read/replay checks. These are 52 developer checks with distinct evidence boundaries, not 52 real Solver or UI scenarios. The SQLite test uses actual archive/SQLite code with native-proof/proposal/lease boundaries replaced; commit-before/after crashes occur only in self-created child processes. A test harness thread-scoped patch mistake was corrected before the 9/9 final result; its failed harness evidence is retained and is not a product failure.

Additional final reports:
- `evidence/MACHINE_TEST_ARCHIVE_TX_c459a6892e2d4a9ba312df15f1cf0119/RESULTS.json`
- `evidence/MACHINE_TEST_GRANT_RESPONSE_1daeb15ffcc3433ca25c61092cfecfeb/cli-process-294c1ef569c94af592efacfc86e41570/RESULTS.json`

Reproduction entry arguments (absolute Python -I -B -S and candidate paths):
- `tests/native_expired_grant.py --package-pin <final pin> --run` creates isolated MACHINE_TEST projects, real test native IPC/Grant/stop, no Submit/Solver.
- `tests/expired_grant_rejection_checks.py --package-pin <final pin> --fixture <that isolated evidence root>`.
- `tests/expired_grant_cli_process.py --package-pin <final pin> --fixture <that isolated evidence root>`.
- `tests/expired_grant_transaction_checks.py --package-pin <final pin>`.

Independent Testing should copy the test harness to its own output root and retain the installed GD/AF pointers, as in previous isolated IPC reviews; it must not mutate historical real projects. No test command is a real B recovery authorization.
