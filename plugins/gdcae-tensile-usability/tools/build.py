"""Canonical wheel/ZIP source build and fresh independent installation.

The wheel contains no installer provenance. pip owns installed direct_url,
INSTALLER, REQUESTED and installation RECORD. No shared environment changes.
"""
import base64,csv,hashlib,io,json,subprocess,sys,zipfile
from pathlib import Path
z=Path(__file__).resolve().parents[1]
gs=z/'src/gd';afs=z/'src/af';g=z/'gd';a=z/'af';pkg=afs/'abqjobpilot'
assert not g.exists() and not a.exists(),'Fresh install targets required; do not overwrite an installed candidate'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
catalog=pkg/'execution/tensile_catalog.py'
files={p.relative_to(afs).as_posix():sha(p) for p in sorted(pkg.rglob('*')) if p.is_file() and p!=catalog}
(gs/'af_installation.py').write_bytes(('ROOT='+repr(str(a))+'\nFILES='+repr(files)+'\nGD_ROOT='+repr(str(g))+'\n').encode())
gd_files={p.relative_to(gs).as_posix():sha(p) for p in sorted(gs.rglob('*.py'))}
catalog.write_bytes(('AF_ROOT='+repr(str(a))+'\nGD_ROOT='+repr(str(g))+'\nGD_FILES='+repr(gd_files)+'\n').encode())
manifest={p.relative_to(gs).as_posix():sha(p) for p in sorted(gs.rglob('*')) if p.is_file() and p.name!='package-manifest.json'}
(gs/'package-manifest.json').write_bytes(json.dumps({'files':manifest},sort_keys=True,indent=2).encode())
di=afs/'abqjobpilot_gdcae_internal-0.0.0+tensileusability1.dist-info'
assert {p.name for p in di.iterdir()}=={'METADATA','WHEEL'},'Source metadata is not a clean wheel specification'
payload={p.relative_to(afs).as_posix():p.read_bytes() for p in sorted(afs.rglob('*')) if p.is_file()}
record=io.StringIO(newline='');w=csv.writer(record,lineterminator='\n')
for name,raw in sorted(payload.items()):w.writerow([name,'sha256='+base64.urlsafe_b64encode(hashlib.sha256(raw).digest()).decode().rstrip('='),len(raw)])
rn=di.name+'/RECORD';w.writerow([rn,'','']);payload[rn]=record.getvalue().encode()
def archive(path,payload):
    with zipfile.ZipFile(path,'w') as f:
        for name,raw in sorted(payload.items()):f.writestr(zipfile.ZipInfo(name,(2026,1,1,0,0,0)),raw,compress_type=zipfile.ZIP_DEFLATED)
wheel=z/'abqjobpilot_gdcae_internal-0.0.0+tensileusability1-py3-none-any.whl'
archive(wheel,payload)
pluginzip=z/'gdcae-tensile-v1-0.1.0-tensile.10.zip'
archive(pluginzip,{'plugins/gdcae-tensile-v1/'+p.relative_to(gs).as_posix():p.read_bytes() for p in gs.rglob('*') if p.is_file()})
command=[sys.executable,'-I','-B','-m','pip','--isolated','install','--no-index','--no-deps','--no-compile','--target',str(a),str(wheel)]
installed=subprocess.run(command,capture_output=True,text=True,timeout=120)
(z/'evidence/pip-install.stdout.txt').write_text(installed.stdout,encoding='utf8')
(z/'evidence/pip-install.stderr.txt').write_text(installed.stderr,encoding='utf8')
(z/'evidence/pip-install-command.json').write_text(json.dumps(command,indent=2),encoding='utf8')
assert installed.returncode==0,installed.stderr
g.mkdir()
with zipfile.ZipFile(pluginzip) as archive_file:
    prefix='plugins/gdcae-tensile-v1/'
    for info in archive_file.infolist():
        assert info.filename.startswith(prefix) and '..' not in Path(info.filename).parts
        destination=g/info.filename[len(prefix):]
        destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(archive_file.read(info))
installed_di=a/di.name
url=json.loads((installed_di/'direct_url.json').read_bytes())
assert url['archive_info']['hashes']['sha256']==sha(wheel)
from urllib.parse import unquote
assert unquote(url['url'])==unquote(wheel.as_uri())
assert (installed_di/'INSTALLER').read_text().strip()=='pip'
for name,raw in payload.items():
    if name.endswith('/RECORD'):continue
    assert (a/name).read_bytes()==raw,name
extras={p.relative_to(a).as_posix() for p in a.rglob('*') if p.is_file()}-set(payload)
assert extras=={di.name+'/'+n for n in ('direct_url.json','INSTALLER','REQUESTED')},extras
for row in csv.reader(io.StringIO((installed_di/'RECORD').read_text())):
    name,h,size=row;p=a/name
    assert p.is_file()
    if h:
        assert h=='sha256='+base64.urlsafe_b64encode(hashlib.sha256(p.read_bytes()).digest()).decode().rstrip('=') and int(size)==p.stat().st_size
result={'gd':str(g),'af':str(a),'package_pin':sha(g/'package-manifest.json'),'wheel':str(wheel),'wheel_sha256':sha(wheel),
        'direct_url':url,'actual_installation':'pip --isolated --no-index --no-deps --no-compile --target; exit 0',
        'wheel_payload_match':True,'installed_RECORD_verified':True,'installer_generated_files':sorted(extras)}
(z/'evidence/INSTALLATION.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps(result))
