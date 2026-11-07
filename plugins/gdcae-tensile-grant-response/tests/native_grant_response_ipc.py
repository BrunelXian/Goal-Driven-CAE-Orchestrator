"""MACHINE_TEST: actual StandardOperator, native IPC and Grant transactions.

Only an isolated new tensile A admission is used by the default fixture: this
proves shared Standard authorization transport semantics, NOT original B
scientific admission. No Submit, Dispatch, Solver or live workspace is used.
The controlled host subclasses the supported before_response test checkpoint;
the ProductStandardControl business handler is unchanged.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'gd'),str(ROOT/'gd/runtime'),str(ROOT/'tests')]


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path,value):
    with Path(path).open('x',encoding='utf8') as f:
        json.dump(value,f,indent=2,allow_nan=False);f.flush();os.fsync(f.fileno())


def installed(pin):
    from types import SimpleNamespace
    from main import verify
    verify(ROOT/'gd',SimpleNamespace(package_pin=pin,python_exe=sys.executable))
    from r3_bridge import trusted_af
    trusted_af()


def fixture_path(path):
    path=Path(path).resolve()
    assert path.parent==ROOT/'evidence' and path.name.startswith('MACHINE_TEST_GRANT_RESPONSE_'),path
    return path


def serve(case_root,pin):
    """Trusted test host seam, not a new launcher supplied to the product."""
    installed(pin);case_root=Path(case_root).resolve();fixture_path(case_root.parent)
    data=json.loads((case_root/'FIXTURE.json').read_bytes())
    assert data['classification']=='MACHINE_TEST_NO_SOLVER'
    assert Path(data['project']).parent==case_root/'research'
    science_context=None
    if data.get('phase')=='B':
        import build_grant_fixture as bf
        science_context=bf.science(case_root/'research',pin,data['contract']);science_context.__enter__()
    else:assert data['project']==str(case_root/'research'/'af-A')
    from abqjobpilot.service_lifecycle import ServiceLifecycleManager,write_new
    from abqjobpilot.service_host import observe_host
    from abqjobpilot.execution.models import digest,now,canonical_json
    from abqjobpilot.execution.lifecycle import LifecycleControl
    from abqjobpilot.execution.standard_contract import StandardConfig
    from abqjobpilot.execution.supervisor import FakeSupervisor
    from abqjobpilot.local_credentials import private_value
    manager=ServiceLifecycleManager(data['project']);profile=manager._profile()
    assert manager._current() is None
    start='start_'+uuid.uuid4().hex;attempt=manager._path(start);attempt.mkdir()
    host=observe_host(disk_output=True)
    intent=dict(start_id=start,context_digest=manager.context.context_digest,profile_digest=digest(profile),
                recorded_at=now(),requester_host=host)
    write_new(attempt/'intent.json',intent);write_new(manager._path('lifecycle-current.json'),intent)
    write_new(attempt/'created.json',dict(start_id=start,transport_pid=os.getpid(),recorded_at=now()))
    extension=profile['standard_extension']
    lifecycle=LifecycleControl(profile['operator_digest'],start,product_host=True,standard_binding=extension['binding'])
    class CheckpointHost(FakeSupervisor):
        def _checkpoint(self,name):
            if name=='product_control:before_response':
                write(case_root/'CHECKPOINT_COMMITTED.json',dict(name=name,mode=data['mode'],at=time.time(),pid=os.getpid()))
                if data['mode']=='delay':time.sleep(3.2)
                elif data['mode']=='drop':raise EOFError('MACHINE_TEST response intentionally lost after native commit')
                else:raise AssertionError(data['mode'])
    bootstrap={k:profile[k] for k in ('authority_instance','credential','client_namespace')}
    bootstrap['endpoint_file']=str(attempt/'endpoint.json')
    supervisor=CheckpointHost(manager.context,bootstrap,standard_config=StandardConfig(canonical_json(extension['standard_config'])),lifecycle=lifecycle)
    try:
        write_new(attempt/'host.json',host)
        write_new(manager._path('connection.json'),private_value(manager.context,dict(endpoint=supervisor.endpoint,credential=profile['credential'])))
        write_new(attempt/'ready.json',dict(owner_id=supervisor.endpoint['owner_id'],start_id=start,recorded_at=now(),process=host['process']))
        write(case_root/'HOST_READY.json',dict(owner_id=supervisor.endpoint['owner_id'],start_id=start,pid=os.getpid(),
             classification='MACHINE_TEST_NATIVE_HOST_SUPPORTED_RESPONSE_CHECKPOINT'))
        supervisor.serve()
    finally:
        if not supervisor.store._session.closed:supervisor.store.close()
    if lifecycle.stop_requested.is_set() and lifecycle.receipt:
        write_new(attempt/'stopped.json',dict(start_id=start,context_digest=manager.context.context_digest,receipt=lifecycle.receipt,recorded_at=now()))


def prepare_case(root,mode,pin):
    """An independently new true model admission; no synthetic A feedback."""
    import workflow
    from r3_bridge import admit
    path=root/mode;path.mkdir();work=path/'research'
    model=Path(r'D:\Projects\GDCAETEST\TENSILE-V1-R3-ADMISSION-20261105-dev-93a1ef42\model')
    target=Path(r'D:\Projects\GDCAETEST\TENSILE-V1-PUBLIC-TARGET-20261104-69d2a041ef\target_force_displacement.csv')
    initial=workflow.initialize(work,model,target,sha(target),'PREPARE_ONLY',pin,'JIT_HUMAN_REVIEW')
    camp=workflow.Campaign(work,initial['contract_sha256'],pin)
    try:
        candidate=camp.prepare('A');row=camp.db.execute("SELECT * FROM stages WHERE phase='A'").fetchone()
        result=admit(camp,row,int(time.time())+590)
        assert result['plan']['registration']['purpose']=='JIT_HUMAN_REVIEW'
        baseline=camp.inspect()
    finally:camp.db.close()
    value=dict(classification='MACHINE_TEST_NO_SOLVER',model_scope='NEW_ISOLATED_A_NOT_ORIGINAL_B',mode=mode,
        project=result['af_project'],plan=result['plan'],candidate=candidate,contract_pin=initial['contract_sha256'],
        scientific_before=baseline,workflow_sha256=sha(work/'workflow.sqlite'),package_pin=pin)
    write(path/'FIXTURE.json',value)
    return path,value


def run_case(root,mode,pin,b_phase=False):
    science_context=None;journal=None
    if b_phase:
        import build_grant_fixture as bf
        path,data=bf.prepare(root,mode,pin)
        science_context=bf.science(path/'research',pin,data['contract']);science_context.__enter__()
    else:path,data=prepare_case(root,mode,pin)
    from abqjobpilot.service_lifecycle import ServiceLifecycleManager
    from abqjobpilot.product_standard import StandardOperator
    from abqjobpilot.execution.models import ExecutionError,digest
    from abqjobpilot.execution.product_standard import scope
    from abqjobpilot.execution.process_handles import ProcessReference
    from abqjobpilot.local_credentials import user_sid
    manager=ServiceLifecycleManager(data['project']);report={'mode':mode,'checks':[]};ref=None;child=None
    def check(label,value=True):assert value,label;report['checks'].append(label)
    with (path/'host.stdout.log').open('xb') as stdout,(path/'host.stderr.log').open('xb') as stderr:
        child=subprocess.Popen([sys.executable,'-I','-B','-S',str(Path(__file__).resolve()),'--serve',str(path),'--package-pin',pin],
            stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,cwd=path,close_fds=True,
            creationflags=subprocess.CREATE_NO_WINDOW,env={'SystemRoot':os.environ['SystemRoot'],'TEMP':str(path),'TMP':str(path)})
    try:
        until=time.monotonic()+15
        while not (path/'HOST_READY.json').exists() and child.poll() is None and time.monotonic()<until:time.sleep(.05)
        assert (path/'HOST_READY.json').is_file(),(child.poll(),(path/'host.stderr.log').read_text(errors='replace'))
        host=json.loads((path/'HOST_READY.json').read_bytes());client,ctx,health=manager.connect()
        check('native_authenticated_owner',client.endpoint['owner_id']==host['owner_id'] and health['lifecycle_start_id']==host['start_id'])
        ref=ProcessReference(health['process']['pid'],health['process'])
        plan=data['plan'];key='authorize_'+uuid.uuid4().hex
        args=dict(plan_id=plan['plan_id'],plan_digest=plan['plan_digest'],expires_at=plan['expires_at'],subject=user_sid(),source=digest(scope(plan)))
        write(path/'AUTHORIZE_REQUEST.json',dict(operation_key=key,arguments=args,owner_id=host['owner_id'],
              classification='MACHINE_TEST_NATIVE_CAPABILITY_NOT_HUMAN_OR_SITE_AUTHORIZATION'))
        if b_phase:journal=bf.create_journal(path,data,dict(owner_id=host['owner_id'],start_id=host['start_id']),key,args,pin)
        begin=time.monotonic()
        try:StandardOperator(data['project']).request('authorize',args,operation_key=key,owner_id=host['owner_id'])
        except ExecutionError as exc:
            report['transport']={'code':exc.code,'stage':exc.stage,'elapsed_seconds':time.monotonic()-begin}
            check('original_native_authorize_returns_unknown',exc.code=='ACCEPTANCE_UNKNOWN')
        else:raise AssertionError('Expected delayed/lost response; no retransmission permitted')
        check('committed_checkpoint_reached',(path/'CHECKPOINT_COMMITTED.json').is_file())
        if mode=='delay':check('actual_delay_exceeds_two_second_client_timeout',report['transport']['elapsed_seconds']>=2)
        # Exactly one authorize transmission. All subsequent IPC is read-only
        # except the explicit normal idle stop of this isolated test host.
        receipt=client.management_receipt('product_standard_authorize',key)
        check('same_key_native_receipt',receipt['operation_key']==key and receipt['plan_id']==plan['plan_id'] and receipt['plan_digest']==plan['plan_digest'])
        check('receipt_exact_owner_subject_scope',receipt['owner_id']==host['owner_id'] and receipt['subject']==args['subject'] and receipt['scope_digest']==args['source'])
        report['recovered_receipt']=receipt
        for label,action,badkey in [('wrong_key','product_standard_authorize','authorize_'+uuid.uuid4().hex),('wrong_namespace','authorize',key)]:
            try:client.management_receipt(action,badkey)
            except ExecutionError as exc:check(label+'_rejected',exc.code=='NOT_FOUND')
            else:raise AssertionError(label)
        db=sqlite3.connect((Path(ctx.root)/'execution.sqlite3').as_uri()+'?mode=ro',uri=True)
        try:
            before=db.execute('SELECT COUNT(*) FROM management_receipts').fetchone()[0]
            check('repeated_readback_identical',client.management_receipt('product_standard_authorize',key)==receipt)
            report['counts_before_stop']={table:db.execute('SELECT COUNT(*) FROM '+table).fetchone()[0] for table in ('plans','grants','runs','receipts','consumption','events','management_receipts','control_events')}
            c=report['counts_before_stop'];check('one_native_grant_and_receipt_only',c==dict(plans=1,grants=1,runs=0,receipts=0,consumption=0,events=0,management_receipts=1,control_events=1))
            grant=json.loads(db.execute('SELECT body FROM grants').fetchone()[0]);report['grant']=grant
            check('actual_grant_matches_management_receipt',grant['grant_id']==receipt['grant_id'] and grant['approval_operation']==receipt['operation_id'])
            check('readback_did_not_write',db.execute('SELECT COUNT(*) FROM management_receipts').fetchone()[0]==before)
        finally:db.close()
        check('scientific_ledger_unchanged',sha(path/'research/workflow.sqlite')==data['workflow_sha256'])
        if b_phase:
            before_files={str(p):sha(p) for p in journal.iterdir()}
            before_db=sha(Path(ctx.root)/'execution.sqlite3')
            recovered=bf.cli(journal,pin);report['installed_cli_recovery']=recovered
            check('installed_B_CLI_recovered',recovered['state']=='COMMITTED_RESPONSE_RECOVERED' and recovered['confirmed_committed'] and recovered['executable_now'])
            check('installed_B_CLI_exact_same_native_receipt',recovered['receipt']==receipt and recovered['operation_key']==key)
            check('installed_B_CLI_no_resume_or_submit_authority',recovered['automatic_resume'] is False and recovered['submit_authorized_by_recovery'] is False)
            check('installed_B_CLI_no_native_or_journal_write',before_db==sha(Path(ctx.root)/'execution.sqlite3') and before_files=={str(p):sha(p) for p in journal.iterdir()})
            check('installed_B_CLI_repeat_same_result',bf.cli(journal,pin)==recovered)
        stopkey='machine_stop_'+uuid.uuid4().hex;write(path/'STOP_INTENT.json',dict(owner=host['owner_id'],start=host['start_id'],key=stopkey,reason='TEST_ONLY_GRANT_UNUSED_NO_RUN'))
        stop=manager.stop(owner_id=host['owner_id'],operation_key=stopkey);report['stop']=stop
        check('normal_native_idle_stop',stop['receipt']['state']=='STOP_COMMITTED')
        child.wait(timeout=15);check('test_host_exit_zero',child.returncode==0)
        report['retained_exit']=ref.exit_evidence();check('retained_native_worker_exit',report['retained_exit'] and report['retained_exit']['exit_code']==0)
        check('native_orderly_marker',manager.inspect()['reason']=='ORDERLY_STOP_RECORDED')
        report.update(status='DEVELOPER_NATIVE_IPC_PASS',passed=len(report['checks']),root=str(path),
            classification='ACTUAL_STANDARD_OPERATOR_AND_NATIVE_GRANT_TRANSACTION_WITH_RESPONSE_CHECKPOINT',
            scientific_admission_scope='ACTUAL_B_NATIVE_PLAN_SYNTHETIC_A_SCIENCE' if b_phase else 'ISOLATED_NEW_A_NOT_ORIGINAL_B',original_B_cli_recovery='INSTALLED_MAIN_WITH_DECLARED_SCIENTIFIC_BOUNDARIES' if b_phase else 'NOT_TESTED_BY_THIS_CASE',
            authorize_transmissions=1,solver_calls=0,submit_calls=0,dispatch_calls=0)
    except BaseException as exc:
        report.update(status='BLOCKED_NO_AUTOMATIC_RETRY',error=repr(exc),test_host_pid=child.pid if child else None)
        raise
    finally:
        if ref:ref.close()
        write(path/'RESULTS.json',report)
        if science_context:science_context.__exit__(None,None,None)
    return report


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',action='store_true');p.add_argument('--serve');p.add_argument('--b-run',action='store_true');p.add_argument('--package-pin',required=True)
    args=p.parse_args()
    if args.serve:return serve(args.serve,args.package_pin)
    assert args.run,'Explicit --run after new install is approved is required'
    installed(args.package_pin)
    root=ROOT/'evidence'/('MACHINE_TEST_GRANT_RESPONSE_'+uuid.uuid4().hex);root.mkdir()
    reports=[run_case(root,mode,args.package_pin,args.b_run) for mode in ('delay','drop')]
    value=dict(status='DEVELOPER_NATIVE_IPC_PASS',cases=reports,passed=sum(r['passed'] for r in reports),
               actual_original_B_untouched=True,no_solver_or_submit_or_dispatch=True)
    write(root/'RESULTS.json',value);print(json.dumps(dict(status=value['status'],passed=value['passed'],evidence=str(root/'RESULTS.json')),indent=2))


if __name__=='__main__':main()
