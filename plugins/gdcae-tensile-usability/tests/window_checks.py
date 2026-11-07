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
root=z/'evidence'/('offline-b-reentry-'+uuid.uuid4().hex[:10]);root.mkdir();work=root/'research'
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

with patch.object(native_feedback,'source',lambda *a:None),patch.object(native_feedback,'extract',lambda *a:feedback),patch.object(native_feedback,'verify',lambda c,row:json.loads(row['result'])):
    camp.observe('A',a['request_sha256'],'NATIVE');prep=camp.prepare('B');req=prep['request'];old_request=camp.db.execute("SELECT request FROM stages WHERE phase='B'").fetchone()[0]
    accepted=dict(source_A_result_sha256=sha_bytes(camp.db.execute("SELECT result FROM stages WHERE phase='A'").fetchone()[0]),decision_reference={'path':'OFFLINE_SYNTHETIC','sha256':'OFFLINE_TEST_ONLY'})
    with patch.object(b,'decision',lambda camp:(accepted,{})),patch.object(subprocess,'run',transport),patch.object(r,'compatibility',lambda:{'package':package}),patch.object(r.legacy,'compatibility',lambda:{'package':package}):
        op=uuid.uuid4().hex;p=b.proposal(camp,op);old=b.prepare(camp,p,b.c.pin(p),int(time.time())+120)
        clock_offset+=130;ref,m=synthetic_stop(old)
        before_a=camp.db.execute("SELECT result FROM stages WHERE phase='A'").fetchone()[0]
        for index in range(3):
            op=uuid.uuid4().hex;p=r.proposal(camp,op,ref)
            check('revision_'+str(index+1),p['window_revision']==index+1)
            check('same_scientific_request_'+str(index),p['original_request']==sha_bytes(old_request) and p['candidate']==req['candidate_id'])
            reject('wrong_proposal_pin_'+str(index),lambda:r.claim(camp,p,'f'*64,int(time.time())+600))
            reject('expired_new_window_'+str(index),lambda:r.claim(camp,p,r.c.pin(p),int(time.time())-1))
            expiry=int(time.time())+600
            result=r.prepare(camp,p,r.c.pin(p),expiry)
            check('native_plan_and_current_snapshot_'+str(index),inspect_preparation(result['new']['af_project'])['plan']==result['new']['plan'] and r.snapshot(camp,'--committed')['result']==result)
            check('scientific_hold_no_reset_'+str(index),camp.counts(camp.verified_rows())==r.BUDGET)
            check('A_result_unchanged_'+str(index),camp.db.execute("SELECT result FROM stages WHERE phase='A'").fetchone()[0]==before_a)
            reject('nonexpired_parent_no_new_window_'+str(index),lambda:r.proposal(camp,uuid.uuid4().hex,ref))
            if index<2:
                clock_offset+=610;ref,m=synthetic_stop(result)
        r0,body=r.record(camp);stored=r0['result'];storedpin=r0['result_pin']
        for name,alter in [('plan_id',lambda v:v['new']['plan'].__setitem__('plan_id','wrong')),('scope',lambda v:v['new'].__setitem__('scope_digest','wrong'))]:
            bad=json.loads(stored);alter(bad)
            camp.db.execute('UPDATE '+r.TABLE+' SET result=?,result_pin=? WHERE operation_id=?',(r.c.pack(bad),r.c.pin(bad),op))
            reject('native_rejects_forged_'+name,lambda:inspect_preparation(result['new']['af_project']))
            camp.db.execute('UPDATE '+r.TABLE+' SET result=?,result_pin=? WHERE operation_id=?',(stored,storedpin,op))
        history=camp.db.execute("SELECT seq,request_pin FROM history WHERE phase='B'").fetchone()
        camp.db.execute('UPDATE history SET request_pin=? WHERE seq=?',('wrong',history['seq']))
        reject('native_rejects_forged_history',lambda:inspect_preparation(result['new']['af_project']))
        camp.db.execute('UPDATE history SET request_pin=? WHERE seq=?',(history['request_pin'],history['seq']))
        camp.db.execute("UPDATE stages SET state='INTENT' WHERE phase='B'");camp.record('B','INTENT',old_request)
        check('terminal_INTENT_reads_same_binding',r.effective(camp,camp.db.execute("SELECT * FROM stages WHERE phase='B'").fetchone())[0]==body['effective_request'])
        reject('science_INTENT_cannot_authorize',lambda:inspect_preparation(result['new']['af_project']))
        camp.db.execute("DELETE FROM history WHERE phase='B' AND event='INTENT'");camp.db.execute("UPDATE stages SET state='PREPARED' WHERE phase='B'")
        final=r.reconcile(camp,op);check('readonly_reconcile_committed',final['state']=='COMMITTED')
        clock_offset+=610
        # Real SQLite write CAS in two threads; fixture-only removal of the
        # losing test's durable INTENT restores the fixture for later crash tests.
        from concurrent.futures import ThreadPoolExecutor
        pa=r.proposal(camp,uuid.uuid4().hex,ref);pb=r.proposal(camp,uuid.uuid4().hex,ref)
        def compete(proposal):
            cc=workflow.Campaign(work,init['contract_sha256'],package)
            try:
                r.claim(cc,proposal,r.c.pin(proposal),int(time.time())+600);return 'CLAIMED'
            except Exception:return 'REFUSED'
            finally:cc.db.close()
        with ThreadPoolExecutor(2) as pool:winners=list(pool.map(compete,[pa,pb]))
        check('concurrent_same_parent_one_CAS_winner',sorted(winners)==['CLAIMED','REFUSED'])
        reject('pending_blocks_prepare',lambda:r.proposal(camp,uuid.uuid4().hex,ref))
        pendingrows=[v for v in r.rows(camp) if v['state']=='INTENT'];check('one_durable_pending',len(pendingrows)==1)
        camp.db.execute('DELETE FROM '+r.TABLE+" WHERE state='INTENT'")  # isolated fixture reset only
        operation=uuid.uuid4().hex;proposal=r.proposal(camp,operation,ref)
        original_finalize=r.finalize
        with patch.object(r,'finalize',side_effect=RuntimeError('OFFLINE_CRASH_AFTER_AF_BEFORE_GD_COMMIT')):
            reject('interrupted_after_AF_prepare',lambda:r.prepare(camp,proposal,r.c.pin(proposal),int(time.time())+600))
        pending=r.reconcile(camp,operation)
        check('AF_prepared_GD_intent_readonly_reconcile',pending['state']=='AF_PREPARED_GD_INTENT')
        reject('pending_cannot_authorize',lambda:inspect_preparation(proposal['new_af_project']))
        reject('pending_cannot_open_another_window',lambda:r.proposal(camp,uuid.uuid4().hex,ref))
        last_committed=r.effective(camp,camp.db.execute("SELECT * FROM stages WHERE phase='B'").fetchone())
        check('pending_does_not_switch_current',last_committed[0]==body['effective_request'])
        completed=original_finalize(camp,operation)
        check('explicit_same_operation_finalize',completed['operation_id']==operation)
        reject('finalize_not_repeated',lambda:original_finalize(camp,operation))
        # Native-shaped accepted Run/Receipt/consumption fixture: no native
        # authorization or Solver. This tests real schema and fact projection.
        import native_accounting as accounting
        current=completed['new']['plan'];manager=ServiceLifecycleManager(completed['new']['af_project'])
        ctx=manager.context;db=sqlite3.connect(Path(ctx.root)/'execution.sqlite3')
        from abqjobpilot.execution.models import CANONICAL,CONTRACT
        grant_id='g_OFFLINE_TEST_ONLY';run_id='r_OFFLINE_TEST_ONLY'
        grant=dict(grant_id=grant_id,plan_id=current['plan_id'],plan_digest=current['plan_digest'])
        run=dict(run_id=run_id,grant_id=grant_id,plan_id=current['plan_id'],plan_digest=current['plan_digest'],project_instance_id=ctx.project_instance_id,job_id=current['job_id'],job_revision=current['job_revision'])
        semantic=dict(contract_version=CONTRACT,operation='submit',project_id=ctx.project_id,project_instance_id=ctx.project_instance_id,job_id=current['job_id'],job_revision=current['job_revision'],plan_id=current['plan_id'],plan_digest=current['plan_digest'],grant_id=grant_id,retry_of=None,context_digest=ctx.context_digest,canonicalization=CANONICAL)
        namespace=canonical_json([ctx.project_instance_id,manager._profile()['client_namespace'],'submit'])
        receipt=dict(request_status='ACCEPTED',request_id='req_OFFLINE',namespace=namespace,idempotency_key='OFFLINE',request_digest=digest(semantic),run_id=run_id,job_id=current['job_id'],accepted_sequence=1)
        db.execute('INSERT INTO grants VALUES(?,?,?)',(grant_id,current['plan_id'],canonical_json(grant)))
        db.execute('INSERT INTO runs VALUES(?,?,?,?,?,?,?,?)',(run_id,current['job_id'],current['job_revision'],current['plan_id'],grant_id,1,None,canonical_json(run)))
        db.execute('INSERT INTO receipts VALUES(?,?,?,?,?)',(namespace,'OFFLINE',receipt['request_digest'],run_id,canonical_json(receipt)))
        db.execute('INSERT INTO consumption VALUES(?,?)',(grant_id,run_id))
        db.execute('INSERT INTO events(event_id,run_id,run_sequence,body) VALUES(?,?,?,?)',('ev_OFFLINE',run_id,1,canonical_json(dict(type='REQUEST_ACCEPTED',run_id=run_id,payload={'revision':1}))))
        db.commit()
        fact=accounting.record_acceptance(camp);check('native_fact_real_SQL_shape',fact['native_consumed']==1 and not fact['replayed'])
        check('native_fact_replay_no_duplicate',accounting.record_acceptance(camp)['replayed'] and camp.db.execute('SELECT count(*) FROM '+accounting.TABLE).fetchone()[0]==1)
        check('native_fact_preserves_frozen_charge_timing',camp.counts(camp.verified_rows())==r.BUDGET)
        reject('native_accepted_forbids_recovery',lambda:r.proposal(camp,uuid.uuid4().hex,ref))
        db.execute("UPDATE receipts SET request_digest='wrong'");db.commit()
        reject('fact_wrong_native_digest',lambda:accounting.source(camp))
        db.execute('UPDATE receipts SET request_digest=?',(receipt['request_digest'],));db.commit();db.close()
        bframes=tensile.fixture_curve(req['parameters']);bfeedback=dict(classification='NATIVE_ODB',binding={'run_id':run_id},frames=bframes,assessment=tensile.compare(camp.target,bframes,req['parameters']))
        with patch.object(native_feedback,'extract',lambda *a:bfeedback):
            outcome=accounting.feedback_once(camp,sha_bytes(old_request))
        check('scientific_feedback_same_original_B',outcome['phase']=='B')
        check('final_budget_once',camp.counts(camp.verified_rows())==dict(limit=2,held=0,charged=2,available=0))
        with patch.object(native_feedback,'extract',side_effect=AssertionError('MUST_NOT_EXTRACT_TWICE')):
            replay=accounting.feedback_once(camp,sha_bytes(old_request))
        check('committed_feedback_replay_without_extraction',replay['replayed'] and replay['budget']['charged']==2)
        check('NATIVE_effective_binding_reopens',r.effective(camp,camp.db.execute("SELECT * FROM stages WHERE phase='B'").fetchone())[0]['job']==current['job_name'])

finish()




