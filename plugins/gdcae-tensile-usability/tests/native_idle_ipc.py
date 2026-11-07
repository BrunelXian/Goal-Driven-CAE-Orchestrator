"""One real isolated Windows native Owner, no Plan/Grant/Run/Solver/UI."""
import sys,json,time,uuid,sqlite3
from pathlib import Path
z=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(z/'gd'),str(z/'gd/runtime')]
from r3_bridge import trusted_af
trusted_af()
from abqjobpilot.product_project import create_project
from abqjobpilot.service_lifecycle import ServiceLifecycleManager
from abqjobpilot.execution.process_handles import ProcessReference
root=z/'evidence'/('MACHINE_TEST_IPC_'+uuid.uuid4().hex);root.mkdir()
project=root/'OFFLINE_TEST_ONLY';create_project(project,'MACHINE_TEST_NO_SOLVER')
m=ServiceLifecycleManager(project);refs=[];report={'classification':'MACHINE_TEST_NATIVE_IPC_NO_SOLVER','project':str(project),'real_B_touched':False}
try:
    start=m.start();report['start']=start
    assert start['state']=='CONNECTED',start
    client,ctx,health=m.connect();report['health']={k:health[k] for k in ('process','lifecycle_start_id','operations')}
    refs.append(ProcessReference(health['process']['pid'],health['process']))
    created=json.loads(m._path(start['start_id']+'/created.json').read_bytes())
    if created['transport_pid']!=health['process']['pid']:refs.append(ProcessReference(created['transport_pid']))
    assert client.dispatch_gate()['state']=='PAUSED'
    key='machine_stop_'+uuid.uuid4().hex
    (root/'stop_intent.json').write_text(json.dumps({'owner':start['owner_id'],'start':start['start_id'],'key':key,'action':'native_idle_stop'}))
    stop=m.stop(owner_id=start['owner_id'],operation_key=key);report['stop']=stop
    assert stop['receipt']['state']=='STOP_COMMITTED'
    deadline=time.monotonic()+15
    while time.monotonic()<deadline and any(ref.exit_evidence() is None for ref in refs):time.sleep(.05)
    report['exits']=[ref.exit_evidence() for ref in refs]
    assert all(e and e['exit_code']==0 for e in report['exits'])
    report['final']=m.inspect();assert report['final']['reason']=='ORDERLY_STOP_RECORDED'
    db=sqlite3.connect((Path(ctx.root)/'execution.sqlite3').as_uri()+'?mode=ro',uri=True)
    try:report['counts']={t:db.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ('plans','grants','runs','receipts','consumption')}
    finally:db.close()
    assert all(v==0 for v in report['counts'].values())
    report['verdict']='DEVELOPER_MACHINE_TEST_PASS'
except BaseException as e:
    report['verdict']='BLOCKED_NO_AUTOMATIC_RETRY';report['error']=repr(e);raise
finally:
    for ref in refs:ref.close()
    (root/'RESULTS.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
