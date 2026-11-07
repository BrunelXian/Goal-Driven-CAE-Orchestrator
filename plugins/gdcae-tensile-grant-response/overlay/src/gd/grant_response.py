"""Read-only acknowledgement of one existing native authorization; never issue one.

The journal is an operation record, not a Grant authority. Native authenticated
receipt, native SQLite binding and original installed scientific ledger must all
agree. Expired committed authorization stays committed but is not executable.
"""
import hashlib,json,re,sqlite3,subprocess,sys,time
from pathlib import Path

def require(value,reason):
    if not value:raise ValueError(reason)

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(path):
    from main import safe
    path=safe(path)
    with path.open('rb') as stream:raw=stream.read(1048577)
    require(len(raw)<=1048576,'RECOVERY_RECORD_LIMIT')
    return json.loads(raw)

def installation(packet):
    """Explicit read-only .11.1 compatibility; never pretend its runtime is ours."""
    from main import safe
    root=Path(__file__).resolve().parent
    value=packet['installation'];old=safe(value['gd_installed'])
    if old==root:
        from types import SimpleNamespace
        from main import verify
        verify(root,SimpleNamespace(package_pin=value['gd_package_sha256'],python_exe=sys.executable))
    else:
        spec=read(root/'grant_response_compatibility.json')
        require(spec['schema']=='grant-response-readonly-runtime-v1' and str(old)==spec['gd_root']
                and value['gd_package_sha256']==spec['package_pin'],'RECOVERY_INSTALLATION_NOT_QUALIFIED')
        parent=safe(spec['root'])
        require(sha(parent/'FREEZE.json')==spec['freeze_sha256'],'RECOVERY_OLD_FREEZE_CHANGED')
        freeze=read_large_freeze(parent/'FREEZE.json')
        for name,pin in spec['files'].items():
            require(freeze['files'].get(name)==pin and sha(parent/name)==pin,'RECOVERY_OLD_INSTALLATION_CHANGED')
    require(sha(old/'package-manifest.json')==value['gd_package_sha256']
            and sha(old/'af_installation.py')==value['af_identity'],'RECOVERY_PACKAGE_CHANGED')
    # No code execution from arbitrary packet paths: they are current or pinned.
    import ast
    tree=ast.parse((old/'af_installation.py').read_text(encoding='utf8'))
    assignments={n.targets[0].id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)}
    require(assignments['ROOT']==value['af_installed'] and assignments['GD_ROOT']==str(old),'RECOVERY_AF_INSTALLATION_CHANGED')
    af=safe(value['af_installed'])
    for name,pin in assignments['FILES'].items():require(sha(af/name)==pin,'RECOVERY_AF_PAYLOAD_CHANGED')
    require({p.relative_to(af).as_posix() for p in (af/'abqjobpilot').rglob('*') if p.is_file() and p.name!='tensile_catalog.py'}==set(assignments['FILES']),
            'RECOVERY_AF_FILESET_CHANGED')
    return old

def read_large_freeze(path):
    with Path(path).open('rb') as stream:raw=stream.read((4<<20)+1)
    require(len(raw)<=4<<20,'RECOVERY_FREEZE_LIMIT');return json.loads(raw)

def packet_context(journal):
    from main import safe
    from approval_dialog import packet_digest
    from abqjobpilot.execution.models import digest
    from abqjobpilot.execution.product_standard import scope
    journal=safe(journal);packet=read(journal/'confirmation-packet.json')
    proof=read(journal/'human-confirmation.json');request=read(journal/'authorize-request.json')
    owner=read(journal/'owner-start-result.json');binding=read(journal/'pre-authorize-binding.json')
    checked=read(journal/'dynamic-gate.json');plan=packet['plan'];op=packet['operation_id'];args=request['arguments']
    require(re.fullmatch('[a-f0-9]{32}',op) and re.fullmatch('authorize_[a-f0-9]{32}',request['operation_key']),'RECOVERY_EXACT_KEY_REQUIRED')
    require(proof['status']=='USER_DECISION_CAPTURED' and proof['input_method']=='local_win32_mouse' and proof['packet_sha256']==packet_digest(packet)
            and proof['operation_id']==op,'RECOVERY_HUMAN_PACKET_CHANGED')
    require(owner==packet['owner'] and owner['state']=='CONNECTED' and owner['created'] is True,'RECOVERY_OWNER_BINDING_CHANGED')
    require(binding['new']==checked['new'] and checked['new']['plan']==plan and checked['operation_id']==op
            and packet['af_project']==checked['new']['af_project'] and packet['candidate']==checked['candidate']==binding['candidate']
            and packet['project']==checked['project']==binding['project']
            and packet['budget']==binding['budget']==checked['budget']==dict(limit=2,held=1,charged=1,available=0),
            'RECOVERY_RESEARCH_BINDING_CHANGED')
    unsigned=dict(plan);require(unsigned.pop('plan_digest')==digest(unsigned),'RECOVERY_PLAN_DIGEST_CHANGED')
    expected=dict(plan_id=plan['plan_id'],plan_digest=plan['plan_digest'],expires_at=plan['expires_at'],subject=args['subject'],source=digest(scope(plan)))
    require(args==expected and plan['registration']['phase']=='B' and packet['scope_digest']==checked['scope_digest']==expected['source']
            and plan['registration']['candidate']==packet['candidate'] and plan['registration']['research_project']==packet['project']
            and packet['input_manifest']==plan['input_manifest'] and packet['parameters']==plan['registration']['parameters']
            and packet['resources']==plan['resources'] and packet['expires_at']==plan['expires_at'], 'RECOVERY_AUTHORIZATION_SCOPE_CHANGED')
    for key in ('plan_id','plan_digest','job_id','job_revision','job_name','engineering','scratch','output_key'):
        require(packet[key]==plan[key],'RECOVERY_DISPLAY_BINDING_CHANGED')
    require(safe(packet['af_project']).parent==journal.parent,'RECOVERY_PROJECT_OUTSIDE_WORKSPACE')
    old=installation(packet)
    return dict(journal=journal,packet=packet,request=request,owner=owner,plan=plan,binding=binding,old=old)

def scientific_context(ctx):
    """Use the exact qualified original installed reader, not a new runtime alias."""
    p=ctx['packet'];plan=ctx['plan'];root=ctx['old'];journal=ctx['journal']
    require(sha(journal.parent/'contract.json')==ctx['binding']['contract'],'RECOVERY_CONTRACT_CHANGED')
    mode='b-window:'+p['operation_id']
    result=subprocess.run([sys.executable,'-I','-B','-S',str(root/'admission_snapshot.py'),str(journal.parent),mode,'--committed'],
                          capture_output=True,timeout=60,stdin=subprocess.DEVNULL,cwd=root)
    require(result.returncode==0,'RECOVERY_ORIGINAL_LEDGER_UNVERIFIED')
    snap=json.loads(result.stdout)
    require(snap['result']==ctx['binding'] and snap['result']['new']['plan']==plan
            and snap['contract']==ctx['binding']['contract'] and snap['project']==p['project']
            and snap['state']=='COMMITTED' and snap['package']==p['installation']['gd_package_sha256'],
            'RECOVERY_ORIGINAL_LEDGER_CHANGED')
    return snap

def durable(ctx,manager):
    """Full native transaction row cross-binding, even when receipt is absent."""
    from abqjobpilot.execution.models import digest,canonical_json
    from abqjobpilot.execution.product_standard import scope
    from abqjobpilot.local_credentials import read_private,user_sid
    m=manager;plan=ctx['plan'];owner=ctx['owner'];req=ctx['request'];args=req['arguments'];key=req['operation_key']
    profile=m._profile();current=m._current();context=m.context
    require(current and current['start_id']==owner['start_id'] and m._stopped(current) is None,'RECOVERY_OWNER_LIFECYCLE_CHANGED')
    ready=read(m._path(owner['start_id']+'/ready.json'))
    require(ready['owner_id']==owner['owner_id'] and ready['start_id']==owner['start_id'],'RECOVERY_READY_CHANGED')
    ext=profile['standard_extension'];binding=ext['binding'];cap=read_private(context,m._path('standard-operator.json'))
    require(digest(cap['operator_token'])==binding['operator_digest'] and cap['context_digest']==context.context_digest
            and args['subject']==user_sid(),'RECOVERY_NATIVE_CAPABILITY_CHANGED')
    require(binding['plan_id']==plan['plan_id'] and binding['plan_digest']==plan['plan_digest']
            and plan['runtime_binding']==ext['standard_config'],'RECOVERY_NATIVE_PROFILE_CHANGED')
    from abqjobpilot.execution.standard_contract import StandardConfig
    StandardConfig(canonical_json(plan['runtime_binding'])).verify()
    require(plan['project_instance_id']==context.project_instance_id and plan['context_digest']==context.context_digest
            and plan['registration']['project_id']==context.project_id,'RECOVERY_NATIVE_PROJECT_CHANGED')
    reg=read_private(context,m._path('tensile-registration.json'))
    require(reg==plan['registration'],'RECOVERY_NATIVE_REGISTRATION_CHANGED')
    # Original qualified AF input validator has unchanged physical semantics.
    from abqjobpilot.execution.tensile_profile import validate_input
    require(validate_input(Path(plan['engineering']),reg)==plan['input_manifest'][0],'RECOVERY_INPUT_CHANGED')
    db=sqlite3.connect((Path(context.root)/'execution.sqlite3').as_uri()+'?mode=ro',uri=True,timeout=.2)
    try:
        db.execute('BEGIN')
        plans=db.execute('SELECT body FROM plans').fetchall()
        require(len(plans)==1 and json.loads(plans[0][0])==plan,'RECOVERY_PERSISTED_PLAN_CHANGED')
        meta=dict(db.execute('SELECT key,value FROM meta'))
        require(meta['context_digest']==context.context_digest and meta['owner_id']==owner['owner_id']
                and meta['supervisor_started']=='1','RECOVERY_NATIVE_META_CHANGED')
        counts={t:db.execute('SELECT COUNT(*) FROM '+t).fetchone()[0] for t in ('grants','runs','receipts','consumption','events','management_receipts','control_events','management_grants','management_consumption','reconciliations')}
        require(all(counts[t]==0 for t in ('runs','receipts','consumption','events','management_grants','management_consumption','reconciliations')),'RECOVERY_EXECUTION_OR_UNKNOWN_EXISTS')
        gate=db.execute('SELECT state,owner_id FROM dispatch_gate').fetchone();slot=db.execute('SELECT run_id FROM slot WHERE id=1').fetchone()[0]
        require(gate==('PAUSED',owner['owner_id']) and slot is None,'RECOVERY_GATE_OR_SLOT_CHANGED')
        rs=db.execute('SELECT namespace,key,request_digest,operation_id,body FROM management_receipts').fetchall()
        if not rs:
            require(counts['grants']==counts['control_events']==0,'RECOVERY_PARTIAL_NATIVE_WRITE')
            return dict(receipt=None,counts=counts,ready=ready)
        require(len(rs)==1 and counts['grants']==counts['control_events']==1,'RECOVERY_EXTRA_AUTHORIZATION')
        ns=canonical_json([context.project_instance_id,profile['client_namespace'],'product_standard_authorize'])
        fingerprint=digest(dict(action='authorize',owner_id=owner['owner_id'],operation_key=key,arguments=args))
        r=rs[0];receipt=json.loads(r[4])
        require(r[:3]==(ns,key,fingerprint) and r[3]==receipt['operation_id']
                and r[4]==canonical_json(receipt),'RECOVERY_NATIVE_RECEIPT_BINDING_CHANGED')
        require(db.execute('SELECT body FROM control_events').fetchone()[0]==canonical_json(receipt),'RECOVERY_CONTROL_EVENT_CHANGED')
        for k,want in dict(action='authorize',owner_id=owner['owner_id'],project_id=context.project_id,project_instance_id=context.project_instance_id,
                           plan_id=plan['plan_id'],plan_digest=plan['plan_digest'],operation_key=key,dispatch_state='PAUSED',
                           subject=args['subject'],source=args['source'],expires_at=args['expires_at'],scope_digest=digest(scope(plan))).items():
            require(receipt.get(k)==want,'RECOVERY_NATIVE_RECEIPT_SCOPE_CHANGED')
        gr=db.execute('SELECT grant_id,plan_id,body FROM grants').fetchone();grant=json.loads(gr[2])
        require(gr[:2]==(receipt['grant_id'],plan['plan_id']) and grant['grant_id']==receipt['grant_id']
                and grant['plan_id']==plan['plan_id'] and grant['plan_digest']==plan['plan_digest']
                and grant['project_id']==context.project_id and grant['project_instance_id']==context.project_instance_id
                and grant['context_digest']==context.context_digest and grant['product_scope']==scope(plan)
                and grant['approval_subject']==args['subject'] and grant['approval_source']==args['source']
                and grant['approval_owner']==owner['owner_id'] and grant['approval_operation']==receipt['operation_id']
                and grant['expires_at']==args['expires_at'] and grant['max_runs']==1
                and grant['resource_limits']==plan['resources'] and grant['output_key']==plan['output_key']
                and grant['allowed_action']==plan['action'] and grant['issuer']=='TrustedStandardOperator'
                and grant['grant_kind']=='REAL_FIXED_STANDARD' and grant['authority_instance']==meta['authority_instance'],
                'RECOVERY_NATIVE_GRANT_CHANGED')
        return dict(receipt=receipt,grant=grant,counts=counts,ready=ready)
    finally:db.close()

def recover(journal,*,wait_seconds=0,deadline=None):
    """Read only. Returning committed evidence cannot exercise Submit or Dispatch."""
    require(type(wait_seconds) in (int,float) and 0<=wait_seconds<=60,'RECOVERY_WAIT_BOUND')
    from main import safe
    journal=safe(journal)
    require(journal.is_dir(),'RECOVERY_JOURNAL_REQUIRED')
    if not (journal/'authorize-request.json').exists():
        require(not any((journal/n).exists() for n in ('authorize-send-intent.json','authorize-result.json')),'RECOVERY_REQUEST_MISSING')
        return dict(state='REQUEST_NOT_PERSISTED',confirmed_committed=False,executable_now=False,automatic_resume=False)
    ctx=packet_context(journal)
    from r3_bridge import trusted_af
    trusted_af()
    from abqjobpilot.service_lifecycle import ServiceLifecycleManager
    m=ServiceLifecycleManager(Path(ctx['packet']['af_project']))
    science=scientific_context(ctx)
    until=min(time.monotonic()+wait_seconds,deadline) if deadline is not None else time.monotonic()+wait_seconds
    while True:
        view=durable(ctx,m)
        if view['receipt'] is not None:break
        if ctx['old']==Path(__file__).resolve().parent and (journal/'authorize-local-state.json').is_file() and not (journal/'authorize-send-intent.json').exists():
            require(read(journal/'authorize-local-state.json')==dict(state='REQUEST_PERSISTED_NOT_SENT',operation_key=ctx['request']['operation_key']),
                    'RECOVERY_LOCAL_STATE_CHANGED')
            return dict(state='REQUEST_PERSISTED_NOT_SENT',operation_key=ctx['request']['operation_key'],confirmed_committed=False,
                        executable_now=False,automatic_resume=False,reason='New-version durable sequence stopped before send-intent; never resend from recovery')
        if time.monotonic()>=until:
            return dict(state='SENT_ACCEPTANCE_UNKNOWN',operation_key=ctx['request']['operation_key'],confirmed_committed=False,
                        executable_now=False,automatic_resume=False,reason='No committed receipt observed; never infer request was not sent')
        time.sleep(min(.2,max(0,until-time.monotonic())))
    # Require an authenticated native readback of the exact original key.
    client,context,health=m.connect()
    require(client.endpoint['owner_id']==ctx['owner']['owner_id'] and health['lifecycle_start_id']==ctx['owner']['start_id']
            and health['process']==view['ready']['process'],'RECOVERY_CONNECTED_OWNER_CHANGED')
    actual=client.management_receipt('product_standard_authorize',ctx['request']['operation_key'])
    require(actual==view['receipt'],'RECOVERY_IPC_RECEIPT_CHANGED')
    fresh=durable(ctx,m);require(fresh==view,'RECOVERY_NATIVE_STATE_CHANGED_DURING_READ')
    require(scientific_context(ctx)==science,'RECOVERY_SCIENTIFIC_STATE_CHANGED_DURING_WAIT')
    require(installation(ctx['packet'])==ctx['old'],'RECOVERY_INSTALLATION_CHANGED_DURING_WAIT')
    p=ctx['plan'];expires=min(p['expires_at'],actual['expires_at']);current=Path(__file__).resolve().parent==ctx['old']
    live=time.time()<expires and (deadline is None or time.monotonic()<deadline)
    received=(journal/'authorize-result.json').exists()
    if received:require(read(journal/'authorize-result.json').get('receipt')==actual,'RECOVERY_SAVED_RESPONSE_CHANGED')
    return dict(state='RECEIPT_RECEIVED' if received else 'COMMITTED_RESPONSE_RECOVERED',operation_key=ctx['request']['operation_key'],
                confirmed_committed=True,executable_now=bool(current and live),expired=not live,
                runtime_compatible_for_execution=current,historical_runtime_readonly=not current,
                expires_at=expires,receipt=actual,grant=view['grant'],counts=view['counts'],
                original_package_pin=ctx['packet']['installation']['gd_package_sha256'],
                packet_sha256=sha(journal/'confirmation-packet.json'),automatic_resume=False,submit_authorized_by_recovery=False,
                recovery_effects='READ_ONLY_NO_AUTHORIZE_SUBMIT_DISPATCH_OR_JOURNAL_WRITE')

def authorize_once(native,journal,args,owner,*,deadline,clock=time.monotonic):
    """One transmission; any recovery polls only the original management receipt."""
    import uuid
    key='authorize_'+uuid.uuid4().hex
    journal.put('authorize-request',dict(operation_key=key,arguments=args))
    journal.put('authorize-local-state',dict(state='REQUEST_PERSISTED_NOT_SENT',operation_key=key))
    require(clock()<deadline and time.time()<args['expires_at'],'PLAN_EXPIRED_BEFORE_AUTHORIZATION_SEND')
    journal.put('authorize-send-intent',dict(state='SENT_ACCEPTANCE_UNKNOWN',operation_key=key,
                                           meaning='May have been sent; this boundary never permits retransmission'))
    try:
        response=native.authorize(args,key,owner)
    except Exception as exc:
        journal.put('authorize-transport-unknown',dict(state='SENT_ACCEPTANCE_UNKNOWN',operation_key=key,error_type=type(exc).__name__,error=str(exc)))
        if not (isinstance(exc,OSError) or getattr(exc,'code',None) in ('ACCEPTANCE_UNKNOWN','COMMUNICATION_UNKNOWN')):raise
        recovered=recover(journal.root,wait_seconds=60,deadline=deadline)
        journal.put('authorize-recovery',recovered)
        require(recovered['confirmed_committed'],'AUTHORIZATION_UNKNOWN_READONLY_RECONCILE_ONLY')
        require(recovered['executable_now'],'AUTHORIZATION_COMMITTED_NOT_EXECUTABLE')
        response=dict(replayed=False,receipt=recovered['receipt'],response_source='READONLY_ORIGINAL_MANAGEMENT_RECEIPT',authorization_reissued=False)
    journal.put('authorize-result',response)
    # Receiving a JSON response alone does not replace exact persisted checks.
    verified=recover(journal.root,deadline=deadline)
    journal.put('authorize-confirmed',verified)
    require(verified['confirmed_committed'] and verified['executable_now'],'AUTHORIZATION_COMMITTED_NOT_EXECUTABLE')
    return response

def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--journal',required=True);p.add_argument('--package-pin',required=True);p.add_argument('--python-exe',required=True)
    a=p.parse_args();root=Path(__file__).resolve().parent
    sys.path[:0]=[str(root),str(root/'runtime')]
    from main import verify
    verify(root,a)
    from r3_bridge import trusted_af
    trusted_af()
    print(json.dumps(recover(a.journal),indent=2,allow_nan=False))

if __name__=='__main__':main()
