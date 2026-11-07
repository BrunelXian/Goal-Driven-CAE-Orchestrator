"""Native acceptance facts in the existing workflow DB; not a second balance.

The frozen campaign's scientific outcome still settles its reservation. Native
consumption is recorded and displayed separately while feedback is pending.
No Grant-only charge, refund, replay or execution authority is implemented.
"""
import json,sqlite3
from pathlib import Path
import continuation as c
TABLE='tensile_native_acceptance_facts'

def source(camp,phase='B'):
    c.require(phase=='B','EXACT_B_FACT_REQUIRED')
    import execution_windows as w
    row=camp.db.execute("SELECT * FROM stages WHERE phase='B'").fetchone()
    req,pin,product=w.effective(camp,row)
    expected=w.snapshot(camp,'--terminal')['result']['new']
    from abqjobpilot.service_lifecycle import ServiceLifecycleManager
    from abqjobpilot.execution.models import digest,canonical_json,CANONICAL,CONTRACT
    m=ServiceLifecycleManager(product)
    db=sqlite3.connect((Path(m.context.root)/'execution.sqlite3').as_uri()+'?mode=ro',uri=True)
    try:
        db.execute('BEGIN')
        runs=db.execute('SELECT body FROM runs').fetchall();receipts=db.execute('SELECT namespace,key,request_digest,run_id,body FROM receipts').fetchall()
        c.require(len(runs)==len(receipts)==1,'EXACT_ONE_NATIVE_ACCEPTANCE_REQUIRED')
        run=json.loads(runs[0][0]);rr=receipts[0];receipt=json.loads(rr[4])
        p=json.loads(db.execute('SELECT body FROM plans').fetchone()[0]);u=dict(p)
        c.require(u.pop('plan_digest')==digest(u),'NATIVE_PLAN_CHANGED')
        from abqjobpilot.execution.product_standard import scope
        c.require(expected['plan']==p and expected['scope_digest']==digest(scope(p))
            and expected['af_project']==str(product) and expected['project_id']==m.context.project_id
            and expected['project_instance_id']==m.context.project_instance_id,'NATIVE_FACT_CURRENT_BINDING_CHANGED')
        c.require(p['registration']['request']==pin and p['registration']['candidate']==req['candidate_id']
                  and p['registration']['research_project']==req['project'],'NATIVE_SCIENTIFIC_BINDING_CHANGED')
        c.require(run['plan_id']==p['plan_id'] and run['plan_digest']==p['plan_digest'] and run['project_instance_id']==m.context.project_instance_id
                  and run['job_id']==p['job_id'] and run['job_revision']==p['job_revision'],'NATIVE_RUN_BINDING_CHANGED')
        c.require(receipt['request_status']=='ACCEPTED' and receipt['run_id']==run['run_id'] and receipt['job_id']==run['job_id']
                  and tuple(rr[:4])==(receipt['namespace'],receipt['idempotency_key'],receipt['request_digest'],run['run_id']), 'NATIVE_RECEIPT_BINDING_CHANGED')
        semantic=dict(contract_version=CONTRACT,operation='submit',project_id=m.context.project_id,project_instance_id=m.context.project_instance_id,
            job_id=p['job_id'],job_revision=p['job_revision'],plan_id=p['plan_id'],plan_digest=p['plan_digest'],grant_id=run['grant_id'],retry_of=None,
            context_digest=m.context.context_digest,canonicalization=CANONICAL)
        c.require(receipt['namespace']==canonical_json([m.context.project_instance_id,m._profile()['client_namespace'],'submit'])
            and receipt['request_digest']==digest(semantic),'NATIVE_RECEIPT_SEMANTIC_CHANGED')
        c.require(db.execute('SELECT grant_id,run_id FROM consumption').fetchall()==[(run['grant_id'],run['run_id'])],'NATIVE_CONSUMPTION_CHANGED')
        grant=json.loads(db.execute('SELECT body FROM grants WHERE grant_id=?',(run['grant_id'],)).fetchone()[0])
        c.require(grant['plan_id']==p['plan_id'] and grant['plan_digest']==p['plan_digest'],'NATIVE_GRANT_BINDING_CHANGED')
        ev=[dict(json.loads(x[1]),project_sequence=x[0]) for x in db.execute('SELECT sequence,body FROM events WHERE run_id=?',(run['run_id'],))]
        accepted=[e for e in ev if e['type']=='REQUEST_ACCEPTED']
        c.require(len(accepted)==1 and accepted[0]['project_sequence']==receipt['accepted_sequence'],'NATIVE_ACCEPTED_EVENT_CHANGED')
        return dict(schema='native-acceptance-fact-v1',phase=phase,project=req['project'],candidate=req['candidate_id'],contract=camp.pin,
          original_request=c.case.hashbytes(row['request']),effective_request=pin,af_project=str(product),project_instance_id=m.context.project_instance_id,
          plan_id=p['plan_id'],plan_digest=p['plan_digest'],run_id=run['run_id'],grant_id=run['grant_id'],receipt=receipt,
          accepted_event=accepted[0],native_consumed=1,scientific_charge_policy='UNCHANGED_FROZEN_OUTCOME_SETTLEMENT',execution_authorized=False)
    finally:db.close()

def record_acceptance(camp,phase='B'):
    value=source(camp,phase);raw=c.pack(value);pin=c.pin(value)
    camp.db.execute('BEGIN IMMEDIATE')
    try:
        camp.verified_rows(terminal_structure_only=True)
        camp.db.execute('CREATE TABLE IF NOT EXISTS '+TABLE+'(phase TEXT PRIMARY KEY,run_id TEXT UNIQUE NOT NULL,body BLOB NOT NULL,pin TEXT NOT NULL)')
        old=camp.db.execute('SELECT run_id,body,pin FROM '+TABLE+' WHERE phase=?',(phase,)).fetchone()
        if old is not None:c.require(tuple(old)==(value['run_id'],raw,pin),'NATIVE_FACT_CONFLICT')
        else:camp.db.execute('INSERT INTO '+TABLE+' VALUES(?,?,?,?)',(phase,value['run_id'],raw,pin))
        camp.db.commit();return dict(value,replayed=old is not None)
    except BaseException:camp.db.rollback();raise

def feedback_once(camp,request_pin):
    """Idempotent terminal observation. An incomplete scientific INTENT is not retried."""
    rows=camp.verified_rows(terminal_structure_only=True)
    c.require(len(rows)==2 and rows[0]['state']=='MISS','ORIGINAL_A_AND_B_REQUIRED')
    row=rows[-1]
    c.require(row['phase']=='B' and c.case.hashbytes(row['request'])==request_pin,'EXACT_ORIGINAL_B_REQUEST_REQUIRED')
    if row['state'] in ('GOAL_MET','EXHAUSTED','FAILED'):
        c.require(row['result'] is not None,'TERMINAL_RESULT_REQUIRED')
        feedback=camp.feedback(row)
        return dict(status='ALREADY_COMMITTED_NATIVE',phase='B',feedback=feedback,budget=camp.counts(rows),replayed=True)
    record_acceptance(camp,'B')
    if row['state']=='INTENT':
        from terminal_materialization import complete_intent
        return complete_intent(camp,row)
    c.require(row['state']=='PREPARED','SCIENTIFIC_STATE_UNKNOWN_READONLY_RECONCILE_ONLY')
    return camp.observe('B',request_pin,'NATIVE')
