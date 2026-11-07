"""One explicitly qualified B window; original scientific B/HOLD stays authoritative.

The append-only window_revision is not a Core revision, retry or new Candidate. Cross
database preparation uses a durable INTENT and explicit reconciliation, not an
atomic transaction claim. Read-only opening never creates the table.
"""
import json,os,re,subprocess,time,sqlite3
from pathlib import Path
import continuation as c
import b_admission as b
import window_history as old_recovery
import b_readmission as legacy

TABLE='tensile_execution_windows'
SCHEMA='expired-unexecuted-b-execution-window-v1'
BUDGET=dict(limit=2,held=1,charged=1,available=0)
COUNTS=dict(plans=1,grants=0,runs=0,receipts=0,consumption=0)

def compatibility():
    path=c.local(Path(__file__).with_name('execution_window_compatibility.json'))
    manifest=json.loads(c.local(Path(__file__).with_name('package-manifest.json')).read_bytes())
    c.require(c.sha(path)==manifest['files']['execution_window_compatibility.json'],'B_COMPATIBILITY_RECORD_CHANGED')
    spec=json.loads(path.read_bytes())
    c.require(spec['schema']=='execution-window-parent-compatibility-v1','B_COMPATIBILITY_REQUIRED')
    root=c.local(spec['root'])
    c.require(c.sha(root/'FREEZE.json')==spec['freeze_sha256'],'B_PARENT_FREEZE_CHANGED')
    actual={str(p.relative_to(root)):c.sha(p) for part in ('gd','af') for p in sorted((root/part).rglob('*')) if p.is_file()}
    c.require(actual==spec['files'] and c.sha(root/'gd/package-manifest.json')==spec['package'],'B_PARENT_INSTALLATION_CHANGED')
    for name in ('tensile.py','scoring.py','odb_reader.py','workflow.py'):
        c.require(c.sha(Path(__file__).with_name(name))==c.sha(root/'gd'/name),'B_SCIENTIFIC_SEMANTICS_CHANGED')
    return spec

def historical_records(camp):
    """Original scientific request and every prior committed execution binding.

    Read raw historical records through their exact structural validators, not
    the old runtime's current-window/PID-absence admission convenience path.
    """
    spec=compatibility();original_install=legacy.compatibility()
    first,body=b.record(camp)
    c.require(first['state']=='COMMITTED','ORIGINAL_B_COMMITTED_REQUIRED')
    stage=camp.db.execute("SELECT * FROM stages WHERE phase='B'").fetchone();request=camp.check_row(stage)
    accepted,_=b.decision(camp)
    c.require(body['request']==request and body['original_request']==c.case.hashbytes(stage['request'])
        and body['project']==request['project'] and body['candidate']==request['candidate_id']
        and body['contract']==camp.pin and body['budget']==BUDGET and body['package']==original_install['package']
        and body['source_A_result']==accepted['source_A_result_sha256'] and body['decision_reference']==accepted['decision_reference'],
        'ORIGINAL_B_SCIENTIFIC_LINEAGE_CHANGED')
    chain=[(dict(first),body)]
    for r in legacy.rows(camp):
        c.require(r['state']=='COMMITTED','LEGACY_PENDING_RECONCILE_REQUIRED')
        v=json.loads(r['body']);c.require(v['package']==spec['package'],'LEGACY_PACKAGE_CHANGED')
        c.require(v['request']==request and v['original_request']==body['original_request'] and v['project']==body['project']
            and v['candidate']==body['candidate'] and v['contract']==camp.pin and v['source_A_result']==body['source_A_result']
            and v['decision_reference']==body['decision_reference'],'LEGACY_B_SCIENTIFIC_LINEAGE_CHANGED')
        chain.append((dict(r),v))
    for r in rows(camp):
        v=json.loads(r['body']);pr,pb=chain[-1];pp=v['parent']['parent']
        c.require(pp['operation_id']==pr['operation_id'] and pp['body_pin']==pr['body_pin'] and pp['result_pin']==pr['result_pin']
            and pp['package']==pb['package'] and pp['identity']==c.identity(json.loads(pr['result'])['new'])
            and pp['chain_digest']==c.pin([dict(operation_id=x['operation_id'],body_pin=x['body_pin'],result_pin=x['result_pin']) for x,_ in chain]),'WINDOW_PARENT_CHAIN_CHANGED')
        if r['state']=='COMMITTED':chain.append((dict(r),v))
    return chain

def parent(camp):
    chain=historical_records(camp);r,body=chain[-1];result=json.loads(r['result'])
    return dict(operation_id=r['operation_id'],body_pin=r['body_pin'],result_pin=r['result_pin'],
                package=body['package'],identity=c.identity(result['new']),
                chain_digest=c.pin([dict(operation_id=x['operation_id'],body_pin=x['body_pin'],result_pin=x['result_pin']) for x,_ in chain])),result

def stopped(camp,ref,expected=None):
    chain=historical_records(camp)
    # During INTENT/COMMITTED re-reading, ancestry ends before this window.
    if expected is not None:
        match=[i for i,(r,_) in enumerate(chain) if r['operation_id']==expected['parent']['operation_id']]
        c.require(len(match)==1,'WINDOW_PARENT_NOT_FOUND');chain=chain[:match[0]+1]
    p_r,p_b=chain[-1];p=dict(operation_id=p_r['operation_id'],body_pin=p_r['body_pin'],result_pin=p_r['result_pin'],
        package=p_b['package'],identity=c.identity(json.loads(p_r['result'])['new']),
        chain_digest=c.pin([dict(operation_id=x['operation_id'],body_pin=x['body_pin'],result_pin=x['result_pin']) for x,_ in chain]))
    proofs=[];managers=[]
    for i,(r,body) in enumerate(chain):
        result=json.loads(r['result']);new=result['new'];identity=c.identity(new)
        qref=ref if i==len(chain)-1 else chain[i+1][1]['qualification_reference']
        actual,m=b.native(new['af_project'])
        c.require(all(actual[k]==new[k] for k in new if k!='counts'),'ANCESTOR_ACTUAL_PLAN_CHANGED')
        proof,m=old_recovery.closed_window(new['af_project'],identity,qref)
        proofs.append(proof);managers.append(m)
    value=dict(parent=p,stopped=proofs)
    c.require(expected is None or value==expected,'B_ANCESTOR_CHANGED')
    return value,managers

def rows(camp):
    if not camp.db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(TABLE,)).fetchone():return []
    rs=list(camp.db.execute('SELECT * FROM '+TABLE+' ORDER BY window_revision'));c.require([r['window_revision'] for r in rs]==list(range(1,len(rs)+1)) and all(r['state']=='COMMITTED' for r in rs[:-1]),'WINDOW_CHAIN_OR_PENDING_CHANGED')
    for r in rs:
        body=json.loads(r['body'])
        c.require(r['window_revision']==body['window_revision'] and r['body_pin']==c.case.hashbytes(r['body']) and body['schema']==SCHEMA
                  and body['operation_id']==r['operation_id'] and body['window_revision']>=1
                  and r['state'] in ('INTENT','COMMITTED'),'B_READMISSION_RECORD_CHANGED')
        if r['state']=='INTENT':c.require(r['result'] is None and r['result_pin'] is None,'B_READMISSION_UNKNOWN')
        else:
            v=json.loads(r['result'])
            c.require(c.case.hashbytes(r['result'])==r['result_pin'] and set(v)=={'schema','operation_id','window_revision','proposal_digest','parent','new','project','candidate','contract','original_request','request_digest','budget','execution_authorized'}
                      and v['schema']==SCHEMA and v['execution_authorized'] is False and v['proposal_digest']==r['body_pin']
                      and all(v[k]==body[k] for k in ('operation_id','window_revision','parent','project','candidate','contract','original_request','request_digest','budget')),
                      'B_READMISSION_RESULT_CHANGED')
            n=v['new'];p=n['plan'];reg=p['registration'];req=body['effective_request']
            c.require(set(n)=={'plan','scope_digest','af_project','project_id','project_instance_id','counts'} and n['counts']==COUNTS
                      and n['af_project']==body['new_af_project'] and p['expires_at']==r['expires_at']
                      and reg['project_id']==n['project_id'] and reg['project_instance_id']==n['project_instance_id']==p['project_instance_id']
                      and reg['context_digest']==p['context_digest'] and reg['research_project']==body['project']
                      and reg['candidate']==body['candidate'] and reg['contract']==body['contract'] and reg['request']==body['request_digest']
                      and reg['gd_package']==body['package'] and reg['phase']==req['phase']=='B'
                      and reg['job']==p['job_name']==req['job'] and reg['engineering']==p['engineering']==req['expected_work_dir']
                      and reg['output']==req['output_key'] and reg['parameters']==req['parameters']
                      and reg['input_digest']=='sha256:'+req['inp_sha256'] and reg['prior']==req['prior_feedback_sha256']
                      and reg['resources']==p['resources']==req['resource_review'] and reg['purpose']==body['purpose'],
                      'B_READMISSION_NATIVE_SCOPE_CHANGED')
    return rs

def record(camp):
    rs=rows(camp);c.require(bool(rs),'EXECUTION_WINDOW_REQUIRED');return rs[-1],json.loads(rs[-1]['body'])

def new_unstarted_window(product):
    """Full native empty-window proof for finalize/gate, never terminal reads."""
    value,m=c.native(product)
    db=sqlite3.connect((Path(m.context.root)/'execution.sqlite3').as_uri()+'?mode=ro',uri=True)
    try:c.require(all(db.execute('SELECT count(*) FROM '+t).fetchone()[0]==0 for t in ('management_grants','management_consumption','reconciliations','control_events')),'B_NEW_ADMINISTRATIVE_UNKNOWN')
    finally:db.close()
    return {**value,'counts':{k:value['counts'][k] for k in COUNTS}},m

def proposal(camp,op,qualification):
    c.require(re.fullmatch('[a-f0-9]{32}',op or '') is not None,'EXACT_B_OPERATION_REQUIRED')
    c.require(all(r['state']=='COMMITTED' for r in rows(camp)),'WINDOW_PENDING_RECONCILE_ONLY')
    row,req,budget=b.phase(camp);accepted,_=b.decision(camp)
    ancestry,_=stopped(camp,qualification)
    dest=camp.root/('af-B-window-'+op);job='Tensile_B_'+op[:16]
    c.require(not dest.exists() and not (camp.root/job).exists(),'UNIQUE_B_OUTPUT_REQUIRED')
    effective={**req,'job':job,'input_name':job+'.inp','expected_odb':job+'.odb','output_key':op[:16],'expected_work_dir':str(dest/'engineering')}
    return dict(schema=SCHEMA,operation_id=op,window_revision=len(rows(camp))+1,project=req['project'],candidate=req['candidate_id'],contract=camp.pin,
                original_request=c.case.hashbytes(row['request']),request=req,effective_request=effective,request_digest=c.pin(effective),
                package=c.sha(Path(__file__).with_name('package-manifest.json')),parent=ancestry,
                source_A_result=accepted['source_A_result_sha256'],decision_reference=accepted['decision_reference'],
                qualification_reference=qualification,history=c.fingerprint(camp),budget=budget,purpose=camp.c['af_purpose'],
                new_af_project=str(dest),execution_authorized=False)

def static(camp,op,qualification):
    from r3_bridge import trusted_af
    trusted_af()
    from readiness import operator_readiness
    camp.db.execute('BEGIN')
    try:
        p=proposal(camp,op,qualification);_,ms=stopped(camp,qualification,p['parent'])
        return dict(status='STATIC_READONLY_READY',proposal=p,proposal_digest=c.pin(p),budget=p['budget'],plan_created=False,
                    execution_authorized=False,native_operator_readiness=operator_readiness(ms[-1]),scope='ONE_CURRENT_B_WINDOW_NO_EXECUTION_RETRY')
    finally:camp.db.rollback()

def snapshot(camp,mode,operation_id=None):
    c.require(mode in ('--preparation','--committed','--terminal'),'B_SNAPSHOT_MODE_REQUIRED')
    row,req,budget=b.phase(camp,mode=='--terminal');r,body=record(camp)
    if operation_id is not None:
        matches=[v for v in rows(camp) if v['operation_id']==operation_id]
        c.require(len(matches)==1,'EXACT_WINDOW_REQUIRED');r=matches[0];body=json.loads(r['body'])
    if mode=='--committed':
        c.require(rows(camp)[-1]['operation_id']==r['operation_id'] and all(x['state']=='COMMITTED' for x in rows(camp)),'WINDOW_NOT_CURRENT_OR_PENDING')
    accepted,_=b.decision(camp);op=r['operation_id'];dest=camp.root/('af-B-window-'+op);job='Tensile_B_'+op[:16]
    effective={**req,'job':job,'input_name':job+'.inp','expected_odb':job+'.odb','output_key':op[:16],'expected_work_dir':str(dest/'engineering')}
    c.require(body['contract']==camp.pin and body['project']==req['project'] and body['candidate']==req['candidate_id']
              and body['original_request']==c.case.hashbytes(row['request']) and body['request']==req
              and body['effective_request']==effective and body['request_digest']==c.pin(effective) and body['new_af_project']==str(dest)
              and body['package']==c.sha(Path(__file__).with_name('package-manifest.json')) and body['budget']==BUDGET
              and body['purpose']==camp.c['af_purpose'] and body['source_A_result']==accepted['source_A_result_sha256']
              and body['decision_reference']==accepted['decision_reference'] and body['execution_authorized'] is False,'B_READMISSION_SCOPE_CHANGED')
    stopped(camp,body['qualification_reference'],body['parent'])
    if mode in ('--committed','--terminal'):c.require(r['state']=='COMMITTED','B_READMISSION_NOT_COMMITTED')
    if r['state']=='INTENT':c.require(c.fingerprint(camp)==body['history'],'B_READMISSION_PENDING_CAS_CHANGED')
    folder=c.local(camp.root/job)
    c.require((folder/effective['input_name']).read_bytes()==row['inp'] and (folder/'handoff.json').read_bytes()==c.pack(effective),'B_EFFECTIVE_INPUT_CHANGED')
    lineage=dict(schema=SCHEMA,window_revision=r['window_revision'],operation_id=op,body_digest=r['body_pin'],parent=body['parent']['parent'],
                 source_A_result=body['source_A_result'],original_request=body['original_request'],expires_at=r['expires_at'])
    return dict(req=effective,project=body['project'],request=body['request_digest'],package=body['package'],contract=camp.pin,
                purpose=body['purpose'],execution_window=lineage,state=r['state'],result=json.loads(r['result']) if r['result'] else None)

def claim(camp,p,pin,expires):
    c.require(type(expires) is int and time.time()<expires<=int(time.time())+600,'BOUNDED_B_EXPIRY_REQUIRED')
    camp.db.execute('BEGIN IMMEDIATE')
    try:
        c.require(c.pin(p)==pin and proposal(camp,p['operation_id'],p['qualification_reference'])==p,'B_READMISSION_STATIC_CAS_CHANGED')
        row,_,_=b.phase(camp)
        camp.db.execute('CREATE TABLE IF NOT EXISTS '+TABLE+' (operation_id TEXT PRIMARY KEY,window_revision INTEGER UNIQUE,body BLOB,body_pin TEXT,state TEXT,expires_at INTEGER,result BLOB,result_pin TEXT)')
        camp.db.execute('INSERT INTO '+TABLE+' VALUES(?,?,?,?,?,?,NULL,NULL)',(p['operation_id'],p['window_revision'],c.pack(p),pin,'INTENT',expires));camp.db.commit();return row
    except BaseException:camp.db.rollback();raise

def finalize(camp,op):
    from abqjobpilot.product_standard import inspect_preparation
    r,body=record(camp);c.require(r['operation_id']==op and r['state']=='INTENT','SAME_PENDING_B_OPERATION_REQUIRED')
    _,m=stopped(camp,body['qualification_reference'],body['parent'])
    with c.leases(m):
        snap=snapshot(camp,'--preparation');actual,_=new_unstarted_window(body['new_af_project']);p=actual['plan']
        from abqjobpilot.execution.tensile_profile import spec_config
        c.require(actual['counts']==COUNTS and p['registration']['execution_window']==snap['execution_window']
                  and p['runtime_binding']==spec_config().value() and p['expires_at']==r['expires_at'] and p['expires_at']>time.time(),
                  'B_NEW_WINDOW_NOT_QUALIFIED')
        camp.db.execute('BEGIN IMMEDIATE')
        try:
            rr,bb=record(camp);b.phase(camp)
            c.require(rr['state']=='INTENT' and bb==body and c.fingerprint(camp)==body['history'],'B_READMISSION_FINALIZE_CAS_CHANGED')
            stopped(camp,body['qualification_reference'],body['parent'])
            v=dict(schema=SCHEMA,window_revision=r['window_revision'],operation_id=op,proposal_digest=r['body_pin'],parent=body['parent'],new=actual,
                   project=body['project'],candidate=body['candidate'],contract=camp.pin,original_request=body['original_request'],
                   request_digest=body['request_digest'],budget=body['budget'],execution_authorized=False)
            q=camp.db.execute('UPDATE '+TABLE+" SET state='COMMITTED',result=?,result_pin=? WHERE operation_id=? AND state='INTENT' AND body_pin=?",
                             (c.pack(v),c.pin(v),op,r['body_pin']));c.require(q.rowcount==1,'B_READMISSION_FINALIZE_CONFLICT');camp.db.commit()
        except BaseException:camp.db.rollback();raise
    c.require(inspect_preparation(body['new_af_project'])['plan']==p,'B_NATIVE_RECHECK_FAILED')
    return v

def prepare(camp,p,pin,expires):
    from r3_bridge import trusted_af
    trusted_af()
    from abqjobpilot.product_project import create_project
    from abqjobpilot.product_standard import prepare_product
    from abqjobpilot.execution.tensile_profile import spec_config
    _,m=stopped(camp,p['qualification_reference'],p['parent'])
    with c.leases(m):
        row=claim(camp,p,pin,expires);req=p['effective_request'];folder=camp.root/req['job'];folder.mkdir()
        for path,raw in ((folder/req['input_name'],row['inp']),(folder/'handoff.json',c.pack(req))):
            with path.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
        product=Path(p['new_af_project']);create_project(product,req['job']);eng=Path(req['expected_work_dir']);eng.mkdir();(eng/'scratch').mkdir()
        with (eng/req['input_name']).open('xb') as f:f.write(row['inp']);f.flush();os.fsync(f.fileno())
        prepare_product(product,eng,req['job'],spec_config(),expires_at=expires,model_profile='tensile-bilinear-3d-r3',preparation_purpose=p['purpose'])
    return finalize(camp,p['operation_id'])

def dynamic(camp,path):
    from r3_bridge import trusted_af
    trusted_af()
    from abqjobpilot.product_standard import inspect_preparation
    from readiness import operator_readiness
    supplied=json.loads(c.local(path).read_bytes());camp.db.execute('BEGIN')
    try:
        snap=snapshot(camp,'--committed');r,body=record(camp);result=json.loads(r['result'])
        c.require(result==supplied,'B_RESULT_NOT_PERSISTED');actual,m=new_unstarted_window(body['new_af_project'])
        c.require(actual==result['new'],'B_NATIVE_PLAN_CHANGED')
        view=inspect_preparation(actual['af_project']);p=actual['plan']
        c.require(view['plan']==p and p['registration']['execution_window']==snap['execution_window'] and view['counts']==COUNTS
                  and view['supervisor_started']=='0' and view['gate']['state']=='PAUSED' and p['expires_at']-time.time()>=60,'B_DYNAMIC_PREFLIGHT_CHANGED')
        owner=m.inspect();c.require(owner==dict(state='NOT_RUNNING',reason='EXPLICIT_START_REQUIRED'),'B_OWNER_NOT_EMPTY')
        return dict(result,status='DYNAMIC_READONLY_PASS',plan_id=p['plan_id'],plan_digest=p['plan_digest'],scope_digest=actual['scope_digest'],
                    expires_at=p['expires_at'],native_operator_readiness=operator_readiness(m),owner=owner)
    finally:camp.db.rollback()

def effective(camp,row):
    rs=rows(camp)
    committed=[r for r in rs if r['state']=='COMMITTED']
    if not committed:return legacy.effective(camp,row)
    r=committed[-1];snap=snapshot(camp,'--terminal',r['operation_id'])
    return snap['req'],snap['request'],Path(json.loads(r['body'])['new_af_project'])

def reconcile(camp,op):
    r,body=record(camp);c.require(r['operation_id']==op,'B_OPERATION_MISMATCH')
    if r['state']=='COMMITTED':
        snapshot(camp,'--terminal');result=json.loads(r['result']);actual,_=b.native(body['new_af_project'])
        c.require(all(actual[k]==result['new'][k] for k in actual if k!='counts'),'B_RECONCILIATION_NATIVE_CHANGED')
        return dict(state='COMMITTED',result=result,current_native_counts=actual['counts'],execution_authorized=False)
    try:
        snap=snapshot(camp,'--preparation');actual,_=new_unstarted_window(body['new_af_project'])
        c.require(actual['plan']['registration']['execution_window']==snap['execution_window'],'B_PARTIAL_LINEAGE_CHANGED')
        return dict(state='AF_PREPARED_GD_INTENT',operation_id=op,new=actual,next='explicit same-operation finalize only',execution_authorized=False)
    except Exception as exc:return dict(state='RECONCILIATION_REQUIRED',detail=str(exc),automatic_retry=False,execution_authorized=False)
