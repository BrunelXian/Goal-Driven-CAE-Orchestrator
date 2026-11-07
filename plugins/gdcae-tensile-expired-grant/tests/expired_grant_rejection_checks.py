"""Bounded TEST_ONLY rejections against the stopped native chain; no new Owner/Grant."""
import argparse,contextlib,copy,hashlib,io,json,sqlite3,sys,uuid
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'gd'),str(ROOT/'gd/runtime'),str(ROOT/'tests')]
import native_grant_response_ipc as ipc,build_grant_fixture as bf

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--fixture',required=True);ap.add_argument('--package-pin',required=True);a=ap.parse_args();root=ipc.fixture_path(a.fixture);ipc.installed(a.package_pin)
    import workflow,expired_grant as eg,execution_windows as ew,b_parameters
    first=root/'first';work=first/'research';data=json.loads((first/'FIXTURE.json').read_bytes());journal=work/'grant-response-journal';ref=json.loads((first/'ARCHIVE_RESULT.json').read_bytes())['reference']
    camp=workflow.Campaign(work,data['contract'],a.package_pin);checks=[]
    output_root=root/('rejections-'+uuid.uuid4().hex);output_root.mkdir()
    def check(label,yes=True):assert yes,label;checks.append(label)
    def reject(label,call):
        try:call()
        except Exception as exc:checks.append(label+':'+type(exc).__name__)
        else:raise AssertionError('Unexpected acceptance: '+label)
    def cli(action,**options):
        opts=['expired_grant.py',action,'--workspace',str(work),'--contract-pin',data['contract'],'--package-pin',a.package_pin,'--python-exe',sys.executable,'--operation-id',ref['operation_id']]
        for k,v in options.items():opts+=['--'+k.replace('_','-'),str(v)]
        output=io.StringIO()
        with patch.object(sys,'argv',opts),contextlib.redirect_stdout(output):eg.main()
        return json.loads(output.getvalue())
    def accepted(c,feedback,raw,pin):
        assert feedback['binding']['run_id']=='MACHINE_TEST_SYNTHETIC_A_NO_SOLVER'
        return raw
    try:
      with bf.science(work,a.package_pin,data['contract']),patch.object(b_parameters,'accepted',accepted):
        rec,p=eg.row(camp.db,ref['operation_id']);before=ipc.sha(work/'workflow.sqlite')
        proposal=output_root/'MACHINE_TEST_ORIGINAL_ARCHIVE_PROPOSAL.json';ipc.write(proposal,p)
        replay=eg.archive(camp,p,ew.c.pin(p));check('archive_same_operation_replay_no_write',replay['replayed'] and replay['reference']==ref and ipc.sha(work/'workflow.sqlite')==before)
        cli_read=cli('read');check('installed_CLI_read_exact_record',cli_read['record']==p and cli_read['reference']==ref)
        cli_replay=cli('archive',proposal=proposal,proposal_pin=ew.c.pin(p));check('installed_CLI_archive_exact_replay',cli_replay['replayed'] and cli_replay['reference']==ref)
        closurefile=output_root/'MACHINE_TEST_CLOSURE_REFERENCE.json';ipc.write(closurefile,p['proof']['closure'])
        reject('installed_CLI_propose_archived_operation_refused',lambda:cli('propose',journal=journal,closure=closurefile,closure_pin=ipc.sha(closurefile)))
        modified=copy.deepcopy(p);modified['operation_id']=uuid.uuid4().hex
        reject('different_operation_cannot_archive_same_old_parent',lambda:eg.archive(camp,modified,ew.c.pin(modified)))
        missing=dict(p['proof']['closure'],path=str(root/'MISSING_CLOSURE.json'))
        reject('missing_retained_closure_rejected',lambda:eg.native_proof(journal,missing,p['parent']['identity']))
        with sqlite3.connect((work/'workflow.sqlite').as_uri()+'?mode=ro',uri=True) as ro:
            check('one_archive_record_persisted',ro.execute('SELECT COUNT(*) FROM '+eg.TABLE).fetchone()[0]==1)
        check('all_readonly_and_replay_preserve_workflow_bytes',ipc.sha(work/'workflow.sqlite')==before)
        from abqjobpilot.service_lifecycle import ServiceLifecycleManager
        manager=ServiceLifecycleManager(data['project']);db=sqlite3.connect(Path(manager.context.root)/'execution.sqlite3')
        request=db.execute("SELECT namespace,key,request_digest FROM management_receipts WHERE key LIKE 'authorize_%'").fetchone()
        original_grant=db.execute('SELECT grant_id,body FROM grants').fetchone()
        def mutated(sql,args,undo,undoargs,label):
            try:
                db.execute(sql,args);db.commit();reject(label,lambda:eg.native_proof(journal,p['proof']['closure'],p['parent']['identity']))
            finally:db.execute(undo,undoargs);db.commit()
        mutated('UPDATE management_receipts SET request_digest=? WHERE namespace=? AND key=?',('forged',request[0],request[1]),'UPDATE management_receipts SET request_digest=? WHERE namespace=? AND key=?',(request[2],request[0],request[1]),'native_authorize_request_digest_changed_rejected')
        badgrant=json.loads(original_grant[1]);badgrant['max_runs']=2
        mutated('UPDATE grants SET body=? WHERE grant_id=?',(json.dumps(badgrant),original_grant[0]),'UPDATE grants SET body=? WHERE grant_id=?',(original_grant[1],original_grant[0]),'native_grant_scope_changed_rejected')
        mutated('INSERT INTO consumption VALUES(?,?)',(original_grant[0],'r_MACHINE_TEST_UNKNOWN'),'DELETE FROM consumption WHERE run_id=?',('r_MACHINE_TEST_UNKNOWN',),'consumption_rejects_expired_unused_claim')
        plan=data['plan']
        mutated('INSERT INTO runs VALUES(?,?,?,?,?,?,?,?)',('r_MACHINE_TEST_UNKNOWN',plan['job_id'],plan['job_revision'],plan['plan_id'],original_grant[0],1,None,'{}'),'DELETE FROM runs WHERE run_id=?',('r_MACHINE_TEST_UNKNOWN',),'native_run_rejects_expired_unused_claim')
        db.close()
        proof,_,_=eg.native_proof(journal,p['proof']['closure'],p['parent']['identity']);check('restored_fixture_exact_native_proof',proof==p['proof'])
        check('same_science_budget_unchanged',camp.counts(camp.verified_rows())==dict(limit=2,held=1,charged=1,available=0))
        before=ipc.sha(work/'workflow.sqlite');cc=workflow.Campaign(work,data['contract'],a.package_pin,readonly=True,candidate_b_admission=True)
        try:check('reopened_schema_readonly_budget',cc.counts(cc.verified_rows())==dict(limit=2,held=1,charged=1,available=0))
        finally:cc.db.close()
        check('readonly_reopen_did_not_mutate_database',ipc.sha(work/'workflow.sqlite')==before)
    finally:camp.db.close()
    out=dict(status='DEVELOPER_BOUNDED_REJECTIONS_PASS',passed=len(checks),checks=checks,classification='NATIVE_STOPPED_FIXTURE_DECLARED_SYNTHETIC_A_SCIENCE',new_owner_grant_submit_dispatch_solver=0)
    path=output_root/'REJECTION_RESULTS.json';ipc.write(path,out);print(json.dumps(dict(passed=len(checks),evidence=str(path))))

if __name__=='__main__':main()
