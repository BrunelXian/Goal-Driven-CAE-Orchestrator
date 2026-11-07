"""MACHINE_TEST B science fixture; native Plan/IPC/Grant/receipt remain real.
Synthetic A extraction/seal/decision and in-process snapshot transport are
explicit boundary substitutes. No original B files or Solver are accessed.
"""
import contextlib,hashlib,json,sys,time,uuid,subprocess,io
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def write(p,v):
    with Path(p).open('x',encoding='utf8') as f:json.dump(v,f,indent=2)

@contextlib.contextmanager
def science(work,pin,contract):
    import workflow,native_feedback,b_admission as b,execution_windows as r
    work=Path(work).resolve();real_run=subprocess.run
    def decision(camp):
        raw=camp.db.execute("SELECT result FROM stages WHERE phase='A'").fetchone()[0]
        ref=work/'MACHINE_TEST_DECISION.json'
        return dict(source_A_result_sha256=hashlib.sha256(raw).hexdigest(),decision_reference=dict(path=str(ref),sha256=sha(ref))),json.loads(ref.read_bytes())
    def transport(args,*aa,**kw):
        if isinstance(args,list) and len(args)>6 and str(args[4]).endswith('admission_snapshot.py'):
            assert Path(args[5]).resolve()==work,'TEST_FIXTURE_WORKSPACE_ONLY'
            cc=workflow.Campaign(work,contract,pin)
            try:
                fn=r.snapshot if args[6].startswith('b-window:') else b.snapshot
                return SimpleNamespace(returncode=0,stdout=json.dumps(fn(cc,args[7] if len(args)>7 else '--preparation')).encode(),stderr=b'')
            except Exception as ex:return SimpleNamespace(returncode=2,stdout=b'',stderr=repr(ex).encode())
            finally:cc.db.close()
        return real_run(args,*aa,**kw)
    with patch.object(native_feedback,'verify',lambda c,row:json.loads(row['result'])),patch.object(b,'decision',decision),patch.object(subprocess,'run',transport),patch.object(r,'compatibility',lambda:{'package':pin}),patch.object(r.legacy,'compatibility',lambda:{'package':pin}):
        yield

def prepare(root,mode,pin):
    import workflow,tensile,native_feedback,b_admission as b,execution_windows as r
    path=root/mode;path.mkdir();work=path/'research'
    model=Path(r'D:\Projects\GDCAETEST\TENSILE-V1-R3-ADMISSION-20261105-dev-93a1ef42\model')
    target=Path(r'D:\Projects\GDCAETEST\TENSILE-V1-PUBLIC-TARGET-20261104-69d2a041ef\target_force_displacement.csv')
    initial=workflow.initialize(work,model,target,sha(target),'PREPARE_ONLY',pin,'JIT_HUMAN_REVIEW')
    camp=workflow.Campaign(work,initial['contract_sha256'],pin)
    try:
        a=camp.prepare('A');frames=tensile.fixture_curve(a['request']['parameters'])
        feedback=dict(classification='NATIVE_ODB',binding={'run_id':'MACHINE_TEST_SYNTHETIC_A_NO_SOLVER'},frames=frames,assessment=tensile.compare(camp.target,frames,a['request']['parameters']))
        write(work/'MACHINE_TEST_DECISION.json',dict(classification='SYNTHETIC_A_SCIENCE_BOUNDARY_NOT_REAL_ODB',parameters_from='Actual tensile.compare and Campaign.prepare B',solver_executed=False))
        with science(work,pin,initial['contract_sha256']),patch.object(native_feedback,'source',lambda *a:None),patch.object(native_feedback,'extract',lambda *a:feedback):
            camp.observe('A',a['request_sha256'],'NATIVE');prepared=camp.prepare('B')
            assert camp.counts(camp.verified_rows())==dict(limit=2,held=1,charged=1,available=0)
            operation=uuid.uuid4().hex;p=b.proposal(camp,operation)
            first=b.prepare(camp,p,b.c.pin(p),int(time.time())+3)
            # Actual old test Plan expires; no clock patch, no old Owner or Grant.
            time.sleep(max(0,first['new']['plan']['expires_at']-time.time()+.1))
            operation=uuid.uuid4().hex;p=r.proposal(camp,operation,{})
            result=r.prepare(camp,p,r.c.pin(p),int(time.time())+600)
            assert result['new']['plan']['registration']['phase']=='B'
        data=dict(classification='MACHINE_TEST_NO_SOLVER',phase='B',mode=mode,project=result['new']['af_project'],plan=result['new']['plan'],binding=result,
            contract=initial['contract_sha256'],package=pin,operation_id=operation,workflow_sha256=sha(work/'workflow.sqlite'),
            scientific_boundary='SYNTHETIC_A_EXTRACT_SEAL_DECISION_AND_SNAPSHOT_TRANSPORT_ONLY_NATIVE_B_PLAN_REAL')
        write(path/'FIXTURE.json',data);return path,data
    finally:camp.db.close()

def create_journal(path,data,owner,key,args,pin):
    from approval_dialog import packet_digest
    from abqjobpilot.execution.models import digest
    from abqjobpilot.execution.product_standard import scope
    from af_installation import ROOT as AF_ROOT
    plan=data['plan'];binding=data['binding'];journal=path/'research'/'grant-response-journal';journal.mkdir()
    actual_owner=dict(owner,state='CONNECTED',created=True)
    packet=dict(operation_id=data['operation_id'],owner=actual_owner,plan=plan,af_project=data['project'],candidate=binding['candidate'],project=binding['project'],budget=binding['budget'],
        scope_digest=digest(scope(plan)),input_manifest=plan['input_manifest'],parameters=plan['registration']['parameters'],resources=plan['resources'],expires_at=plan['expires_at'],
        installation=dict(gd_installed=str(ROOT/'gd'),gd_package_sha256=pin,af_installed=AF_ROOT,af_identity=sha(ROOT/'gd/af_installation.py')))
    packet.update({k:plan[k] for k in ('plan_id','plan_digest','job_id','job_revision','job_name','engineering','scratch','output_key')})
    checked=dict(binding,scope_digest=packet['scope_digest'])
    values={'confirmation-packet':packet,'human-confirmation':dict(status='USER_DECISION_CAPTURED',input_method='local_win32_mouse',packet_sha256=packet_digest(packet),operation_id=data['operation_id'],test_only='MODELED_DECISION_NOT_HUMAN_UI_ACCEPTANCE'),
        'authorize-request':dict(operation_key=key,arguments=args),'owner-start-result':actual_owner,'pre-authorize-binding':binding,'dynamic-gate':checked,
        'authorize-local-state':dict(state='REQUEST_PERSISTED_NOT_SENT',operation_key=key),'authorize-send-intent':dict(state='SENT_ACCEPTANCE_UNKNOWN',operation_key=key)}
    for name,value in values.items():write(journal/(name+'.json'),value)
    return journal

def cli(journal,pin):
    import grant_response
    output=io.StringIO()
    with patch.object(sys,'argv',['grant_response.py','--journal',str(journal),'--package-pin',pin,'--python-exe',sys.executable]),contextlib.redirect_stdout(output):grant_response.main()
    return json.loads(output.getvalue())
