"""Reconstruct a new independent source candidate from exact frozen input + overlay.

Usage: absolute Python -I -B -S rebuild.py --baseline <.12> --destination <new>
Add --build to construct wheel/ZIP and pip --target into the new candidate only.
"""
import argparse,hashlib,json,shutil,subprocess,sys
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('--baseline',required=True);parser.add_argument('--destination',required=True);parser.add_argument('--build',action='store_true');a=parser.parse_args()
assert sys.version_info[:3]==(3,12,10) and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode
source=Path(__file__).resolve().parent;spec=json.loads((source/'SOURCE_MANIFEST.json').read_bytes())
base=Path(a.baseline).resolve();out=Path(a.destination).resolve()
assert Path(a.baseline).is_absolute() and Path(a.destination).is_absolute() and not out.exists() and out.parent.is_dir()
assert not out.is_relative_to(base) and not base.is_relative_to(out)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(base/'FREEZE.json')==spec['baseline']['freeze_sha256'],'BASELINE_FREEZE_CHANGED'
for name,pin in spec['baseline_source_files'].items():assert sha(base/name)==pin, name
for name,pin in spec['files'].items():assert sha(source/name)==pin,name
out.mkdir();(out/'evidence').mkdir()
for name in spec['baseline_source_files']:
    deleted=any(x['path']==name and x['after_sha256'] is None for x in spec['changes'])
    if deleted:continue
    p=out/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(base/name,p)
for item in spec['changes']:
    if item['after_sha256'] is None:continue
    p=out/item['path'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/'overlay'/item['path'],p)
for name in spec['files']:
    if name.startswith('overlay/'):continue
    p=out/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/name,p)
if a.build:subprocess.run([sys.executable,'-I','-B','-S',str(out/'tools/build.py')],check=True,timeout=180)
print(json.dumps({'status':'RECONSTRUCTED_SOURCE','destination':str(out),'installation_performed':a.build,'new_path_changes_site_bound_runtime_identity':True}))
