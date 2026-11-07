"""Versioned historical normal-stop evidence; PID reuse is not original-process survival."""
import ctypes,json,sqlite3,time
from pathlib import Path
import continuation as c

def closed_window(project,expected,reference):
    """Either proven never-started or a fully reviewed orderly stopped window.

    A reboot/no PID/START_UNCONFIRMED is neither condition.
    """
    from r3_bridge import trusted_af
    trusted_af()
    from abqjobpilot.service_lifecycle import ServiceLifecycleManager
    m=ServiceLifecycleManager(c.local(project))
    if m._current():
        if reference.get('schema')=='af-cross-boot-terminal-reference-v1':return cross_boot_window(m,expected,reference)
        return stopped_window(project,expected,reference,review_kind='B')
    from abqjobpilot.execution.models import canonical_json,digest
    from abqjobpilot.execution.product_standard import ProductStandardControl,scope
    from abqjobpilot.execution.standard_contract import StandardConfig
    from abqjobpilot.execution.lifecycle import require_idle
    from abqjobpilot.execution.tensile_profile import validate_input
    from abqjobpilot.local_credentials import read_private
    profile=m._profile();ext=profile['standard_extension'];ctx=m.context
    db=sqlite3.connect((Path(ctx.root)/'execution.sqlite3').as_uri()+'?mode=ro',uri=True)
    try:
        db.execute('BEGIN')
        tables=('plans','grants','runs','receipts','consumption','events','management_receipts','control_events','management_grants','management_consumption','reconciliations','observations','validations')
        counts={t:db.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in tables}
        c.require(counts=={t:int(t=='plans') for t in tables},'ANCESTOR_NOT_UNEXECUTED')
        plan=json.loads(db.execute('SELECT body FROM plans').fetchone()[0]);unsigned=dict(plan)
        c.require(unsigned.pop('plan_digest')==digest(unsigned),'ANCESTOR_PLAN_CHANGED')
        require_idle(db,standard_binding=ext['binding'])
        c.require(dict(db.execute('SELECT key,value FROM meta'))['supervisor_started']=='0','ANCESTOR_OWNER_UNKNOWN')
    finally:db.close()
    config=StandardConfig(canonical_json(ext['standard_config']));config.verify()
    ProductStandardControl(ext['binding']).check_plan(plan)
    c.require(plan['runtime_binding']==config.value() and plan['expires_at']<=time.time(),'ANCESTOR_RUNTIME_OR_EXPIRY')
    reg=read_private(ctx,m._path('tensile-registration.json'))
    c.require(reg==plan['registration'] and reg['context_digest']==ctx.context_digest,'ANCESTOR_REGISTRATION')
    c.require(validate_input(Path(plan['engineering']),reg)==plan['input_manifest'][0],'ANCESTOR_INPUT')
    view=dict(plan=plan,scope_digest=digest(scope(plan)),af_project=str(c.local(project)),project_id=ctx.project_id,project_instance_id=ctx.project_instance_id)
    c.require(c.identity(view)==expected,'ANCESTOR_IDENTITY')
    eng=Path(plan['engineering'])
    c.require({p.name for p in eng.iterdir()}=={plan['job_name']+'.inp','scratch'} and not list((eng/'scratch').iterdir()),'ANCESTOR_OUTPUT_UNKNOWN')
    c.require(not any(p.name.startswith('start_') or p.name.endswith('.intent.json') for p in Path(ctx.test_root).rglob('*')),'ANCESTOR_START_INTENT')
    return dict(identity=expected,lifecycle='NEVER_STARTED',counts=counts),m

def cross_boot_window(manager,expected,reference):
    """Only AF's sealed authoritative abnormal terminal qualifies this branch."""
    from abqjobpilot.cross_boot_terminal import read_terminal,STATE,no_replacement
    from abqjobpilot.execution.models import canonical_json,digest
    from abqjobpilot.execution.standard_contract import StandardConfig
    from abqjobpilot.execution.product_standard import scope
    from abqjobpilot.execution.tensile_profile import validate_input
    from abqjobpilot.local_credentials import read_private
    c.require(set(reference)=={'schema','path','sha256'},'EXACT_NATIVE_TERMINAL_REFERENCE_REQUIRED')
    native=read_terminal(manager)
    c.require(native and native['path']==reference['path'] and native['sha256']==reference['sha256']
              and native['state']==STATE and native['normal_stop'] is False,'NATIVE_CROSS_BOOT_TERMINAL_REQUIRED')
    no_replacement(manager,native['record']['proposal']['scope']['identities'])
    ctx=manager.context;profile=manager._profile();ext=profile['standard_extension']
    db=sqlite3.connect((Path(ctx.root)/'execution.sqlite3').as_uri()+'?mode=ro',uri=True)
    try:plan=json.loads(db.execute('SELECT body FROM plans').fetchone()[0])
    finally:db.close()
    config=StandardConfig(canonical_json(ext['standard_config']));config.verify()
    c.require(plan['runtime_binding']==config.value(),'PARENT_RUNTIME_CHANGED')
    reg=read_private(ctx,manager._path('tensile-registration.json'))
    c.require(reg==plan['registration'] and validate_input(Path(plan['engineering']),reg)==plan['input_manifest'][0],'PARENT_INPUT_CHANGED')
    view=dict(plan=plan,scope_digest=digest(scope(plan)),af_project=str(Path(ctx.root).parent),project_id=ctx.project_id,project_instance_id=ctx.project_instance_id)
    c.require(c.identity(view)==expected,'PARENT_IDENTITY_CHANGED')
    return dict(identity=expected,lifecycle=STATE,normal_stop=False,exit_codes='UNKNOWN',native_terminal=reference,proof=native['record']),manager

def original_process_exited(identity):
    """Retained exit is primary evidence. A reused PID identifies another process.

    Access denial/ambiguous identity rejects. Never opens TERMINATE permissions.
    """
    from ctypes import wintypes as w
    api=ctypes.WinDLL('kernel32',use_last_error=True)
    api.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];api.OpenProcess.restype=w.HANDLE
    api.CloseHandle.argtypes=[w.HANDLE]
    api.GetProcessTimes.argtypes=[w.HANDLE]+[ctypes.POINTER(w.FILETIME)]*4
    api.QueryFullProcessImageNameW.argtypes=[w.HANDLE,w.DWORD,w.LPWSTR,ctypes.POINTER(w.DWORD)]
    api.WaitForSingleObject.argtypes=[w.HANDLE,w.DWORD];api.WaitForSingleObject.restype=w.DWORD
    h=api.OpenProcess(0x100000|0x1000,False,identity['pid'])
    if not h:
        c.require(ctypes.get_last_error()==87,'PROCESS_IDENTITY_UNKNOWN');return 'ABSENT_WITH_PRIOR_RETAINED_EXIT'
    try:
        a,b,d,e=[w.FILETIME() for _ in range(4)]
        c.require(api.GetProcessTimes(h,*[ctypes.byref(v) for v in (a,b,d,e)]),'PROCESS_TIMES_UNKNOWN')
        created=(a.dwHighDateTime<<32)|a.dwLowDateTime
        # Windows may no longer expose the image of an already exited process.
        # Exact creation + signaled handle and prior retained image/exit proof
        # suffice; this is not a PID-absence inference.
        if created==identity['creation_time_100ns'] and api.WaitForSingleObject(h,0)==0:
            return 'ORIGINAL_PROCESS_SIGNALED_WITH_PRIOR_RETAINED_IDENTITY'
        size=w.DWORD(32768);buf=ctypes.create_unicode_buffer(size.value)
        c.require(api.QueryFullProcessImageNameW(h,0,buf,ctypes.byref(size)),'PROCESS_IMAGE_UNKNOWN')
        if created!=identity['creation_time_100ns']:
            return 'PID_REUSED_DISTINCT_CREATION_AND_OBSERVED_IMAGE'
        c.require(str(Path(buf.value)).casefold()==str(Path(identity['image_path'])).casefold(),'ORIGINAL_PROCESS_IMAGE_CHANGED')
        c.require(api.WaitForSingleObject(h,0)==0,'ORIGINAL_PROCESS_STILL_LIVE')
        return 'ORIGINAL_PROCESS_SIGNALED'
    finally:api.CloseHandle(h)


def qualification(ref,receipt,expected,ready,created,*,review_kind="A"):
    c.require(type(ref) is dict and set(ref)=={'schema','pre_call','final','review','index'} and ref['schema']=='retained-stop-review-reference-v1','RETAINED_EXIT_REVIEW_REQUIRED')
    raw={}
    for key in ('pre_call','final','review','index'):
        item=ref[key];c.require(set(item)=={'path','sha256'} and Path(item['path']).is_absolute(),'EXACT_REVIEW_REFERENCE_REQUIRED')
        path=c.local(item['path'])
        with path.open('rb') as f:data=f.read((2<<20)+1)
        c.require(len(data)<=2<<20 and c.case.hashbytes(data)==item['sha256'],'REVIEW_SOURCE_CHANGED')
        raw[key]=data
    before=json.loads(raw['pre_call']);after=json.loads(raw['final']);index=json.loads(raw['index']);review=raw['review'].decode('utf8')
    for key in ('pre_call','final'):
        c.require(index[ref[key]['path']]['sha256']==ref[key]['sha256'],'REVIEW_INDEX_MISMATCH')
    c.require(review_kind in ('A','B'),'REVIEW_KIND_REQUIRED')
    if review_kind=='A':
        c.require('PASS_LIMITED_NATIVE_IDLE_STOP_AND_RETAINED_HANDLE_EXIT' in review
                  and all(value in review for value in (receipt['owner_id'],receipt['start_id'],expected['project_id'],expected['project_instance_id'],expected['plan_id'],expected['plan_digest'])),'INDEPENDENT_REVIEW_SCOPE_MISMATCH')
    else:
        verified=json.loads(raw['review'])
        c.require(verified['verdict']=='PASS_B_NATIVE_IDLE_STOP_AND_THREE_RETAINED_EXITS'
                  and verified['receipt']==receipt and verified['exits']==after['process_exits']
                  and verified['B_preparation']==before['research']['binding']
                  and verified['A_result_sha256']==before['research']['A_result_sha256']
                  and verified['research_sha256']==before['research']['workflow_sha256']
                  and verified['budget']==before['research']['budget']==dict(limit=2,held=1,charged=1,available=0)
                  and verified['B_solver_execution_count']==0 and verified['native_stop_count']==1,
                  'INDEPENDENT_B_REVIEW_SCOPE_MISMATCH')
    c.require(before['owner']==receipt['owner_id'] and before['start']==receipt['start_id']
              and before['project_id']==expected['project_id'] and before['instance']==expected['project_instance_id']
              and after['receipt']==receipt and after['orderly_stop']==dict(state='NOT_RUNNING',reason='ORDERLY_STOP_RECORDED')
              and after['status']=='NATIVE_IDLE_STOP_RECORDED_EXIT_OBSERVED' and after['solver_started'] is False
              and after['budget_changed'] is False and before['research']==after['research'],'EXIT_REVIEW_SCOPE_MISMATCH')
    for key in ('plan_id','plan_digest','scope_digest'):
        c.require(before['store'][key]==after['store'][key]==expected[key],'EXIT_REVIEW_PLAN_MISMATCH')
    identities=before['processes'];exits=after['process_exits']
    c.require(len(identities)==len(exits)==3 and len({p['pid'] for p in identities})==3,'EXACT_THREE_RETAINED_MEMBERS_REQUIRED')
    for ident,exit in zip(identities,exits):
        c.require(set(ident)=={'pid','creation_time_100ns','image_path'} and ident['creation_time_100ns']>0
                  and all(exit[k]==v for k,v in ident.items()) and exit['exit_source']=='retained_windows_handle'
                  and exit['exit_code']==0,'RETAINED_EXIT_IDENTITY_MISMATCH')
    c.require(all(identities[0][k]==ready['process'][k] for k in identities[0]) and identities[1]['pid']==created['transport_pid']
              and Path(identities[2]['image_path']).name.lower()=='conhost.exe','RETAINED_TREE_SOURCE_MISMATCH')
    for ident in identities:original_process_exited(ident)
    return dict(reference=ref,identities=identities,exits=exits,scope='Only three independently reviewed retained members; no claim for arbitrary descendants')

def stopped_window(project,expected,review_reference,*,review_kind="A"):
    """Native stopped evidence, zero execution, old runtime and immutable Plan.

    No Owner call, no repair, no writes; lifecycle marker alone is insufficient.
    """
    from r3_bridge import trusted_af
    trusted_af()
    from abqjobpilot.service_lifecycle import ServiceLifecycleManager
    from abqjobpilot.execution.models import digest,canonical_json
    from abqjobpilot.execution.product_standard import ProductStandardControl,scope
    from abqjobpilot.execution.standard_contract import StandardConfig
    from abqjobpilot.local_credentials import read_private
    from abqjobpilot.execution.lifecycle import STOP,require_idle
    from abqjobpilot.execution.tensile_profile import validate_input
    m=ServiceLifecycleManager(c.local(project));ctx=m.context;profile=m._profile();ext=profile['standard_extension']
    current=m._current();stopped=m._stopped(current)
    c.require(current and stopped,'ORDERLY_STOP_REQUIRED')
    start=current['start_id'];base=m._path(start)
    load=lambda name:json.loads(c.local(base/name).read_bytes())
    intent=load('intent.json');created=load('created.json');ready=load('ready.json');owner=json.loads(c.local(Path(ctx.root)/'owner.json').read_bytes())
    receipt=stopped['receipt']
    c.require(intent['start_id']==created['start_id']==ready['start_id']==receipt['start_id']==start
              and intent['context_digest']==ctx.context_digest and current['profile_digest']==digest(profile)
              and ready['owner_id']==owner['owner_id']==receipt['owner_id']
              and receipt['project_instance_id']==ctx.project_instance_id and receipt['action']==STOP
              and receipt['state']=='STOP_COMMITTED' and receipt['source']=='explicit_lifecycle_operator_capability'
              and receipt['effects']==['PAUSED','orderly_idle_stop'],'STOP_IDENTITY_CHANGED')
    db=sqlite3.connect(c.local(Path(ctx.root)/'execution.sqlite3').as_uri()+'?mode=ro',uri=True)
    try:
        db.execute('BEGIN')
        counts={t:db.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in
                ('plans','grants','runs','receipts','consumption','events','management_receipts','control_events','management_grants','management_consumption','reconciliations','observations','validations')}
        c.require(counts==dict(plans=1,grants=0,runs=0,receipts=0,consumption=0,events=0,management_receipts=1,control_events=1,management_grants=0,management_consumption=0,reconciliations=0,observations=0,validations=0),'EXECUTION_OR_EXTRA_MANAGEMENT_EVIDENCE')
        plan=json.loads(db.execute('SELECT body FROM plans').fetchone()[0]);unsigned=dict(plan)
        c.require(unsigned.pop('plan_digest')==digest(unsigned),'PLAN_DIGEST_CHANGED')
        ProductStandardControl(ext['binding']).check_plan(plan)
        require_idle(db,standard_binding=ext['binding'])
        c.require(dict(db.execute('SELECT key,value FROM meta'))['supervisor_started']=='1'
                  and db.execute('SELECT state,owner_id FROM dispatch_gate').fetchone()==('PAUSED',receipt['owner_id']),'STOP_STATE_CHANGED')
        ns=canonical_json([ctx.project_instance_id,profile['client_namespace'],STOP])
        record=db.execute('SELECT namespace,key,request_digest,operation_id,body FROM management_receipts').fetchone()
        fp=digest(dict(owner_id=receipt['owner_id'],start_id=start,action=STOP,key=receipt['operation_key']))
        c.require(record==(ns,receipt['operation_key'],fp,receipt['operation_id'],canonical_json(receipt))
                  and db.execute('SELECT body FROM control_events').fetchone()[0]==canonical_json(receipt),'STOP_RECEIPT_OR_CONTROL_CHANGED')
    finally:db.close()
    config=StandardConfig(canonical_json(ext['standard_config']));config.verify()
    c.require(plan['runtime_binding']==config.value() and plan['expires_at']<=time.time(),'PARENT_RUNTIME_OR_EXPIRY_CHANGED')
    reg=read_private(ctx,m._path('tensile-registration.json'))
    c.require(reg==plan['registration'] and reg['context_digest']==ctx.context_digest
              and (reg['project_id'],reg['project_instance_id'])==(ctx.project_id,ctx.project_instance_id),'PARENT_REGISTRATION_CHANGED')
    c.require(validate_input(Path(plan['engineering']),reg)==plan['input_manifest'][0],'PARENT_INPUT_CHANGED')
    view=dict(plan=plan,scope_digest=digest(scope(plan)),af_project=str(c.local(project)),project_id=ctx.project_id,project_instance_id=ctx.project_instance_id)
    c.require(c.identity(view)==expected,'PARENT_IDENTITY_CHANGED')
    eng=Path(plan['engineering']);c.require({p.name for p in eng.iterdir()}=={plan['job_name']+'.inp','scratch'} and not list((eng/'scratch').iterdir()),'OUTPUT_OR_SOLVER_INTENT_FOUND')
    # Exactly one original native startup, no unexplained later intent.
    c.require([p.name for p in m.private.iterdir() if p.is_dir() and p.name.startswith('start_')]==[start],'EXTRA_OWNER_START_OR_UNKNOWN')
    for p in Path(ctx.root).rglob('*'):
        c.local(p)
        c.require(not p.name.endswith('.intent.json'),'SOLVER_INTENT_FOUND')
    if review_reference.get('schema')=='execution-window-stop-reference-v1':
        from window_closure import qualification as machine_qualification
        review=machine_qualification(review_reference,receipt,expected,ready,created,m)
    else:review=qualification(review_reference,receipt,expected,ready,created,review_kind=review_kind)
    proof=dict(start_id=start,owner_id=receipt['owner_id'],receipt=receipt,process=ready['process'],transport_pid=created['transport_pid'],
               files={str(p.relative_to(c.local(project))):c.sha(p) for p in sorted([base/n for n in
                    ('intent.json','created.json','ready.json','stopped.json','claimed.json','host.json')]+[m._path('lifecycle-current.json'),Path(ctx.root)/'owner.json'])},counts=counts,retained_exit_review=review)
    return dict(identity=c.identity(view),lifecycle='ORDERLY_STOP_RECORDED',proof=proof),m
