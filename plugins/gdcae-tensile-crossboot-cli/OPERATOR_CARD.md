# Exact archive preparation — NOT permission to retry

Current state: no actual terminal/intent has been written. No Owner, Plan, Grant, Solver or research state mutation is authorized by this card. Main must obtain a new exact archive approval after Testing accepts this candidate. The previous failed invocation is not retried automatically.

New proposal: `D:\Projects\GDCAETEST\TENSILE-CROSSBOOT-CLI-PROPOSAL-20261106-736616abf2\PROPOSAL.stdout.json`
File SHA256: `c7cbd1c96d084dd0d719fe07a904c0a787e3849c376a026952d5e9f3f3930dd0`
Native canonical object digest: `sha256:8cbc2db2ebc38e470d2bfcbe070aa2c52109b5351035645421adf7269444bb73`
Operation: `44d35ecaa64e4893a119aead1bb9735f` (unchanged).
Original Proposal file remains unchanged. Only the native implementation identity differs in the new object. Bare-input compatibility does not authorize a new installation or rewrite old approvals.

Read-only check, single command (no writing to the incident):
```powershell
& 'D:\XianLab\envs\LangChainEnv\Scripts\python.exe' -I -B -S 'D:\Projects\GDCAETEST\TENSILE-CROSSBOOT-CLI-FIX-20261106-dev-9bdbd25434\gd\cross_boot_archive.py' check --project 'D:\Projects\GDCAETEST\TENSILE-R4-JIT-A-20261105-MAIN-8fb1ad880d\research\af-B-readmit-d45dfb32dec2016ed6fa61c8b7075bbe' --package-pin 45b9cf1f24d94ed355febeb2bff5aa2443f41ce4c17cc9f655c39b244e3adf04 --python-exe 'D:\XianLab\envs\LangChainEnv\Scripts\python.exe' --proposal 'D:\Projects\GDCAETEST\TENSILE-CROSSBOOT-CLI-PROPOSAL-20261106-736616abf2\PROPOSAL.stdout.json' --proposal-digest 'sha256:8cbc2db2ebc38e470d2bfcbe070aa2c52109b5351035645421adf7269444bb73'
```
Expected `EXACT_READONLY_CHECK`. Any mismatch stops; never regenerate scope to hide mismatch.

Future exact approval must use schema `cross-boot-exact-authorization-reference-v1`, action `RECORD_HOST_RESTART_TERMINATED_UNCLEANLY`, operation above, `proposal_digest` exactly the tagged value above, `new_execution_authorized=false`, `budget_change_authorized=false`, fresh `expires_at` within native 600-second limit. Its provenance must be the future actual user's precise approval, not this development GO. The existing native capability remains necessary. Do not pre-create the approval now.

Only after that approval and independent qualification, Main supplies the actual approval path and file-byte SHA256 in these two variables. They are deliberately not populated here; no old approval path is reused. Execute at most once:
```powershell
& {
  if (-not $authorizationPath -or -not $authorizationSha256) { throw 'NEW_EXACT_APPROVAL_REQUIRED' }
  & 'D:\XianLab\envs\LangChainEnv\Scripts\python.exe' -I -B -S 'D:\Projects\GDCAETEST\TENSILE-CROSSBOOT-CLI-FIX-20261106-dev-9bdbd25434\gd\cross_boot_archive.py' commit --project 'D:\Projects\GDCAETEST\TENSILE-R4-JIT-A-20261105-MAIN-8fb1ad880d\research\af-B-readmit-d45dfb32dec2016ed6fa61c8b7075bbe' --package-pin 45b9cf1f24d94ed355febeb2bff5aa2443f41ce4c17cc9f655c39b244e3adf04 --python-exe 'D:\XianLab\envs\LangChainEnv\Scripts\python.exe' --proposal 'D:\Projects\GDCAETEST\TENSILE-CROSSBOOT-CLI-PROPOSAL-20261106-736616abf2\PROPOSAL.stdout.json' --proposal-digest 'sha256:8cbc2db2ebc38e470d2bfcbe070aa2c52109b5351035645421adf7269444bb73' --authorization $authorizationPath --authorization-sha256 $authorizationSha256
  if ($LASTEXITCODE -ne 0) { throw 'STOP_NO_RETRY_READONLY_RECONCILE' }
}
```
Allowed future write set: native `cross-boot-terminal-intent.json` and `cross-boot-terminal.json` under the original start only, protected by native capability/lock/MAC. It records HOST_RESTART_TERMINATED_UNCLEANLY, never normal stop or process exit codes. No GD/AF DB, budget, ready/stopped or original evidence rewrite. Any exception/uncertain result: stop, preserve output, use only reconcile:
```powershell
& 'D:\XianLab\envs\LangChainEnv\Scripts\python.exe' -I -B -S 'D:\Projects\GDCAETEST\TENSILE-CROSSBOOT-CLI-FIX-20261106-dev-9bdbd25434\gd\cross_boot_archive.py' reconcile --project 'D:\Projects\GDCAETEST\TENSILE-R4-JIT-A-20261105-MAIN-8fb1ad880d\research\af-B-readmit-d45dfb32dec2016ed6fa61c8b7075bbe' --package-pin 45b9cf1f24d94ed355febeb2bff5aa2443f41ce4c17cc9f655c39b244e3adf04 --python-exe 'D:\XianLab\envs\LangChainEnv\Scripts\python.exe'
```
Existing terminal historical re-read does not need an unexpired old approval; do not repeat commit for that purpose. Partial intent is a reconcile-only block. No following B preparation is authorized here.
