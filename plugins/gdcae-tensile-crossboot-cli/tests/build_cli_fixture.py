"""OFFLINE_TEST_ONLY: actual SQLite/AF Plan; synthetic A and stopped process proof.
No real Owner, Grant, Run, Solver, D7 or SP mutation. Native snapshot transport
is in-process to retain explicitly synthetic A proof; real profile code runs.
"""
import json,sys,hashlib,time,uuid,sqlite3,copy,subprocess,re
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
z=Path(__file__).resolve().parents[1];sys.path[:0]=[str(z/'gd'),str(z/'gd/runtime')]
import workflow,tensile,native_feedback,b_admission as b,execution_windows as r
from r3_bridge import trusted_af
trusted_af()
from abqjobpilot.service_lifecycle import ServiceLifecycleManager,write_new
from abqjobpilot.product_standard import inspect_preparation
from abqjobpilot.execution.models import canonical_json,digest
from abqjobpilot.execution.lifecycle import STOP
from abqjobpilot.execution.tensile_profile import spec_config
root=z/'evidence'/('OFFLINE_CROSS_BOOT-'+uuid.uuid4().hex[:10]);root.mkdir();work=root/'research'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
model=Path(r'D:\Projects\GDCAETEST\TENSILE-V1-R3-ADMISSION-20261105-dev-93a1ef42\model')
target=Path(r'D:\Projects\GDCAETEST\TENSILE-V1-PUBLIC-TARGET-20261104-69d2a041ef\target_force_displacement.csv')
package=sha(z/'gd/package-manifest.json')
init=workflow.initialize(work,model,target,sha(target),'PREPARE_ONLY',package,'OFFLINE_TEST_ONLY')
camp=workflow.Campaign(work,init['contract_sha256'],package)
a=camp.prepare('A');frames=tensile.fixture_curve(a['request']['parameters'])
feedback=dict(classification='NATIVE_ODB',binding={'run_id':'OFFLINE_TEST_ONLY_SYNTHETIC_A'},frames=frames,assessment=tensile.compare(camp.target,frames,a['request']['parameters']))
real_run=subprocess.run;checks=[]
real_time=time.time;clock_offset=0
clock_patch=patch.object(time,'time',lambda:real_time()+clock_offset);clock_patch.start()
real_ns=time.time_ns;patch.object(time,'time_ns',lambda:real_ns()+int(clock_offset*1e9)).start()
real_source=native_feedback.source;real_extract=native_feedback.extract;real_verify=native_feedback.verify
def check(name,value=True):assert value,name;checks.append(name)
def reject(name,call):
    try:call()
    except Exception:checks.append(name)
    else:raise AssertionError('accepted: '+name)
def finish():
    camp.db.close()
    out=dict(classification='OFFLINE_TEST_ONLY_REAL_SQLITE_AND_NATIVE_PLAN_SYNTHETIC_A_STOP_AND_SNAPSHOT_TRANSPORT',mode=sys.argv[1:] or ['normal'],passed=len(checks),checks=checks,root=str(root),solver_calls=0,owner_calls=0)
    (root/'RESULTS.json').write_bytes(r.c.pack(out));print(json.dumps(out))
def transport(args,*other,**kw):
    if isinstance(args,list) and len(args)>4 and str(args[4]).endswith('admission_snapshot.py'):
        assert args[5]==str(work)
        fn=r.snapshot if args[6].startswith('b-window:') else b.snapshot
        try:return SimpleNamespace(returncode=0,stdout=json.dumps(fn(camp,args[7] if len(args)>7 else '--preparation')).encode(),stderr=b'')
        except Exception as e:return SimpleNamespace(returncode=2,stdout=b'',stderr=str(e).encode())
    return real_run(args,*other,**kw)

def synthetic_stop(result):
    p=result['new']['plan'];assert p['registration']['purpose']=='OFFLINE_TEST_ONLY'
    m=ServiceLifecycleManager(result['new']['af_project']);ctx=m.context;profile=m._profile()
    start='start_'+uuid.uuid4().hex;owner='owner_'+uuid.uuid4().hex;op='stop_'+uuid.uuid4().hex;key='stop_'+uuid.uuid4().hex
    base=m._path(start);base.mkdir();process=dict(pid=2147483647,creation_time_100ns=3,image_path='OFFLINE_SYNTHETIC_WORKER')
    intent=dict(start_id=start,context_digest=ctx.context_digest,profile_digest=digest(profile),recorded_at=int(time.time()),requester_host={'OFFLINE_TEST_ONLY':True})
    receipt=dict(operation_id=op,action=STOP,owner_id=owner,project_instance_id=ctx.project_instance_id,start_id=start,
        operation_key=key,recorded_at=int(time.time()),state='STOP_COMMITTED',source='explicit_lifecycle_operator_capability',effects=['PAUSED','orderly_idle_stop'],not_evidence_of='Solver or unknown descendant exit')
    docs={'intent.json':intent,'created.json':dict(start_id=start,transport_pid=2147483646,recorded_at=int(time.time())),
       'ready.json':dict(owner_id=owner,start_id=start,recorded_at=int(time.time()),process=process),
       'stopped.json':dict(start_id=start,context_digest=ctx.context_digest,receipt=receipt,recorded_at=int(time.time())),
       'claimed.json':dict(start_id=start,context_digest=ctx.context_digest,recorded_at=int(time.time())),
       'host.json':dict(process=process,classification='OFFLINE_SYNTHETIC_NO_OWNER')}
    for name,v in docs.items():write_new(base/name,v)
    write_new(m._path('lifecycle-current.json'),intent);write_new(Path(ctx.root)/'owner.json',{'owner_id':owner})
    db=sqlite3.connect(Path(ctx.root)/'execution.sqlite3')
    db.execute("UPDATE meta SET value='1' WHERE key='supervisor_started'");db.execute('UPDATE dispatch_gate SET version=3,owner_id=?',(owner,))
    ns=canonical_json([ctx.project_instance_id,profile['client_namespace'],STOP]);fp=digest(dict(owner_id=owner,start_id=start,action=STOP,key=key))
    db.execute('INSERT INTO management_receipts VALUES(?,?,?,?,?)',(ns,key,fp,op,canonical_json(receipt)))
    db.execute('INSERT INTO control_events(body) VALUES(?)',(canonical_json(receipt),));db.commit();db.close()
    pr,_=b.record(camp);binding={k:pr[k] for k in ('operation_id','state','body_pin','result_pin')}
    research=dict(contract_sha256=camp.pin,budget=b.BUDGET if hasattr(b,'BUDGET') else r.BUDGET,binding=binding,
        workflow_sha256=sha(work/'workflow.sqlite'),A_result_sha256=sha_bytes(camp.db.execute("SELECT result FROM stages WHERE phase='A'").fetchone()[0]))
    identities=[process,dict(pid=2147483646,creation_time_100ns=2,image_path='OFFLINE_SYNTHETIC_TRANSPORT'),dict(pid=2147483645,creation_time_100ns=3,image_path=r'C:\Windows\System32\conhost.exe')]
    store=dict(plan_id=p['plan_id'],plan_digest=p['plan_digest'],scope_digest=result['new']['scope_digest'])
    before=dict(owner=owner,start=start,project_id=ctx.project_id,instance=ctx.project_instance_id,store=store,research=research,processes=identities)
    after=dict(status='NATIVE_IDLE_STOP_RECORDED_EXIT_OBSERVED',receipt=receipt,orderly_stop=dict(state='NOT_RUNNING',reason='ORDERLY_STOP_RECORDED'),store=store,research=research,solver_started=False,budget_changed=False,
        process_exits=[{**i,'exit_code':0,'exit_source':'retained_windows_handle','exit_observed_at':int(time.time())} for i in identities])
    report=dict(verdict='PASS_B_NATIVE_IDLE_STOP_AND_THREE_RETAINED_EXITS',classification='OFFLINE_SYNTHETIC_NOT_INDEPENDENT_REAL_REVIEW',receipt=receipt,exits=after['process_exits'],
        B_preparation=binding,A_result_sha256=research['A_result_sha256'],research_sha256=research['workflow_sha256'],budget=r.BUDGET,B_solver_execution_count=0,native_stop_count=1)
    proof=root/('synthetic-stop-'+uuid.uuid4().hex);proof.mkdir()
    for n,v in [('before.json',before),('after.json',after),('review.json',report)]: (proof/n).write_bytes(r.c.pack(v))
    (proof/'index.json').write_bytes(r.c.pack({str(proof/n):{'sha256':sha(proof/n)} for n in ('before.json','after.json')}))
    ref=dict(schema='retained-stop-review-reference-v1',**{k:dict(path=str(proof/n),sha256=sha(proof/n)) for k,n in [('pre_call','before.json'),('final','after.json'),('review','review.json'),('index','index.json')]})
    if 'execution_window' in p['registration']:
        from abqjobpilot.local_credentials import private_value
        import window_closure
        process['parent_pid']=2147483646
        ready=dict(docs['ready.json'],process=process)
        (base/'ready.json').write_bytes(r.c.pack(ready)) # fixture construction only
        ids=[{k:process[k] for k in ('pid','creation_time_100ns','image_path')},dict(pid=2147483646,creation_time_100ns=2,image_path=r'D:\OFFLINE\python.exe')]
        payload=dict(schema=window_closure.SCHEMA,classification='MACHINE_EVIDENCE_NOT_INDEPENDENT_HUMAN_APPROVAL',
            project_id=ctx.project_id,project_instance_id=ctx.project_instance_id,context_digest=ctx.context_digest,
            plan_id=p['plan_id'],plan_digest=p['plan_digest'],scope_digest=result['new']['scope_digest'],
            execution_window=p['registration']['execution_window'],research_project=camp.c['project'],contract=camp.pin,budget=r.BUDGET,
            receipt=receipt,ready=ready,created=docs['created.json'],identities=ids,
            exits=[dict(v,exit_code=0,exit_source='retained_windows_handle') for v in ids],member_scope='OFFLINE_SYNTHETIC_TWO_MEMBERS')
        path=proof/'machine-closure.json';write_new(path,private_value(ctx,payload))
        ref=dict(schema=window_closure.SCHEMA,path=str(path),sha256=sha(path))
        check('machine_qualification_fixture_'+str(p['registration']['execution_window']['window_revision']))
    return ref,m
sha_bytes=lambda x:hashlib.sha256(x).hexdigest()

from abqjobpilot import cross_boot_terminal as cb
from abqjobpilot.local_credentials import private_value
from abqjobpilot.execution.models import ExecutionError
import window_history
boot=cb.boot_observation()
(root/'REAL_READONLY_BOOT.json').write_text(json.dumps(boot))
check('real_kernel_CIM_event12_agree',boot['source']=='Kernel+CIM+Kernel-General-12')

def setup_incident(result):
    m=ServiceLifecycleManager(result['new']['af_project']);ctx=m.context;p=result['new']['plan'];profile=m._profile()
    start='start_'+uuid.uuid4().hex;owner='owner_'+uuid.uuid4().hex;base=m._path(start);base.mkdir()
    identities=[dict(pid=2147483647,creation_time_100ns=boot['boot_time_100ns']-300000000,image_path=r'D:\OFFLINE\python.exe'),
                dict(pid=2147483646,creation_time_100ns=boot['boot_time_100ns']-310000000,image_path=r'D:\OFFLINE\python.exe'),
                dict(pid=2147483645,creation_time_100ns=boot['boot_time_100ns']-305000000,image_path=r'C:\Windows\System32\conhost.exe')]
    proc=dict(identities[0],parent_pid=identities[1]['pid'],executable=r'D:\OFFLINE\python.exe')
    intent=dict(start_id=start,context_digest=ctx.context_digest,profile_digest=digest(profile),recorded_at=int((boot['boot_time_100ns']-116444736000000000)/10000000)-30,requester_host={'OFFLINE_SIMULATED_PREVIOUS_BOOT':True})
    docs={'intent.json':intent,'created.json':dict(start_id=start,transport_pid=identities[1]['pid']),
          'ready.json':dict(start_id=start,owner_id=owner,process=proc),'claimed.json':dict(start_id=start),'host.json':dict(process=proc)}
    for n,v in docs.items():write_new(base/n,v)
    endpoint=dict(owner_id=owner,process=proc)
    write_new(m._path('lifecycle-current.json'),intent);write_new(Path(ctx.root)/'owner.json',endpoint)
    write_new(m._path('connection.json'),private_value(ctx,dict(endpoint=endpoint,credential=profile['credential'])))
    db=sqlite3.connect(Path(ctx.root)/'execution.sqlite3');db.execute("UPDATE meta SET value='1' WHERE key='supervisor_started'");db.execute('UPDATE dispatch_gate SET owner_id=?',(owner,));db.commit();db.close()
    journal=root/('known-helper-'+uuid.uuid4().hex);journal.mkdir();(journal/'STOP_UNKNOWN.json').write_text('{"stop_request_exists":false}')
    review=dict(schema='cross-boot-independent-review-v1',scope='KNOWN_BOUND_SOURCES_RECONCILED',unresolved_native_operation=False,
        project_id=ctx.project_id,project_instance_id=ctx.project_instance_id,owner_id=owner,start_id=start,plan_id=p['plan_id'],
        process_identities=identities,scientific_commit_guard={str(work/'workflow.sqlite'):sha(work/'workflow.sqlite')},known_operator_journals=[dict(root=str(journal),request_exists=False,files={'STOP_UNKNOWN.json':sha(journal/'STOP_UNKNOWN.json')})],
        classification='OFFLINE_SYNTHETIC_REVIEW_NOT_REAL_TESTING')
    reviewpath=root/('review-'+uuid.uuid4().hex+'.json');reviewpath.write_bytes(r.c.pack(review))
    return m,identities,[dict(path=str(reviewpath),sha256=sha(reviewpath))]


clock_offset=-120
with patch.object(native_feedback,'source',lambda *a:None),patch.object(native_feedback,'extract',lambda *a:feedback),patch.object(native_feedback,'verify',lambda c,row:json.loads(row['result'])):
    camp.observe('A',a['request_sha256'],'NATIVE');prep=camp.prepare('B')
    accepted=dict(source_A_result_sha256=sha_bytes(camp.db.execute("SELECT result FROM stages WHERE phase='A'").fetchone()[0]),decision_reference={'path':'OFFLINE_SYNTHETIC','sha256':'OFFLINE_TEST_ONLY'})
    with patch.object(b,'decision',lambda camp:(accepted,{})),patch.object(subprocess,'run',transport):
        op=uuid.uuid4().hex;p=b.proposal(camp,op);result=b.prepare(camp,p,b.c.pin(p),int(time.time())+60)
        m,identities,refs=setup_incident(result)
camp.db.close();clock_patch.stop()
(root/'IDENTITIES.json').write_text(json.dumps(identities,indent=2))
fixture=dict(root=str(root),project=result['new']['af_project'],identities=str(root/'IDENTITIES.json'),review=refs[0],operation_id=uuid.uuid4().hex,package_pin=package,
    native_start=m._current()['start_id'],native_private=str(m.private),native_db=str(Path(m.context.root)/'execution.sqlite3'),workflow_db=str(work/'workflow.sqlite'),classification='OFFLINE_NATIVE_PLAN_WITH_SYNTHETIC_PREBOOT_LIFECYCLE')
(root/'FIXTURE.json').write_text(json.dumps(fixture,indent=2));print(json.dumps(fixture))
