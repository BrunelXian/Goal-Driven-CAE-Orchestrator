"""Source/installation freeze; no native or research API calls."""
import hashlib,json,shutil,subprocess,sys,difflib
from pathlib import Path
z=Path(__file__).resolve().parents[1]
b=Path(r'D:\Projects\GDCAETEST\TENSILE-GRANT-RESPONSE-20261107-dev-4d9e7c1b20')
repo=Path(r'D:\Projects\Goal-Driven-CAE-Orchestrator');dest=repo/'plugins/gdcae-tensile-expired-grant'
assert not dest.exists() and not (z/'FREEZE.json').exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,sort_keys=True,indent=2),encoding='utf8')
generated={'src/gd/af_installation.py','src/gd/package-manifest.json','src/af/abqjobpilot/execution/tensile_catalog.py'}
files=lambda root:{p.relative_to(root).as_posix():p for p in (root/'src').rglob('*') if p.is_file() and p.relative_to(root).as_posix() not in generated}
bf,nf=files(b),files(z);changes=[];diff=[];dest.mkdir()
for name in sorted(set(bf)|set(nf)):
 before=sha(bf[name]) if name in bf else None;after=sha(nf[name]) if name in nf else None
 if before==after:continue
 changes.append(dict(path=name,before_sha256=before,after_sha256=after))
 if after:
  p=dest/'overlay'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(nf[name],p)
 diff.extend(difflib.unified_diff(bf[name].read_text(encoding='utf8').splitlines(True) if before else [],nf[name].read_text(encoding='utf8').splitlines(True) if after else [],fromfile='a/'+name,tofile='b/'+name))
for d in ('tests','tools'):shutil.copytree(z/d,dest/d)
for n in ('OPERATOR_CARD.md','DEVELOPMENT_REPORT.md'):shutil.copyfile(z/n,dest/n)
shutil.copyfile(repo/'plugins/gdcae-tensile-grant-response/rebuild.py',dest/'rebuild.py')
p=dest/'rebuild.py';p.write_text(p.read_text(encoding='utf8').replace('baseline <.9>','baseline <.12>'),encoding='utf8')
(dest/'SOURCE_DIFF.patch').write_text(''.join(diff),encoding='utf8');write(dest/'SOURCE_CHANGES.json',changes)
git={}
for n,r in [('gd',repo),('af',Path(r'D:\Projects\abqjobpilot_dev'))]:
 git[n]=dict(path=str(r),commit=subprocess.check_output(['git','-C',str(r),'rev-parse','HEAD'],text=True).strip(),status=subprocess.check_output(['git','-C',str(r),'status','--short'],text=True).splitlines())
spec=dict(version='0.1.0-tensile.13',af_version='0.0.0+tensileexpiredgrant1',baseline=dict(frozen_source=str(b),freeze_sha256=sha(b/'FREEZE.json'),**git),baseline_source_files={n:sha(p) for n,p in bf.items()},changes=changes,files={p.relative_to(dest).as_posix():sha(p) for p in dest.rglob('*') if p.is_file()})
write(dest/'SOURCE_MANIFEST.json',spec)
for n in ('SOURCE_DIFF.patch','SOURCE_CHANGES.json','SOURCE_MANIFEST.json'):shutil.copyfile(dest/n,z/n)
out=z/'evidence/RECONSTRUCTED_SOURCE'
subprocess.run([sys.executable,'-I','-B','-S',str(dest/'rebuild.py'),'--baseline',str(b),'--destination',str(out)],check=True,timeout=30)
assert all(sha(out/name)==sha(p) for name,p in nf.items())
write(z/'evidence/SOURCE_REBUILD.json',dict(source_manifest_sha256=sha(dest/'SOURCE_MANIFEST.json'),reconstructed_source=str(out),all_nongenerated_source_bytes_equal=True,site_bound_installation_rebuild_not_repeated=True))
paths=[]
for d in ('src','gd','af','tests','tools'):paths.extend(p for p in (z/d).rglob('*') if p.is_file())
paths.extend(p for p in z.iterdir() if p.is_file())
paths.extend(p for p in (z/'evidence').iterdir() if p.is_file())
for folder in (z/'evidence').iterdir():
 if folder.is_dir() and folder.name.startswith(('MACHINE_TEST_GRANT_RESPONSE_','COORDINATOR_','EXPIRED_GRANT_','MACHINE_TEST_ARCHIVE_TX_')):
  paths.extend(p for p in folder.rglob('*') if p.is_file() and p.name in ('RESULTS.json','host.stdout.log','host.stderr.log','CLI_RECOVERY.stdout.json','CLI_RECOVERY.stderr.txt','CLI_NEGATIVE_RESULTS.json','EXPIRED_GRANT_REJECTIONS.json','ARCHIVE_RESULT.json','REJECTION_RESULTS.json','ARCHIVE_PROPOSAL.json','CLOSURE_REFERENCE.json','RECOVERED.json','STOP_AND_CLOSURE.json','STOP_INTENT.json','TEST_ONLY_AUTHORIZATION_SCOPE.json','CLI_SUBPROCESS_RESULTS.json','CONCURRENT_RESULTS.json','read.stdout.json','read.stderr.txt','archive.stdout.json','archive.stderr.txt'))
f=dict(status='DEVELOPMENT_FROZEN_PENDING_INDEPENDENT_ACCEPTANCE',version='0.1.0-tensile.13',af_version='0.0.0+tensileexpiredgrant1',package_pin=sha(z/'gd/package-manifest.json'),zip_sha256=sha(next(z.glob('*.zip'))),wheel_sha256=sha(next(z.glob('*.whl'))),source_manifest_sha256=sha(dest/'SOURCE_MANIFEST.json'),files={p.relative_to(z).as_posix():sha(p) for p in sorted(set(paths))})
write(z/'FREEZE.json',f)
print(json.dumps(dict(candidate=str(z),freeze_sha256=sha(z/'FREEZE.json'),files=len(f['files']),package_pin=f['package_pin'],zip_sha256=f['zip_sha256'],wheel_sha256=f['wheel_sha256'],source=str(dest),source_manifest_sha256=f['source_manifest_sha256']),indent=2))
