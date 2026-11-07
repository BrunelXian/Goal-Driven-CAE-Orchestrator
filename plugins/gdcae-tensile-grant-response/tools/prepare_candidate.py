from pathlib import Path
import json,hashlib
z=Path(r'D:\Projects\GDCAETEST\TENSILE-GRANT-RESPONSE-20261107-dev-4d9e7c1b20')
b=Path(r'D:\Projects\GDCAETEST\TENSILE-CROSSBOOT-CLI-FIX-20261106-dev-9bdbd25434')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=z/'src/gd/operator_entry.py';s=p.read_text(encoding='utf8');s=s.replace("grant = journal.call('authorize', args, lambda key: native.authorize(args, key, owner['owner_id']))", "from grant_response import authorize_once\n    grant = authorize_once(native, journal, args, owner['owner_id'], deadline=jit_deadline)")
p.write_text(s,encoding='utf8')
p=z/'src/gd/plugin.json';s=p.read_text(encoding='utf8').replace('0.1.0-tensile.11.1','0.1.0-tensile.12');p.write_text(s,encoding='utf8')
p=z/'tools/build.py';s=p.read_text(encoding='utf8').replace('0.1.0-tensile.11.1','0.1.0-tensile.12').replace('tensilecrossbootcli1','tensilegrant1');p.write_text(s,encoding='utf8')
a=z/'src/af/abqjobpilot_gdcae_internal-0.0.0+tensilecrossbootcli1.dist-info';q=a.with_name('abqjobpilot_gdcae_internal-0.0.0+tensilegrant1.dist-info');a.rename(q)
p=q/'METADATA';p.write_text(p.read_text(encoding='utf8').replace('tensilecrossbootcli1','tensilegrant1'),encoding='utf8')
spec=dict(schema='grant-response-readonly-runtime-v1',root=str(b),gd_root=str(b/'gd'),package_pin=sha(b/'gd/package-manifest.json'),freeze_sha256=sha(b/'FREEZE.json'),files={p.relative_to(b).as_posix():sha(p) for part in ('gd','af') for p in (b/part).rglob('*') if p.is_file()},scope='READ_ONLY_RECEIPT_CONFIRMATION_NEVER_EXECUTION_OR_OLD_PLAN_RENEWAL')
(z/'src/gd/grant_response_compatibility.json').write_text(json.dumps(spec,sort_keys=True,indent=2),encoding='utf8')
print('PREPARED')
