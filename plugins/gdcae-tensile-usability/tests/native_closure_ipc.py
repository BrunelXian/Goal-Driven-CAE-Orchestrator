"""Real isolated native IPC/handles/DPAPI; Plan/research descriptors are fixtures.

No execution authorization, submit, dispatch, Solver, or real B access.
"""
import sys,json,uuid,time,sqlite3
from pathlib import Path
from types import SimpleNamespace
z=Path(__file__).resolve().parents[1];sys.path[:0]=[str(z/'gd'),str(z/'gd/runtime')]
from r3_bridge import trusted_af
trusted_af()
import continuation as c
from window_closure import TrackedOwner,qualification
from abqjobpilot.product_project import create_project
from abqjobpilot.service_lifecycle import ServiceLifecycleManager
from abqjobpilot.execution.models import digest,canonical_json
from abqjobpilot.execution.product_standard import scope
root=z/'evidence'/('MACHINE_TEST_CLOSURE_'+uuid.uuid4().hex);root.mkdir();product=root/'OFFLINE_TEST_ONLY'
create_project(product,'MACHINE_TEST_CLOSURE_NO_SOLVER');m=ServiceLifecycleManager(product);ctx=m.context
checks=[];report={};tracked=None
def check(n,v=True):assert v,n;checks.append(n)
def reject(n,f):
    try:f()
    except Exception:checks.append(n)
    else:raise AssertionError(n)
plan=dict(plan_id='plan_OFFLINE_DESCRIPTOR',plan_digest='sha256:OFFLINE_DESCRIPTOR',context_digest=ctx.context_digest,
    project_instance_id=ctx.project_instance_id,backend_id='fake-v1',runtime_binding={},input_manifest=[],engineering=str(product/'engineering'),scratch='',
    job_name='OFFLINE_DESCRIPTOR',output_key='OFFLINE',resources={},process_management={},product_dispatch={},model_profile='OFFLINE_DESCRIPTOR',
    registration={'execution_window':{'schema':'expired-unexecuted-b-execution-window-v1','operation_id':uuid.uuid4().hex,'window_revision':1},'research_project':'rp_OFFLINE','contract':'OFFLINE'})
camp=SimpleNamespace(pin='OFFLINE',c={'project':'rp_OFFLINE'},counts=lambda rows:dict(limit=2,held=1,charged=1,available=0),verified_rows=lambda:[])
try:
    owner=m.start();check('native_CONNECTED',owner['state']=='CONNECTED')
    client,_,health=m.connect();tracked=TrackedOwner(m,health,owner)
    check('tracked_real_native_worker_transport',len(tracked.refs) in (1,2))
    reject('wrong_owner_rejected',lambda:tracked.verify(health,dict(owner,owner_id='wrong')))
    # Descriptor row is never passed to authorization/execute. It only gives
    # the machine-evidence parser its actual SQL Plan lookup shape.
    db=sqlite3.connect(Path(ctx.root)/'execution.sqlite3');db.execute('INSERT INTO plans VALUES(?,?,?,?)',(plan['plan_id'],'OFFLINE',1,canonical_json(plan)));db.commit();db.close()
    key='machine_stop_'+uuid.uuid4().hex;(root/'intent.json').write_text(json.dumps({'owner':owner,'key':key,'scope':'OFFLINE_ONLY_NORMAL_IDLE_STOP'}))
    stop=m.stop(owner_id=owner['owner_id'],operation_key=key)
    done=tracked.exit_record(owner,stop)
    check('completion_exit_record_is_not_readmission',done['unexecuted_readmission_qualification'] is False and len(done['exits'])==len(tracked.refs))
    ref=tracked.record(plan,owner,stop,root,camp)
    check('native_stop_and_machine_reference',ref['schema']=='execution-window-stop-reference-v1')
    expected=dict(project_id=ctx.project_id,project_instance_id=ctx.project_instance_id,plan_id=plan['plan_id'],plan_digest=plan['plan_digest'],scope_digest=digest(scope(plan)))
    proof=qualification(ref,stop['receipt'],expected,tracked.ready,tracked.created,m)
    check('machine_readonly_gate_accepts_exact_proof',proof['classification']=='AUTOMATED_READONLY_GATE_NOT_HUMAN_SIGNATURE')
    check('actual_retained_exit_codes',all(v['exit_code']==0 and v['exit_source']=='retained_windows_handle' for v in proof['exits']))
    reject('wrong_reference_hash',lambda:qualification(dict(ref,sha256='f'*64),stop['receipt'],expected,tracked.ready,tracked.created,m))
    reject('cross_plan_reference',lambda:qualification(ref,stop['receipt'],dict(expected,plan_id='wrong'),tracked.ready,tracked.created,m))
    reject('cross_stop_receipt',lambda:qualification(ref,dict(stop['receipt'],operation_id='wrong'),expected,tracked.ready,tracked.created,m))
    report.update(reference=ref,proof=proof,stop=stop,final=m.inspect())
    check('normal_native_marker',report['final']['reason']=='ORDERLY_STOP_RECORDED')
    db=sqlite3.connect((Path(ctx.root)/'execution.sqlite3').as_uri()+'?mode=ro',uri=True)
    try:counts={t:db.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ('grants','runs','receipts','consumption')}
    finally:db.close()
    check('no_execution',not any(counts.values()))
    report.update(counts=counts,status='DEVELOPER_MACHINE_TEST_PASS')
except BaseException as e:report.update(status='BLOCKED_NO_RETRY',error=repr(e));raise
finally:
    if tracked:tracked.close()
    report.update(classification='ACTUAL_NATIVE_IPC_HANDLES_DPAPI_WITH_SYNTHETIC_PLAN_AND_RESEARCH_DESCRIPTORS',checks=checks,passed=len(checks),root=str(root),real_B_touched=False)
    (root/'RESULTS.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
