"""Explicit capability-bound unclean host-restart terminal; never a stop receipt.

No process control, Plan, Grant or ledger mutation. Same-account trusted local
operator scope; reference files are provenance, not cryptographic human signatures.
"""
import ctypes,hashlib,hmac,json,os,sqlite3,time,sys
from pathlib import Path
from .execution.models import require,digest,canonical_json,ExecutionError
from .service_discovery import read_document
from .local_credentials import read_private,private_value,host_binding

SCHEMA='af-cross-boot-terminal-v1'
ACTION='RECORD_HOST_RESTART_TERMINATED_UNCLEANLY'
STATE='HOST_RESTART_TERMINATED_UNCLEANLY'
NAME='cross-boot-terminal.json'
INTENT='cross-boot-terminal-intent.json'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def boot_observation():
    """Kernel boot FILETIME and machine binding; not wallclock-minus-uptime."""
    class Times(ctypes.Structure):
        _fields_=[('BootTime',ctypes.c_longlong),('CurrentTime',ctypes.c_longlong),('TimeZoneBias',ctypes.c_longlong),
                  ('CurrentTimeZoneId',ctypes.c_ulong),('Reserved',ctypes.c_ulong),('BootTimeBias',ctypes.c_ulonglong),('SleepTimeBias',ctypes.c_ulonglong)]
    value=Times();returned=ctypes.c_ulong()
    api=ctypes.WinDLL('ntdll');api.NtQuerySystemInformation.argtypes=[ctypes.c_int,ctypes.c_void_p,ctypes.c_ulong,ctypes.c_void_p]
    require(api.NtQuerySystemInformation(3,ctypes.byref(value),ctypes.sizeof(value),ctypes.byref(returned))==0,
            'BOOT_IDENTITY_UNKNOWN','Kernel boot time unavailable')
    require(0<value.BootTime<value.CurrentTime,'BOOT_IDENTITY_UNKNOWN','Invalid kernel boot boundary')
    import subprocess
    command="$ErrorActionPreference='Stop';Import-Module CimCmdlets; $b=(Get-CimInstance Win32_OperatingSystem).LastBootUpTime.ToUniversalTime().ToFileTimeUtc(); $e=Get-WinEvent -FilterHashtable @{LogName='System';ProviderName='Microsoft-Windows-Kernel-General';Id=12} -MaxEvents 1; $x=[xml]$e.ToXml(); $s=($x.Event.EventData.Data|Where-Object {$_.Name -eq 'StartTime'}).'#text'; @{cim=[string]$b;start=[string]([DateTime]::Parse($s).ToUniversalTime().ToFileTimeUtc());record=[string]$e.RecordId;provider=$e.ProviderName;event_id=$e.Id}|ConvertTo-Json -Compress"
    result=subprocess.run([r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe','-NoProfile','-NonInteractive','-Command',command],capture_output=True,text=True,timeout=20)
    require(result.returncode==0,'BOOT_IDENTITY_UNKNOWN','Independent CIM/Event12 boot observation unavailable')
    corroboration=json.loads(result.stdout)
    require(corroboration['provider']=='Microsoft-Windows-Kernel-General' and corroboration['event_id']==12
            and int(corroboration['cim'])==int(corroboration['start']) and abs(int(corroboration['cim'])-value.BootTime)<10000000,
            'BOOT_IDENTITY_UNKNOWN','Kernel, CIM and event boot boundaries disagree')
    return dict(source='Kernel+CIM+Kernel-General-12',boot_time_100ns=int(corroboration['cim']),host_binding=host_binding(),event_record=corroboration['record'])

def process_after_boot(identity,boot):
    """A current PID may be reused; no original exit code can be inferred."""
    from ctypes import wintypes as w
    require(set(identity)>={'pid','creation_time_100ns','image_path'} and 0<identity['creation_time_100ns']<boot['boot_time_100ns'],
            'PROCESS_NOT_PRIOR_BOOT','Original process must precede kernel boot')
    api=ctypes.WinDLL('kernel32',use_last_error=True)
    api.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];api.OpenProcess.restype=w.HANDLE
    api.CloseHandle.argtypes=[w.HANDLE];api.GetProcessTimes.argtypes=[w.HANDLE]+[ctypes.POINTER(w.FILETIME)]*4
    api.QueryFullProcessImageNameW.argtypes=[w.HANDLE,w.DWORD,w.LPWSTR,ctypes.POINTER(w.DWORD)]
    handle=api.OpenProcess(0x1000,False,identity['pid'])
    if not handle:
        require(ctypes.get_last_error()==87,'PROCESS_IDENTITY_UNKNOWN','Cannot inspect original numeric PID')
        return 'ABSENT_AFTER_CONFIRMED_HOST_BOOT'
    try:
        times=[w.FILETIME() for _ in range(4)]
        require(api.GetProcessTimes(handle,*[ctypes.byref(v) for v in times]),'PROCESS_IDENTITY_UNKNOWN','Cannot read creation time')
        created=(times[0].dwHighDateTime<<32)|times[0].dwLowDateTime
        size=w.DWORD(32768);image=ctypes.create_unicode_buffer(size.value)
        require(api.QueryFullProcessImageNameW(handle,0,image,ctypes.byref(size)),'PROCESS_IDENTITY_UNKNOWN','Cannot read reused PID image')
        require(created>=boot['boot_time_100ns'] and created!=identity['creation_time_100ns'],
                'PROCESS_IDENTITY_UNKNOWN','PID cannot be resolved to a distinct current-boot process')
        return 'PID_REUSED_BY_DISTINCT_CURRENT_BOOT_PROCESS'
    finally:api.CloseHandle(handle)

def reference(item):
    require(type(item) is dict and set(item)=={'path','sha256'},'EXACT_EVIDENCE_REFERENCE_REQUIRED','Reference path and digest required')
    from .execution.paths import local_path,no_reparse
    path=local_path(item['path']);no_reparse(path)
    require(path.is_absolute() and sha(path)==item['sha256'],'EVIDENCE_CHANGED','Evidence reference bytes changed')
    return item

def no_replacement(manager,identities,*,boot=None):
    """Check supported Python Owner startup path, not hostile same-user code."""
    import subprocess
    command="$ErrorActionPreference='Stop';Import-Module CimCmdlets; @(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\"|Select-Object ProcessId,ExecutablePath,CommandLine)|ConvertTo-Json -Compress"
    result=subprocess.run([r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe','-NoProfile','-NonInteractive','-Command',command],capture_output=True,text=True,timeout=20)
    require(result.returncode==0,'PROCESS_INVENTORY_UNKNOWN','Supported Owner process inventory unavailable')
    values=json.loads(result.stdout or '[]');values=values if isinstance(values,list) else [values]
    images={str(Path(v['image_path'])).casefold() for v in identities[:2]}
    targets={str(Path(manager.context.root)).casefold(),str(Path(manager.context.test_root)).casefold()}
    shell=ctypes.WinDLL('shell32');shell.CommandLineToArgvW.argtypes=[ctypes.c_wchar_p,ctypes.POINTER(ctypes.c_int)];shell.CommandLineToArgvW.restype=ctypes.POINTER(ctypes.c_wchar_p)
    kernel=ctypes.WinDLL('kernel32');kernel.LocalFree.argtypes=[ctypes.c_void_p]
    from .execution.ownership import current_process_identity
    own=current_process_identity()
    def arguments(text):
        n=ctypes.c_int();pointer=shell.CommandLineToArgvW(text,ctypes.byref(n))
        require(bool(pointer),'PROCESS_INVENTORY_UNKNOWN','Cannot parse supported process command line')
        try:return [pointer[i] for i in range(n.value)]
        finally:kernel.LocalFree(pointer)
    own_rows=[r for r in values if r['ProcessId']==own['pid']]
    require(len(own_rows)==1 and own_rows[0].get('CommandLine'),'COLLECTOR_IDENTITY_UNKNOWN','Collector command line unavailable')
    own_args=arguments(own_rows[0]['CommandLine'])
    from .execution.process_handles import ProcessReference
    from .execution.tensile_catalog import GD_ROOT
    archive=str(Path(GD_ROOT)/'cross_boot_archive.py')
    for row in values:
        require(row.get('ExecutablePath') and row.get('CommandLine'),'PROCESS_INVENTORY_UNKNOWN','Python process image/command line unreadable')
        if row['ProcessId']==own['pid']:
            require(str(Path(row['ExecutablePath'])).casefold()==str(Path(own['image_path'])).casefold(),'COLLECTOR_IDENTITY_UNKNOWN','Collector image mismatch')
            continue
        if str(Path(row['ExecutablePath'])).casefold() not in images:continue
        args=arguments(row['CommandLine'])
        if (row['ProcessId']==own['parent_pid'] and args[1:]==own_args[1:] and archive in args
                and str(Path(args[0])).casefold()==str(Path(row['ExecutablePath'])).casefold()==str(Path(sys.executable)).casefold()
                and str(Path(own_args[0])).casefold()==str(Path(own['image_path'])).casefold()):
            # Windows venv launcher is a transport for this exact archive CLI.
            # Never exempt a merely similar command or an arbitrary parent PID.
            boundary=boot if boot is not None else boot_observation()
            with_ref=ProcessReference(row['ProcessId'])
            try:
                identity=with_ref.identity
                require(str(Path(identity['image_path'])).casefold()==str(Path(row['ExecutablePath'])).casefold()
                        and boundary['boot_time_100ns']<=identity['creation_time_100ns']<=own['creation_time_100ns']
                        and with_ref.exit_evidence() is None,'COLLECTOR_IDENTITY_UNKNOWN','Collector transport identity unavailable')
            finally:with_ref.close()
            continue
        linked=any(a=='--project' and i+1<len(args) and str(Path(args[i+1])).casefold() in targets for i,a in enumerate(args))
        linked=linked or any(a=='--start-id' and i+1<len(args) and args[i+1]==manager._current()['start_id'] for i,a in enumerate(args))
        require(not linked,'REPLACEMENT_OWNER_UNKNOWN','Another process uses the exact supported instance/start path')
    return 'SUPPORTED_NATIVE_PYTHON_START_PATH_CHECKED_NOT_HOSTILE_SAME_USER_ISOLATION'

def snapshot(manager,identities,*,historical_boot=None):
    """Authoritative read-only empty instance state, current reservation and boot."""
    ctx=manager.context;profile=manager._profile();current=manager._current()
    require(current is not None,'START_ID_REQUIRED','No original lifecycle reservation')
    start=current['start_id'];base=manager._path(start)
    require(not (base/'stopped.json').exists(),'NORMAL_STOP_PRESENT','Unclean terminal cannot replace normal stop')
    ready=read_document(base/'ready.json');created=read_document(base/'created.json');intent=read_document(base/'intent.json')
    owner=read_document(Path(ctx.root)/'owner.json')
    connection=read_private(ctx,manager._path('connection.json'))
    require(current==intent and current['context_digest']==ctx.context_digest and current['profile_digest']==digest(profile)
            and ready['start_id']==created['start_id']==start and ready['owner_id']==owner['owner_id']
            and ready['process']==owner['process'],'LIFECYCLE_IDENTITY_CHANGED','Original ready/owner/start identity mismatch')
    require(connection['endpoint']==owner and connection['credential']==profile['credential'],
            'CONNECTION_IDENTITY_CHANGED','Native original connection/endpoint differs')
    require(len(identities) in (2,3) and len({v['pid'] for v in identities})==len(identities)
            and all(identities[0][k]==ready['process'][k] for k in identities[0])
            and identities[1]['pid']==created['transport_pid']==ready['process']['parent_pid'],
            'TRACKED_IDENTITY_CHANGED','Original worker/transport provenance required')
    if len(identities)==3:require(Path(identities[2]['image_path']).name.lower()=='conhost.exe','TRACKED_IDENTITY_CHANGED','Third tracked member is not conhost')
    boot=historical_boot if historical_boot is not None else boot_observation()
    require(boot['host_binding']==host_binding() and all(0<v['creation_time_100ns']<boot['boot_time_100ns'] for v in identities),
            'BOOT_IDENTITY_UNKNOWN','Original identities and authenticated host boot boundary differ')
    replacement='SUPPORTED_NATIVE_PYTHON_START_PATH_CHECKED_NOT_HOSTILE_SAME_USER_ISOLATION'
    if historical_boot is None:
        for value in identities:process_after_boot(value,boot)
        replacement=no_replacement(manager,identities,boot=boot)
    require(current['recorded_at']*10000000+116444736000000000<boot['boot_time_100ns'],
            'START_NOT_PRIOR_BOOT','Startup reservation not before host boot')
    require([p.name for p in manager.private.iterdir() if p.is_dir() and p.name.startswith('start_')]==[start],
            'EXTRA_START_UNKNOWN','Extra startup reservation cannot be silently closed')
    from .execution.lifecycle import require_idle
    db=sqlite3.connect(Path(ctx.root).joinpath('execution.sqlite3').as_uri()+'?mode=ro',uri=True)
    try:
        db.execute('BEGIN')
        names=('plans','grants','runs','receipts','consumption','events','management_receipts','control_events','management_grants','management_consumption','reconciliations','observations','validations')
        counts={n:db.execute('SELECT count(*) FROM '+n).fetchone()[0] for n in names}
        require(counts=={n:int(n=='plans') for n in names},'EXECUTION_OR_MANAGEMENT_UNKNOWN','Nonempty execution or management state')
        plan=json.loads(db.execute('SELECT body FROM plans').fetchone()[0]);unsigned=dict(plan)
        require(unsigned.pop('plan_digest')==digest(unsigned),'PLAN_CHANGED','Original Plan digest mismatch')
        extension=profile['standard_extension'];require_idle(db,standard_binding=extension['binding'])
        require(plan['plan_id']==extension['binding']['plan_id'] and plan['plan_digest']==extension['binding']['plan_digest']
                and (historical_boot is not None or plan['expires_at']<=time.time()),'PLAN_CHANGED','Original exact expired Plan required')
        meta=dict(db.execute('SELECT key,value FROM meta'))
        require(db.execute('SELECT state,owner_id FROM dispatch_gate WHERE id=1').fetchone()==('PAUSED',owner['owner_id'])
                and meta['supervisor_started']=='1' and meta['authority_instance']==profile['authority_instance'],'OWNER_STATE_CHANGED','Expected prior started PAUSED Owner')
        from .execution.product_standard import scope
        scope_digest=digest(scope(plan))
    finally:db.close()
    engineering=Path(plan['engineering'])
    require({p.name for p in engineering.iterdir()}=={plan['job_name']+'.inp','scratch'} and not list((engineering/'scratch').iterdir()),
            'OUTPUT_OR_START_INTENT_FOUND','Unexpected solver output or intent')
    require(not any(p.name.endswith('.intent.json') for p in Path(ctx.root).rglob('*')),'START_INTENT_FOUND','Execution intent found')
    paths=[base/n for n in ('intent.json','created.json','ready.json','claimed.json','host.json')]+[manager._path('lifecycle-current.json'),manager._path('connection.json'),Path(ctx.root)/'owner.json',Path(ctx.root)/'execution.sqlite3']
    return dict(project_id=ctx.project_id,project_instance_id=ctx.project_instance_id,context_digest=ctx.context_digest,
        owner_id=owner['owner_id'],start_id=start,plan_id=plan['plan_id'],plan_digest=plan['plan_digest'],scope_digest=scope_digest,
        boot=boot,identities=identities,counts=counts,files={str(p):sha(p) for p in paths},
        process_state='ORIGINAL_IDENTITIES_PRECEDE_CONFIRMED_BOOT',replacement_scope=replacement,exit_codes='UNKNOWN',normal_stop=False,execution_authorized=False)

def proposal(manager,identities,evidence_references,operation_id,*,check_scientific_guard=True,historical_boot=None):
    require(type(operation_id) is str and len(operation_id)==32 and all(c in '0123456789abcdef' for c in operation_id),'EXACT_OPERATION_REQUIRED','32 hex operation ID required')
    require(evidence_references and all(reference(v) for v in evidence_references),'EVIDENCE_REQUIRED','Original tracked identity and independent reconciliation references required')
    view=snapshot(manager,identities,historical_boot=historical_boot)
    review=read_document(evidence_references[0]['path'])
    require(review['schema']=='cross-boot-independent-review-v1' and review['unresolved_native_operation'] is False
            and review['scope']=='KNOWN_BOUND_SOURCES_RECONCILED' and review['process_identities']==identities
            and all(review[k]==view[k] for k in ('project_id','project_instance_id','owner_id','start_id','plan_id')),
            'INDEPENDENT_RECONCILIATION_REQUIRED','Exact independent known-source reconciliation required')
    require(review['known_operator_journals'],'INDEPENDENT_RECONCILIATION_REQUIRED','Known helper sources required')
    for journal in review['known_operator_journals']:
        root=Path(journal['root'])
        require(root.is_absolute() and root.is_dir() and journal['request_exists'] is False,'PENDING_STOP_UNKNOWN','Unknown helper state')
        actual={str(p.relative_to(root)):sha(p) for p in root.rglob('*') if p.is_file()}
        require(len(actual)<=128 and actual==journal['files'],'PENDING_STOP_UNKNOWN','Helper journal changed after reconciliation')
    guards=review['scientific_commit_guard']
    require(type(guards) is dict and guards and any(Path(p).name=='workflow.sqlite' for p in guards),
            'SCIENTIFIC_STATE_GUARD_REQUIRED','Exact original scientific state hashes required')
    if check_scientific_guard:
        for path,pin in guards.items():reference(dict(path=path,sha256=pin))
    view['independent_review_digest']=evidence_references[0]['sha256']
    view['scientific_state_at_commit']=guards
    return dict(schema=SCHEMA,action=ACTION,operation_id=operation_id,state=STATE,scope=view,evidence_references=evidence_references,
                implementation={str(Path(__file__).resolve()):sha(Path(__file__)),str(Path(__file__).with_name('service_lifecycle.py').resolve()):sha(Path(__file__).with_name('service_lifecycle.py')),
                                str(Path(__file__).parent/'execution/tensile_catalog.py'):sha(Path(__file__).parent/'execution/tensile_catalog.py')},
                target_path=str(manager._path(view['start_id']+'/'+NAME)),execution_authorized=False,budget_changed=False)

def _mac(token,value):
    return hmac.new(token.encode(),canonical_json(value).encode(),hashlib.sha256).hexdigest()

def read_terminal(manager):
    current=manager._current()
    if not current:return None
    path=manager._path(current['start_id']+'/'+NAME)
    if not path.exists():return None
    token=manager._operator();value=read_private(manager.context,path)
    require(set(value)=={'record','operator_mac'} and hmac.compare_digest(value['operator_mac'],_mac(token,value['record'])),
            'TERMINAL_IDENTITY_CHANGED','Native capability-bound terminal seal mismatch')
    record=value['record'];p=record['proposal'];view=p['scope']
    require(p['schema']==SCHEMA and p['action']==ACTION and p['state']==STATE and p['execution_authorized'] is False
            and p['budget_changed'] is False and p['target_path']==str(path) and view['start_id']==current['start_id']
            and record['proposal_digest']==digest(p),'TERMINAL_IDENTITY_CHANGED','Terminal proposal identity mismatch')
    for ref in p['evidence_references']+[record['authorization_reference']]:reference(ref)
    actual=proposal(manager,view['identities'],p['evidence_references'],p['operation_id'],check_scientific_guard=False,historical_boot=view['boot'])
    require(actual==p,'TERMINAL_STATE_CHANGED','Native historical state, known journals or boot changed')
    intent=read_private(manager.context,manager._path(current['start_id']+'/'+INTENT))
    require(intent['proposal_digest']==record['proposal_digest'] and intent['operation_id']==p['operation_id']
            and intent['authorization_reference']==record['authorization_reference'],'TERMINAL_INTENT_CHANGED','Original terminal intent differs')
    return dict(state=STATE,normal_stop=False,exit_codes='UNKNOWN',path=str(path),sha256=sha(path),record=record)

def commit(manager,p,proposal_digest,authorization_reference):
    """Explicit trusted-local capability invocation after separate exact approval."""
    require(digest(p)==proposal_digest,'PROPOSAL_CHANGED','Exact proposal digest required')
    reference(authorization_reference)
    approval=read_document(authorization_reference['path'])
    require(approval['schema']=='cross-boot-exact-authorization-reference-v1' and approval['action']==ACTION
            and approval['proposal_digest']==proposal_digest and approval['operation_id']==p['operation_id']
            and approval['new_execution_authorized'] is False and approval['budget_change_authorized'] is False
            and type(approval['expires_at']) is int and time.time()<approval['expires_at']<=time.time()+600,
            'EXACT_AUTHORIZATION_REQUIRED','Exact bounded archival authorization reference required; native capability still mandatory')
    from .execution.ownership import LocalOwnerLock
    from .service_lifecycle import write_new
    token=manager._operator();lease=LocalOwnerLock(manager.context)
    try:
        prior=read_terminal(manager)
        if prior:
            require(prior['record']['proposal_digest']==proposal_digest and prior['record']['authorization_reference']==authorization_reference,
                    'IDEMPOTENCY_CONFLICT','Another terminal scope already committed')
            return dict(replayed=True,terminal=prior)
        actual=proposal(manager,p['scope']['identities'],p['evidence_references'],p['operation_id'])
        require(actual==p,'PROPOSAL_CHANGED','Native state changed after review')
        path=manager._path(p['scope']['start_id']+'/'+INTENT)
        require(not path.exists(),'TERMINAL_INTENT_UNKNOWN','Existing intent permits read-only reconciliation only')
        write_new(path,private_value(manager.context,dict(proposal_digest=proposal_digest,operation_id=p['operation_id'],authorization_reference=authorization_reference)))
        manager._checkpoint('cross_boot_intent_persisted')
        require(proposal(manager,p['scope']['identities'],p['evidence_references'],p['operation_id'])==p,'TERMINAL_STATE_CHANGED','State changed before terminal publication')
        record=dict(proposal=p,proposal_digest=proposal_digest,authorization_reference=authorization_reference,recorded_at=int(time.time()),
                    source='explicit_lifecycle_operator_capability',statement='Unclean host-restart termination; no orderly stop or process exit code')
        write_new(Path(p['target_path']),private_value(manager.context,dict(record=record,operator_mac=_mac(token,record))))
        return dict(replayed=False,terminal=read_terminal(manager))
    finally:lease.close()
