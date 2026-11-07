"""MACHINE_TEST actual native expired unused Grant -> archive -> fresh B window.
Only science A/seal/decision/install-history/snapshot transport are explicit test
boundaries. Native Plan, Grant, IPC, same-key receipt, idle-stop and retained
process-handle exits are real. NO Submit, Dispatch, Solver or original site IO.
"""
import argparse,hashlib,json,os,sqlite3,subprocess,sys,time,uuid,traceback,io,contextlib
from unittest.mock import patch
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'gd'),str(ROOT/'gd/runtime'),str(ROOT/'tests')]
import build_grant_fixture as bf
import native_grant_response_ipc as transport
sha=transport.sha;write=transport.write

def counts(manager):
    with sqlite3.connect((Path(manager.context.root)/'execution.sqlite3').as_uri()+'?mode=ro',uri=True) as db:
        return {t:db.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ('plans','grants','runs','receipts','consumption','events','management_receipts','control_events')}

def launch(path,data,pin):
    from abqjobpilot.service_lifecycle import ServiceLifecycleManager
    from window_closure import TrackedOwner
    with (path/'host.stdout.log').open('xb') as out,(path/'host.stderr.log').open('xb') as err:
        child=subprocess.Popen([sys.executable,'-I','-B','-S',str(ROOT/'tests/native_grant_response_ipc.py'),'--serve',str(path),'--package-pin',pin],stdin=subprocess.DEVNULL,stdout=out,stderr=err,cwd=path,close_fds=True,creationflags=subprocess.CREATE_NO_WINDOW,env={'SystemRoot':os.environ['SystemRoot'],'TEMP':str(path),'TMP':str(path)})
    until=time.monotonic()+20
    while not (path/'HOST_READY.json').exists() and child.poll() is None and time.monotonic()<until:time.sleep(.05)
    assert (path/'HOST_READY.json').is_file(),(child.poll(),(path/'host.stderr.log').read_text(errors='replace'))
    host=json.loads((path/'HOST_READY.json').read_bytes());manager=ServiceLifecycleManager(data['project']);client,context,health=manager.connect()
    owner=dict(owner_id=host['owner_id'],start_id=host['start_id'],state='CONNECTED',created=True)
    assert client.endpoint['owner_id']==owner['owner_id'] and health['lifecycle_start_id']==owner['start_id']
    tracked=TrackedOwner(manager,health,owner)
    return manager,client,child,owner,tracked

def authorize(path,data,owner):
    from abqjobpilot.product_standard import StandardOperator
    from abqjobpilot.execution.models import ExecutionError,digest
    from abqjobpilot.execution.product_standard import scope
    from abqjobpilot.local_credentials import user_sid
    p=data['plan'];key='authorize_'+uuid.uuid4().hex
    args=dict(plan_id=p['plan_id'],plan_digest=p['plan_digest'],expires_at=p['expires_at'],subject=user_sid(),source=digest(scope(p)))
    journal=bf.create_journal(path,data,owner,key,args,data['package'])
    write(path/'TEST_ONLY_AUTHORIZATION_SCOPE.json',dict(classification='MACHINE_TEST_NOT_HUMAN_UI_ACCEPTANCE',operation_key=key,plan=p['plan_id'],no_submit_dispatch_solver=True))
    start=time.monotonic()
    try:
        result=StandardOperator(data['project']).request('authorize',args,operation_key=key,owner_id=owner['owner_id'])
        response=dict(state='RECEIVED',result=result,elapsed=time.monotonic()-start)
    except ExecutionError as exc:
        response=dict(state='UNKNOWN',code=exc.code,elapsed=time.monotonic()-start)
        assert exc.code=='ACCEPTANCE_UNKNOWN'
    return journal,key,response

def stop(path,data,manager,child,owner,tracked,camp):
    key='machine_stop_'+uuid.uuid4().hex
    write(path/'STOP_INTENT.json',dict(key=key,owner=owner,project=data['project'],classification='MACHINE_TEST_UNUSED_GRANT_NO_RUN'))
    result=manager.stop(owner_id=owner['owner_id'],operation_key=key)
    assert result['receipt']['state']=='STOP_COMMITTED'
    child.wait(timeout=15);assert child.returncode==0
    ref=tracked.record(data['plan'],owner,result,path,camp)
    write(path/'STOP_AND_CLOSURE.json',dict(result=result,closure=ref,process_exit=tracked.exit_record(owner,result)))
    tracked.close()
    return ref

def main():
    a=argparse.ArgumentParser();a.add_argument('--package-pin',required=True);a.add_argument('--run',action='store_true');args=a.parse_args();assert args.run
    transport.installed(args.package_pin)
    import workflow,execution_windows as ew,expired_grant as eg
    root=ROOT/'evidence'/('MACHINE_TEST_GRANT_RESPONSE_'+uuid.uuid4().hex);root.mkdir()
    report=dict(classification='ACTUAL_NATIVE_EXPIRED_GRANT_CHAIN_WITH_DECLARED_SCIENTIFIC_BOUNDARIES',checks=[],solver_calls=0,submit_calls=0,dispatch_calls=0,original_site_untouched=True)
    def check(name,value=True):assert value,name;report['checks'].append(name)
    path,data=bf.prepare(root,'first',args.package_pin,window_ttl=45)
    data['mode']='delay'
    # Descriptor is test-only fixture, changed before the controlled host exists.
    (path/'FIXTURE.json').write_text(json.dumps(data,indent=2),encoding='utf8')
    work=path/'research';camp=workflow.Campaign(work,data['contract'],args.package_pin)
    try:
      with bf.science(work,args.package_pin,data['contract']):
        original_rows=[dict(r) for r in camp.db.execute('SELECT * FROM stages ORDER BY phase')]
        manager,client,child,owner,tracked=launch(path,data,args.package_pin)
        journal,key,reply=authorize(path,data,owner)
        check('actual_timeout_after_committed_native_grant',reply['state']=='UNKNOWN' and reply['elapsed']>=2)
        recovered=bf.cli(journal,args.package_pin)
        check('same_key_installed_recovery',recovered['state']=='COMMITTED_RESPONSE_RECOVERED' and recovered['receipt']['operation_key']==key and recovered['confirmed_committed'])
        write(path/'RECOVERED.json',recovered)
        expected=dict(plans=1,grants=1,runs=0,receipts=0,consumption=0,events=0,management_receipts=1,control_events=1)
        check('unused_grant_no_execution',counts(manager)==expected)
        until=time.monotonic()+50
        while time.time()<=data['plan']['expires_at'] and time.monotonic()<until:time.sleep(.2)
        check('actual_wallclock_plan_and_grant_expiry',time.time()>data['plan']['expires_at'] and time.time()>recovered['grant']['expires_at'])
        expired=bf.cli(journal,args.package_pin)
        check('expired_receipt_remains_committed_not_executable',expired['confirmed_committed'] and expired['expired'] and not expired['executable_now'])
        closure=stop(path,data,manager,child,owner,tracked,camp)
        check('native_stop_and_real_retained_exit',manager.inspect()['reason']=='ORDERLY_STOP_RECORDED')
        after=counts(manager);check('one_grant_and_exact_authorize_stop_receipts',after==dict(expected,management_receipts=2,control_events=2))
        operation=uuid.uuid4().hex
        closure_file=path/'CLOSURE_REFERENCE.json';write(closure_file,closure)
        def archive_cli(action,**options):
            argv=['expired_grant.py',action,'--workspace',str(work),'--contract-pin',data['contract'],'--package-pin',args.package_pin,'--python-exe',sys.executable,'--operation-id',operation]
            for k,v in options.items():argv+=['--'+k.replace('_','-'),str(v)]
            output=io.StringIO()
            with patch.object(sys,'argv',argv),contextlib.redirect_stdout(output):eg.main()
            return json.loads(output.getvalue())
        proposed=archive_cli('propose',journal=journal,closure=closure_file,closure_pin=sha(closure_file));p=proposed['proposal']
        proposal_file=path/'ARCHIVE_PROPOSAL.json';write(proposal_file,proposed)
        check('installed_CLI_propose_exact_canonical_pin',proposed['proposal_digest']==ew.c.pin(p))
        archived=archive_cli('archive',proposal=proposal_file,proposal_pin=proposed['proposal_digest'])
        archive=archived['reference'];write(path/'ARCHIVE_RESULT.json',archived)
        check('installed_CLI_first_archive_not_replay',not archived['replayed'])
        check('installed_CLI_read_first_archive',archive_cli('read')['reference']==archive)
        check('versioned_expired_unused_grant_archive',archive['schema']=='expired-unconsumed-grant-reference-v1' and archive['operation_id']==operation)
        check('archive_preserves_same_science_and_unique_hold',camp.counts(camp.verified_rows())==dict(limit=2,held=1,charged=1,available=0) and [dict(r) for r in camp.db.execute('SELECT * FROM stages ORDER BY phase')]==original_rows)
        newop=uuid.uuid4().hex;static=ew.static(camp,newop,archive);proposal=static['proposal']
        renewed=ew.prepare(camp,proposal,static['proposal_digest'],int(time.time())+120)
        check('new_window_same_candidate_contract_original_request',all(renewed[k]==data['binding'][k] for k in ('candidate','project','contract','original_request','budget')))
        check('new_plan_independent_identity_output',renewed['new']['plan']['plan_id']!=data['plan']['plan_id'] and renewed['new']['af_project']!=data['project'])
        second=root/'second';second.mkdir()
        data2=dict(data,mode='normal',workspace=str(work),project=renewed['new']['af_project'],plan=renewed['new']['plan'],binding=renewed,operation_id=newop)
        write(second/'FIXTURE.json',data2)
        manager2,client2,child2,owner2,tracked2=launch(second,data2,args.package_pin)
        # Native new grant is machine test capability use, not automatic retry.
        from abqjobpilot.product_standard import StandardOperator
        from abqjobpilot.execution.product_standard import scope
        from abqjobpilot.execution.models import digest
        from abqjobpilot.local_credentials import user_sid
        p2=data2['plan'];key2='authorize_'+uuid.uuid4().hex
        args2=dict(plan_id=p2['plan_id'],plan_digest=p2['plan_digest'],expires_at=p2['expires_at'],subject=user_sid(),source=digest(scope(p2)))
        write(second/'AUTHORIZE_REQUEST.json',dict(operation_key=key2,arguments=args2,owner=owner2,classification='MACHINE_TEST_SECOND_NATIVE_GRANT_NO_SUBMIT'))
        result2=StandardOperator(data2['project']).request('authorize',args2,operation_key=key2,owner_id=owner2['owner_id'])
        receipt2=client2.management_receipt('product_standard_authorize',key2)
        check('new_grant_exact_new_plan_once',result2['receipt']==receipt2 and receipt2['plan_id']==p2['plan_id'] and receipt2['grant_id']!=recovered['grant']['grant_id'])
        check('second_native_grant_zero_run_consumption',counts(manager2)==expected)
        check('old_native_history_preserved',counts(manager)==after)
        stop(second,data2,manager2,child2,owner2,tracked2,camp)
        check('second_test_owner_native_stop_exit',manager2.inspect()['reason']=='ORDERLY_STOP_RECORDED')
        check('final_same_scientific_budget',camp.counts(camp.verified_rows())==dict(limit=2,held=1,charged=1,available=0))
        report.update(status='DEVELOPER_NATIVE_CHAIN_PASS',passed=len(report['checks']),first_plan=data['plan']['plan_id'],second_plan=p2['plan_id'],archive=archive,authorize_transmissions=2)
    except BaseException as exc:
        report.update(status='BLOCKED_NO_RETRY',error=repr(exc),traceback=traceback.format_exc());raise
    finally:
        camp.db.close();write(root/'RESULTS.json',report)
    print(json.dumps(dict(status=report['status'],passed=report['passed'],evidence=str(root/'RESULTS.json'))))

if __name__=='__main__':main()
