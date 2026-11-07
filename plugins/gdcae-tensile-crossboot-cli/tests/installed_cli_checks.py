"""Actual installed CLI subprocesses, no monkeypatch in proposal/check/commit.

Native isolated Plan/lifecycle fixtures are synthetic preboot evidence, not a
real machine restart. No actual site, Owner or Solver is operated.
"""
import sys,json,subprocess,uuid,time,hashlib
from pathlib import Path
z=Path(__file__).resolve().parents[1];root=z/'evidence'/('INSTALLED_CLI_'+uuid.uuid4().hex);root.mkdir()
checks=[];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check(n,v=True):assert v,n;checks.append(n)
def fixture():
    r=subprocess.run([sys.executable,'-I','-B','-S',str(z/'tests/build_cli_fixture.py')],capture_output=True,text=True,timeout=90)
    assert r.returncode==0,r.stderr
    return json.loads(r.stdout)
def cli(f,action,extra=(),ok=True):
    args=[sys.executable,'-I','-B','-S',str(z/'gd/cross_boot_archive.py'),action,'--project',f['project'],'--package-pin',f['package_pin'],'--python-exe',sys.executable,*extra]
    r=subprocess.run(args,capture_output=True,text=True,timeout=60)
    n=str(len(list(root.glob('call-*.json'))));(root/('call-'+n+'.json')).write_text(json.dumps(dict(args=args,code=r.returncode,stdout=r.stdout,stderr=r.stderr),indent=2))
    assert (r.returncode==0)==ok,(action,r.returncode,r.stderr)
    return json.loads(r.stdout) if ok else r.stderr
def create_proposal(f):
    result=cli(f,'proposal',['--identities',f['identities'],'--review',f['review']['path'],'--review-sha256',f['review']['sha256'],'--operation-id',f['operation_id']])
    path=Path(f['root'])/'PROPOSAL.json';path.write_text(json.dumps(result,indent=2));return result,path
def authorization(f,p):
    path=Path(f['root'])/'AUTHORIZATION_OFFLINE.json';path.write_text(json.dumps(dict(schema='cross-boot-exact-authorization-reference-v1',action='RECORD_HOST_RESTART_TERMINATED_UNCLEANLY',proposal_digest=p['proposal_digest'],operation_id=f['operation_id'],new_execution_authorized=False,budget_change_authorized=False,expires_at=int(time.time())+590,provenance='OFFLINE_TEST_ONLY_NOT_SITE_APPROVAL')))
    return path
f=fixture();p,path=create_proposal(f);pin=p['proposal_digest'];check('proposal_native_tagged_output',pin.startswith('sha256:') and len(pin)==71)
base=['--proposal',str(path),'--proposal-digest',pin]
check('installed_check_canonical',cli(f,'check',base)['proposal_digest']==pin)
check('explicit_legacy_bare_input_normalized',cli(f,'check',['--proposal',str(path),'--proposal-digest',pin[7:]])['proposal_digest']==pin)
for name,wrong in [('wrong_algorithm','sha512:'+pin[7:]),('duplicate_prefix','sha256:'+pin),('wrong_content','sha256:'+'f'*64),('whitespace',' '+pin),('uppercase',pin.upper())]:
    cli(f,'check',['--proposal',str(path),'--proposal-digest',wrong],ok=False);checks.append(name+'_rejected')
bad=Path(f['root'])/'WRONG_OBJECT.json';v=json.loads(path.read_bytes());v['proposal']['operation_id']='0'*32;bad.write_text(json.dumps(v))
cli(f,'check',['--proposal',str(bad),'--proposal-digest',pin],ok=False);checks.append('changed_object_rejected')
auth=authorization(f,p);authargs=['--authorization',str(auth),'--authorization-sha256',sha(auth)]
for name,wrong in [('wrong_algorithm','sha512:'+pin[7:]),('duplicate_algorithm','sha256:'+pin),('wrong_object','sha256:'+'f'*64)]:
    cli(f,'commit',['--proposal',str(path),'--proposal-digest',wrong]+authargs,ok=False);checks.append('commit_'+name+'_rejected')
before=(sha(f['native_db']),sha(f['workflow_db']))
result=cli(f,'commit',base+authargs);check('installed_native_commit',not result['replayed'] and result['terminal']['state']=='HOST_RESTART_TERMINATED_UNCLEANLY')
check('stored_canonical_digest',result['terminal']['record']['proposal_digest']==pin)
again=cli(f,'commit',base+authargs);check('installed_duplicate_no_second_write',again['replayed'])
view=cli(f,'reconcile');check('installed_reconcile',view['terminal']['record']==result['terminal']['record'])
check('native_and_scientific_db_unchanged',before==(sha(f['native_db']),sha(f['workflow_db'])))
badapproval=json.loads(auth.read_bytes());badapproval['proposal_digest']=pin[7:];badpath=Path(f['root'])/'WRONG_BARE_APPROVAL.json';badpath.write_text(json.dumps(badapproval))
cli(f,'commit',base+['--authorization',str(badpath),'--authorization-sha256',sha(badpath)],ok=False);checks.append('bare_approval_not_silently_rewritten')
# Separate fixture: persist the exact native protected intent shape to model a
# crash after write_new intent, before terminal. No CLI production function is patched.
g=fixture();q,qpath=create_proposal(g);qa=authorization(g,q)
sys.path[:0]=[str(z/'gd'),str(z/'gd/runtime')]
from r3_bridge import trusted_af
trusted_af()
from abqjobpilot.service_lifecycle import ServiceLifecycleManager,write_new
from abqjobpilot.local_credentials import private_value
m=ServiceLifecycleManager(g['project'])
write_new(m._path(g['native_start']+'/cross-boot-terminal-intent.json'),private_value(m.context,dict(proposal_digest=q['proposal_digest'],operation_id=g['operation_id'],authorization_reference=dict(path=str(qa),sha256=sha(qa)))))
check('partial_reopen_is_intent_only',cli(g,'reconcile')['intent_exists'] is True and cli(g,'reconcile')['terminal'] is None)
cli(g,'commit',['--proposal',str(qpath),'--proposal-digest',q['proposal_digest'],'--authorization',str(qa),'--authorization-sha256',sha(qa)],ok=False);checks.append('partial_not_retried')
out=dict(classification='ACTUAL_INSTALLED_CLI_NATIVE_SQLITE_DPAPI_SYNTHETIC_PREBOOT_FIXTURE',passed=len(checks),checks=checks,fixtures=[f,g],real_site_changed=False,solver_calls=0,owner_calls=0,
    interruption='EXACT_PROTECTED_INTENT_FIXTURE_CONSTRUCTION_NOT_OS_PROCESS_KILL')
(root/'RESULTS.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
