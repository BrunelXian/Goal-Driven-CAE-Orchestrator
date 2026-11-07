# Cross-boot native archival — prepared only

GD 0.1.0-tensile.11 / AF 0.0.0+tensilecrossboot1. No real archival is authorized by this development package.
Original Owner owner_5ceb54fdf1ec443fbced42660531e108, Start start_61b46dcbc23c4acd92f26197cbccee9c.

The actual read-only proposal is outside the freeze:
D:\Projects\GDCAETEST\TENSILE-CROSSBOOT-PROPOSAL-20261106-af59b913de\PROPOSAL.stdout.json
Proposal digest: 543e9c376b39d9d3adfc9986f3e175a6c6425dc59e0acade564b59636eb9333e.
Operation: 44d35ecaa64e4893a119aead1bb9735f.
The proposal contains exact original AF instance/Plan/scope, original three process identities, current kernel+CIM+Event12 boot, nine original-file hashes, independent journal/Scientific DB CAS references and new implementation identity. It is UNAPPROVED.

Common command (PowerShell; exact paths, no UI and no Solver):
```powershell
$py = 'D:\XianLab\envs\LangChainEnv\Scripts\python.exe'
$entry = 'D:\Projects\GDCAETEST\TENSILE-V1-CROSSBOOT-20261106-dev-7a1e3f3aaf\gd\cross_boot_archive.py'
$project = 'D:\Projects\GDCAETEST\TENSILE-R4-JIT-A-20261105-MAIN-8fb1ad880d\research\af-B-readmit-d45dfb32dec2016ed6fa61c8b7075bbe'
$pkg = '7f8c2118ee2b8f930d2c35452f30c041dde603701afc233d4060c9ca4ec3df18'
$proposal = 'D:\Projects\GDCAETEST\TENSILE-CROSSBOOT-PROPOSAL-20261106-af59b913de\PROPOSAL.stdout.json'
$pin = '543e9c376b39d9d3adfc9986f3e175a6c6425dc59e0acade564b59636eb9333e'
& $py -I -B -S $entry check --project $project --package-pin $pkg --python-exe $py --proposal $proposal --proposal-digest $pin
```
Expected EXACT_READONLY_CHECK; this does not grant archival or execution permission. Any failure stops.

After independent candidate/proposal acceptance and a new exact user archival authorization only, Main may invoke the same entry `commit` with the common fields plus `--authorization <absolute-reference.json> --authorization-sha256 <file-sha256>` once. Authorization reference schema:
`cross-boot-exact-authorization-reference-v1`, action `RECORD_HOST_RESTART_TERMINATED_UNCLEANLY`, exact proposal_digest and operation_id above, new_execution_authorized=false, budget_change_authorized=false, expires_at=current UTC epoch+at most600 seconds; include actual decision provenance. Do not generate this reference before the exact decision. It is provenance/scope, not a human cryptographic signature or substitute for native DPAPI lifecycle capability.

Allowed writes are exactly two append-only protected native files under the original Start directory: cross-boot-terminal-intent.json and cross-boot-terminal.json. Native owner.lock is acquired/released without deleting/changing its bytes. No old native DB, scientific DB, stopped/ready, approval/Grant/Run or budget writes. Commit authenticates existing native operator capability, acquires the native lease, resamples exact state, writes unique intent then HMAC+DPAPI terminal; partial intent refuses retry.

Result is HOST_RESTART_TERMINATED_UNCLEANLY / normal_stop=false / exit_codes=UNKNOWN. It is not STOP_COMMITTED or ORDERLY_STOP. Old instance start remains refused. A later research window needs its separately permitted fresh qualification and new execution authorization.

Read-only reopening uses `reconcile` with project/package/interpreter only; it does not need an unexpired old authorization. Existing terminal is revalidated as historical evidence, not requalified against each future boot. INTENT without terminal is UNKNOWN, no automatic retry/finalize. Future GD window admission separately rechecks no supported current Owner republication and original zero execution state. No claim against malicious arbitrary same-user processes.

Current task stops before the `commit` call. Actual B Plan/Owner/Grant/Run/Solver remain uncreated.
