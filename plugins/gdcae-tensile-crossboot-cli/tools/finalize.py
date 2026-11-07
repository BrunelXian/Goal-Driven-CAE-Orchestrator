"""Freeze only this isolated candidate; no live lifecycle calls."""
import hashlib,json,shutil,subprocess,sys,difflib
from pathlib import Path
z=Path(__file__).resolve().parents[1]
base=Path(r'D:\Projects\GDCAETEST\TENSILE-V1-CROSSBOOT-20261106-dev-7a1e3f3aaf')
repo=Path(r'D:\Projects\Goal-Driven-CAE-Orchestrator')
dest=repo/'plugins/gdcae-tensile-crossboot-cli'
assert not dest.exists() and not (z/'FREEZE.json').exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,sort_keys=True,indent=2),encoding='utf8')
old=Path(r'D:\Projects\GDCAETEST\TENSILE-CROSSBOOT-PROPOSAL-20261106-af59b913de\PROPOSAL.stdout.json')
assert sha(old)=='b7ee5acbf40e5e4b9076d6dbfd7f31b9ee19d80e3677c11a9d4f0629df303353'
proposal=Path(r'D:\Projects\GDCAETEST\TENSILE-CROSSBOOT-CLI-PROPOSAL-20261106-736616abf2\PROPOSAL.stdout.json')
v=json.loads(proposal.read_bytes());pin=v['proposal_digest'];assert pin=='sha256:8cbc2db2ebc38e470d2bfcbe070aa2c52109b5351035645421adf7269444bb73'
afdiff=[p.relative_to(z/'src/af').as_posix() for p in (z/'src/af/abqjobpilot').rglob('*.py') if sha(p)!=sha(base/'src/af'/p.relative_to(z/'src/af'))]
assert afdiff==['abqjobpilot/execution/tensile_catalog.py'],afdiff
for p in (z/'src/gd').rglob('*'):
 if p.is_file():assert sha(p)==sha(z/'gd'/p.relative_to(z/'src/gd'))
for p in (z/'src/af').rglob('*'):
 if p.is_file():assert sha(p)==sha(z/'af'/p.relative_to(z/'src/af'))
write(z/'evidence/PAYLOAD_IDENTITY.json',dict(gd_source_install_identical=True,af_source_install_identical=True,af_business_python_unchanged=True,af_generated_difference=afdiff,original_proposal_sha256=sha(old),new_proposal_sha256=sha(proposal),new_proposal_digest=pin))
(z/'DEVELOPMENT_REPORT.md').write_text('''# CLI digest boundary repair — Development, pending independent acceptance

GD 0.1.0-tensile.11.1; AF 0.0.0+tensilecrossbootcli1. Scope: one GD CLI serialization boundary. Original .11 and original failed-attempt evidence remain unchanged.

The .11 CLI produced a bare canonical-object SHA256 and forwarded it to AF, which requires `sha256:`. Its tests called AF directly and missed this installed CLI boundary. The real failed call rejected before any native intent or terminal write. This was a developer interface defect.

`cross_boot_archive.py` now emits the native AF digest. CLI input accepts only exact lowercase 64 hex, explicitly converted, or exact `sha256:` plus 64 lowercase hex. Wrong algorithm, whitespace, uppercase and duplicate prefix are rejected. The supplied proposal object and envelope are independently checked. Authorization references are never rewritten: native authorization still requires the tagged identity. File-byte SHA256 is separate from canonical JSON object SHA256.

AF business Python sources, including lifecycle, capability, terminal writer, canonicalization and authorization, are byte-identical to .11. Strict GD_ROOT/catalog qualification prevents using the old AF install with modified GD. Only generated catalog, installation metadata/version and provenance change. No permissions were weakened to preserve an old digest.

Actual installed subprocess CLI tests: 17/17 in `evidence/INSTALLED_CLI_32c9b857b1a2457d8a5d844531df30c7/RESULTS.json`, plus 3/3 commit-boundary negatives in its `COMMIT_BOUNDARY_RESULTS.json`. The current reproducible driver combines all 20. Proposal/check/commit/reconcile children do not patch production. Fixture creation uses synthetic preboot lifecycle and A proof with real isolated SQLite, protected native capability and real host boot sampling. Partial interruption is an exact protected-intent fixture, not a killed process. No real Owner, Solver or actual site archive. Prior unaffected .11 evidence is retained, not claimed rerun.

Reproduce: absolute LangChainEnv Python 3.12.10 `-I -B -S tests/installed_cli_checks.py`. It creates unique OFFLINE_TEST_ONLY directories in this candidate's evidence area. `tests/build_cli_fixture.py` is the standalone fixture constructor. Actual system restart, real archival retry and new B execution are NOT_TESTED/NOT_AUTHORIZED.

Original Proposal file SHA b7ee5acbf40e5e4b9076d6dbfd7f31b9ee19d80e3677c11a9d4f0629df303353 remains unchanged. Its canonical bare 543e9c376b39d9d3adfc9986f3e175a6c6425dc59e0acade564b59636eb9333e and tagged representation identify the same old object. The new read-only proposal preserves operation 44d35ecaa64e4893a119aead1bb9735f and all original scope/evidence, but has a different `implementation` identity. It must receive new exact authorization after independent acceptance; no previous approval is replayed.

Build/source ownership: new `plugins/gdcae-tensile-crossboot-cli` overlay, baseline .11 FREEZE and every source byte pinned, exact patch, two repository HEAD/dirty snapshots. No Git stage/commit/push or shared environment change. Installation is the built wheel via isolated pip target and the exact ZIP payload; RECORD/provenance verified.
''',encoding='utf8')
common=f"--project 'D:\\Projects\\GDCAETEST\\TENSILE-R4-JIT-A-20261105-MAIN-8fb1ad880d\\research\\af-B-readmit-d45dfb32dec2016ed6fa61c8b7075bbe' --package-pin {sha(z/'gd/package-manifest.json')} --python-exe 'D:\\XianLab\\envs\\LangChainEnv\\Scripts\\python.exe'"
cmd=f"& 'D:\\XianLab\\envs\\LangChainEnv\\Scripts\\python.exe' -I -B -S '{z / 'gd/cross_boot_archive.py'}'"
(z/'OPERATOR_CARD.md').write_text(f'''# Exact archive preparation — NOT permission to retry

Current state: no actual terminal/intent has been written. No Owner, Plan, Grant, Solver or research state mutation is authorized by this card. Main must obtain a new exact archive approval after Testing accepts this candidate. The previous failed invocation is not retried automatically.

New proposal: `{proposal}`
File SHA256: `{sha(proposal)}`
Native canonical object digest: `{pin}`
Operation: `44d35ecaa64e4893a119aead1bb9735f` (unchanged).
Original Proposal file remains unchanged. Only the native implementation identity differs in the new object. Bare-input compatibility does not authorize a new installation or rewrite old approvals.

Read-only check, single command (no writing to the incident):
```powershell
{cmd} check {common} --proposal '{proposal}' --proposal-digest '{pin}'
```
Expected `EXACT_READONLY_CHECK`. Any mismatch stops; never regenerate scope to hide mismatch.

Future exact approval must use schema `cross-boot-exact-authorization-reference-v1`, action `RECORD_HOST_RESTART_TERMINATED_UNCLEANLY`, operation above, `proposal_digest` exactly the tagged value above, `new_execution_authorized=false`, `budget_change_authorized=false`, fresh `expires_at` within native 600-second limit. Its provenance must be the future actual user's precise approval, not this development GO. The existing native capability remains necessary. Do not pre-create the approval now.

Only after that approval and independent qualification, Main supplies the actual approval path and file-byte SHA256 in these two variables. They are deliberately not populated here; no old approval path is reused. Execute at most once:
```powershell
& {{
  if (-not $authorizationPath -or -not $authorizationSha256) {{ throw 'NEW_EXACT_APPROVAL_REQUIRED' }}
  {cmd} commit {common} --proposal '{proposal}' --proposal-digest '{pin}' --authorization $authorizationPath --authorization-sha256 $authorizationSha256
  if ($LASTEXITCODE -ne 0) {{ throw 'STOP_NO_RETRY_READONLY_RECONCILE' }}
}}
```
Allowed future write set: native `cross-boot-terminal-intent.json` and `cross-boot-terminal.json` under the original start only, protected by native capability/lock/MAC. It records HOST_RESTART_TERMINATED_UNCLEANLY, never normal stop or process exit codes. No GD/AF DB, budget, ready/stopped or original evidence rewrite. Any exception/uncertain result: stop, preserve output, use only reconcile:
```powershell
{cmd} reconcile {common}
```
Existing terminal historical re-read does not need an unexpired old approval; do not repeat commit for that purpose. Partial intent is a reconcile-only block. No following B preparation is authorized here.
''',encoding='utf8')
generated={'src/gd/af_installation.py','src/gd/package-manifest.json','src/af/abqjobpilot/execution/tensile_catalog.py'}
files=lambda root:{p.relative_to(root).as_posix():p for p in (root/'src').rglob('*') if p.is_file() and p.relative_to(root).as_posix() not in generated}
bf,nf=files(base),files(z);changes=[];patch=[];dest.mkdir()
for name in sorted(set(bf)|set(nf)):
 before=sha(bf[name]) if name in bf else None;after=sha(nf[name]) if name in nf else None
 if before==after:continue
 changes.append(dict(path=name,before_sha256=before,after_sha256=after))
 if after:
  out=dest/'overlay'/name;out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(nf[name],out)
 patch.extend(difflib.unified_diff(bf[name].read_text(encoding='utf8').splitlines(True) if before else [],nf[name].read_text(encoding='utf8').splitlines(True) if after else [],fromfile='a/'+name,tofile='b/'+name))
for d in ('tests','tools'):
 shutil.copytree(z/d,dest/d)
for name in ('DEVELOPMENT_REPORT.md','OPERATOR_CARD.md'):shutil.copyfile(z/name,dest/name)
shutil.copyfile(repo/'plugins/gdcae-tensile-crossboot/rebuild.py',dest/'rebuild.py')
(dest/'SOURCE_DIFF.patch').write_text(''.join(patch),encoding='utf8');write(dest/'SOURCE_CHANGES.json',changes)
git={}
for n,r in [('gd',repo),('af',Path(r'D:\Projects\abqjobpilot_dev'))]:
 git[n]=dict(path=str(r),commit=subprocess.check_output(['git','-C',str(r),'rev-parse','HEAD'],text=True).strip(),status=subprocess.check_output(['git','-C',str(r),'status','--short'],text=True).splitlines())
spec=dict(version='0.1.0-tensile.11.1',af_version='0.0.0+tensilecrossbootcli1',baseline=dict(frozen_source=str(base),freeze_sha256=sha(base/'FREEZE.json'),**git),baseline_source_files={n:sha(p) for n,p in bf.items()},changes=changes,files={p.relative_to(dest).as_posix():sha(p) for p in dest.rglob('*') if p.is_file()})
write(dest/'SOURCE_MANIFEST.json',spec)
for name in ('SOURCE_MANIFEST.json','SOURCE_DIFF.patch','SOURCE_CHANGES.json'):shutil.copyfile(dest/name,z/name)
out=z/'evidence/RECONSTRUCTED_SOURCE'
subprocess.run([sys.executable,'-I','-B','-S',str(dest/'rebuild.py'),'--baseline',str(base),'--destination',str(out)],check=True,timeout=30)
assert all(sha(out/name)==sha(p) for name,p in nf.items())
write(z/'evidence/REBUILD_VERIFY.json',dict(reconstructed_source=str(out),nongenerated_source_match=True,source_recipe=str(dest/'rebuild.py'),source_manifest_sha256=sha(dest/'SOURCE_MANIFEST.json'),separate_site_bound_build_not_repeated=True))
paths=[]
for d in ('src','gd','af','tests','tools'):
 paths.extend(p for p in (z/d).rglob('*') if p.is_file())
paths.extend(p for p in z.iterdir() if p.is_file())
paths.extend(p for p in (z/'evidence').iterdir() if p.is_file())
paths.extend(p for p in (z/'evidence/INSTALLED_CLI_32c9b857b1a2457d8a5d844531df30c7').rglob('*') if p.is_file())
freeze=dict(status='DEVELOPMENT_FROZEN_PENDING_INDEPENDENT_ACCEPTANCE',version='0.1.0-tensile.11.1',af_version='0.0.0+tensilecrossbootcli1',package_pin=sha(z/'gd/package-manifest.json'),zip_sha256=sha(next(z.glob('*.zip'))),wheel_sha256=sha(next(z.glob('*.whl'))),source_manifest_sha256=sha(dest/'SOURCE_MANIFEST.json'),files={p.relative_to(z).as_posix():sha(p) for p in sorted(set(paths))})
write(z/'FREEZE.json',freeze)
print(json.dumps(dict(candidate=str(z),freeze_sha256=sha(z/'FREEZE.json'),files=len(freeze['files']),package_pin=freeze['package_pin'],zip_sha256=freeze['zip_sha256'],wheel_sha256=freeze['wheel_sha256'],source=str(dest),source_manifest_sha256=freeze['source_manifest_sha256']),indent=2))
