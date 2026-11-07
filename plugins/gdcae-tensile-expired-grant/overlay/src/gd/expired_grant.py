"""Versioned qualification of one expired, unconsumed B Grant.

This does not revoke, modify, renew or replace a native Grant. The append-only
record is in the existing workflow database; native facts remain authoritative.
No budget operation, Owner call, execution or new Plan is performed here.
"""
import argparse,json,re,sqlite3,sys,time
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parent),str(Path(__file__).resolve().parent/"runtime")]
import continuation as c
import grant_response as response

TABLE='tensile_expired_unconsumed_grants'
SCHEMA='expired-unconsumed-grant-qualification-v1'
REFERENCE='expired-unconsumed-grant-reference-v1'

def row(db,op):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(TABLE,)).fetchone():return None
    values=db.execute('SELECT * FROM '+TABLE+' WHERE operation_id=?',(op,)).fetchall()
    c.require(len(values)<=1,'EXPIRED_GRANT_RECORD_CONFLICT')
    if not values:return None
    value=dict(values[0]);body=json.loads(value['body'])
    c.require(set(value)=={'operation_id','schema','grant_id','parent_operation_id','body','body_digest','state'}
              and value['state']=='COMMITTED' and value['schema']==body['schema']==SCHEMA
              and value['operation_id']==body['operation_id'] and value['body_digest']==c.case.hashbytes(value['body'])
              and value['grant_id']==body['proof']['native']['grant']['grant_id']
              and value['parent_operation_id']==body['parent']['operation_id'],'EXPIRED_GRANT_RECORD_CHANGED')
    return value,body

def native_proof(journal,closure,expected):
    """The old zero-Grant path is untouched; this branch demands exactly one."""
    from r3_bridge import trusted_af
    trusted_af()
    from abqjobpilot.service_lifecycle import ServiceLifecycleManager
    from window_closure import qualification,SCHEMA as CLOSURE
    from abqjobpilot.execution.models import digest
    from abqjobpilot.execution.product_standard import scope
    journal=c.local(journal)
    c.require(journal.is_dir(),'ORIGINAL_AUTHORIZATION_JOURNAL_REQUIRED')
    c.require(not any((journal/(name+'.json')).exists() for name in
                      ('submit-request','submit-result','dispatch-request','dispatch-result','native-acceptance-fact-request','native-observation-request')),
              'POSSIBLE_SUBMIT_OR_EXECUTION_RECONCILE_ONLY')
    ctx=response.packet_context(journal);m=ServiceLifecycleManager(c.local(ctx['packet']['af_project']))
    c.require(c.identity(ctx['binding']['new'])==expected,'EXPIRED_GRANT_PARENT_IDENTITY_CHANGED')
    native=response.durable(ctx,m,closed=True)
    c.require(native['receipt'] is not None and native['grant']['expires_at']<=time.time()
              and ctx['plan']['expires_at']<=time.time(),'GRANT_AND_PLAN_MUST_BE_EXPIRED')
    c.require(closure.get('schema')==CLOSURE,'VERIFIED_RETAINED_CLOSURE_REQUIRED')
    created=response.read(m._path(ctx['owner']['start_id']+'/created.json'))
    exit_proof=qualification(closure,native['normal_stop']['receipt'],expected,native['ready'],created,m)
    # Native history must have one supported original startup and no subsequent
    # unknown startup/solver intent. PID reuse alone does not invalidate exits.
    starts=[p.name for p in m.private.iterdir() if p.is_dir() and p.name.startswith('start_')]
    c.require(starts==[ctx['owner']['start_id']],'EXTRA_OWNER_START_OR_UNKNOWN')
    eng=Path(ctx['plan']['engineering'])
    c.require({p.name for p in eng.iterdir()}=={ctx['plan']['job_name']+'.inp','scratch'}
              and not list((eng/'scratch').iterdir()),'OLD_OUTPUT_OR_SOLVER_INTENT')
    needed=('confirmation-packet.json','human-confirmation.json','authorize-request.json','owner-start-result.json',
            'pre-authorize-binding.json','dynamic-gate.json')
    native_files=[m._path(ctx['owner']['start_id']+'/'+name) for name in ('intent.json','created.json','ready.json','stopped.json')]
    native_files.extend((m._path('lifecycle-current.json'),Path(m.context.root)/'owner.json'))
    return dict(schema=SCHEMA,identity=expected,original_key=ctx['request']['operation_key'],native=native,
                journal=str(journal),journal_files={n:c.sha(journal/n) for n in needed},closure=closure,exits=exit_proof,
                native_files={str(p):c.sha(p) for p in native_files},
                classification='EXPIRED_UNCONSUMED_NOT_REVOKED_OR_RENEWED',normal_stop=True,
                execution_authorized=False,budget_changed=False),m,ctx

def proposal(camp,op,journal,closure):
    import execution_windows as ew
    import b_admission as b
    import window_history
    c.require(re.fullmatch('[a-f0-9]{32}',op or '') is not None,'EXACT_ARCHIVE_OPERATION_REQUIRED')
    c.require(not row(camp.db,op),'EXPIRED_GRANT_ARCHIVE_ALREADY_EXISTS_QUERY_OR_REPLAY')
    c.require(all(r['state']=='COMMITTED' for r in ew.rows(camp)),'WINDOW_PENDING_RECONCILE_ONLY')
    current,request,budget=b.phase(camp)
    parent,result=ew.parent(camp)
    proof,m,ctx=native_proof(journal,closure,parent['identity'])
    c.require(ctx['binding']==result and ctx['packet']['candidate']==request['candidate_id']
              and ctx['binding']['original_request']==c.case.hashbytes(current['request'])
              and ctx['binding']['contract']==camp.pin,'EXPIRED_GRANT_SCIENTIFIC_BINDING_CHANGED')
    response.scientific_context(ctx)
    chain=ew.historical_records(camp)
    for index,(r,body) in enumerate(chain[:-1]):
        old=json.loads(r['result']);ref=chain[index+1][1]['qualification_reference']
        window_history.closed_window(old['new']['af_project'],c.identity(old['new']),ref)
    return dict(schema=SCHEMA,operation_id=op,workspace=str(camp.root),project=request['project'],candidate=request['candidate_id'],
                contract=camp.pin,original_request=c.case.hashbytes(current['request']),parent=parent,
                history=c.fingerprint(camp),budget=budget,proof=proof,package=c.sha(Path(__file__).with_name('package-manifest.json')),
                execution_authorized=False,budget_changed=False,native_grant_modified=False)

def reference(camp,record):
    r,body=record
    return dict(schema=REFERENCE,operation_id=r['operation_id'],body_digest=r['body_digest'],workspace=str(camp.root))

def archive(camp,p,pin):
    """One local GD transaction/CAS. No cross-database atomicity claim."""
    c.require(c.pin(p)==pin,'EXPIRED_GRANT_PROPOSAL_CHANGED')
    previous=row(camp.db,p['operation_id'])
    if previous:
        c.require(previous[1]==p,'EXPIRED_GRANT_IDEMPOTENCY_CONFLICT')
        ref=reference(camp,previous)
        verify_reference(None,p['parent']['identity'],ref)
        return dict(reference=ref,replayed=True,budget_changed=False,native_grant_modified=False,execution_authorized=False)
    _,m,_=native_proof(p['proof']['journal'],p['proof']['closure'],p['parent']['identity'])
    with c.leases([m]):
        camp.db.execute('BEGIN IMMEDIATE')
        try:
            c.require(proposal(camp,p['operation_id'],p['proof']['journal'],p['proof']['closure'])==p,'EXPIRED_GRANT_ARCHIVE_CAS_CHANGED')
            # Existing schema is never migrated or rewritten by read-only open.
            camp.db.execute('CREATE TABLE IF NOT EXISTS '+TABLE+' (operation_id TEXT PRIMARY KEY,schema TEXT NOT NULL,grant_id TEXT NOT NULL UNIQUE,parent_operation_id TEXT NOT NULL UNIQUE,body BLOB NOT NULL,body_digest TEXT NOT NULL,state TEXT NOT NULL CHECK(state="COMMITTED"))')
            camp.db.execute('INSERT INTO '+TABLE+' VALUES(?,?,?,?,?,?,?)',(p['operation_id'],SCHEMA,p['proof']['native']['grant']['grant_id'],
                             p['parent']['operation_id'],c.pack(p),pin,'COMMITTED'))
            camp.db.commit()
        except BaseException:camp.db.rollback();raise
    return dict(reference=reference(camp,row(camp.db,p['operation_id'])),replayed=False,budget_changed=False,native_grant_modified=False,execution_authorized=False)

def verify_reference(manager,expected,ref):
    """Used by every native admission snapshot, not merely the local UI gate."""
    c.require(set(ref)=={'schema','operation_id','body_digest','workspace'} and ref['schema']==REFERENCE,'EXACT_EXPIRED_GRANT_REFERENCE_REQUIRED')
    work=c.local(ref['workspace'])
    if manager is not None:c.require(Path(manager.context.test_root).parent==work,'EXPIRED_GRANT_CROSS_PROJECT')
    db=sqlite3.connect((work/'workflow.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    try:record=row(db,ref['operation_id'])
    finally:db.close()
    c.require(record is not None and record[0]['body_digest']==ref['body_digest'],'EXPIRED_GRANT_ARCHIVE_REQUIRED')
    body=record[1]
    c.require(body['workspace']==str(work) and body['parent']['identity']==expected
              and body['budget']==dict(limit=2,held=1,charged=1,available=0)
              and body['execution_authorized'] is False and body['budget_changed'] is False and body['native_grant_modified'] is False,
              'EXPIRED_GRANT_ARCHIVE_SCOPE_CHANGED')
    actual,m,ctx=native_proof(body['proof']['journal'],body['proof']['closure'],expected)
    c.require(actual==body['proof'],'EXPIRED_GRANT_NATIVE_PROOF_CHANGED')
    c.require(body['project']==ctx['binding']['project']==ctx['packet']['project']
              and body['candidate']==ctx['binding']['candidate']==ctx['packet']['candidate']
              and body['contract']==ctx['binding']['contract']
              and body['original_request']==ctx['binding']['original_request']
              and body['parent']['operation_id']==ctx['packet']['operation_id']
              and body['parent']['result_pin']==c.pin(ctx['binding']),
              'EXPIRED_GRANT_ARCHIVE_SCIENTIFIC_IDENTITY_CHANGED')
    return dict(identity=expected,lifecycle='ORDERLY_STOP_RECORDED_EXPIRED_UNCONSUMED_GRANT',proof=actual,
                archive=dict(operation_id=ref['operation_id'],body_digest=ref['body_digest']),normal_stop=True),m

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('propose','archive','read'))
    for n in ('workspace','contract-pin','package-pin','python-exe','operation-id'):p.add_argument('--'+n,required=True)
    for n in ('journal','closure','closure-pin','proposal','proposal-pin'):p.add_argument('--'+n)
    a=p.parse_args();root=Path(__file__).resolve().parent
    from main import verify
    verify(root,a)
    from r3_bridge import trusted_af
    trusted_af()
    import workflow
    camp=workflow.Campaign(a.workspace,a.contract_pin,a.package_pin,readonly=a.action!='archive',candidate_b_admission=True)
    try:
        if a.action=='read':
            found=row(camp.db,a.operation_id);c.require(found is not None,'EXPIRED_GRANT_ARCHIVE_NOT_FOUND')
            ref=reference(camp,found);verify_reference(None,found[1]['parent']['identity'],ref)
            result=dict(record=found[1],reference=ref,execution_authorized=False)
        elif a.action=='propose':
            c.require(c.sha(c.local(a.closure))==a.closure_pin,'CLOSURE_REFERENCE_CHANGED')
            camp.db.execute('BEGIN')
            try:value=proposal(camp,a.operation_id,a.journal,response.read(a.closure))
            finally:camp.db.rollback()
            result=dict(proposal=value,proposal_digest=c.pin(value),execution_authorized=False)
        else:
            value=response.read(a.proposal);value=value.get('proposal',value)
            c.require(value['operation_id']==a.operation_id,'ARCHIVE_OPERATION_CHANGED')
            result=archive(camp,value,a.proposal_pin)
        print(json.dumps(result,indent=2))
    finally:camp.db.close()

if __name__=='__main__':
    sys.path[:0]=[str(Path(__file__).resolve().parent),str(Path(__file__).resolve().parent/'runtime')]
    main()
