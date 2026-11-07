"""Machine evidence for this profile's newly created Owner, not human attestation.

Only native worker/transport members evidenced by the authenticated health and
created record are tracked. No descendant-completeness or conhost claim.
"""
import json,time
from pathlib import Path
import continuation as c
SCHEMA='execution-window-stop-reference-v1'

def load(path):
    path=c.local(path)
    with path.open('rb') as stream:raw=stream.read((2<<20)+1)
    c.require(len(raw)<=2<<20,'CLOSURE_DOCUMENT_LIMIT')
    return json.loads(raw)

class TrackedOwner:
    def __init__(self,manager,health,owner):
        from abqjobpilot.execution.process_handles import ProcessReference
        self.manager=manager;self.refs=[];self.owner=owner;self.health=health
        current=manager._current();start=owner['start_id']
        c.require(current and current['start_id']==start and health['lifecycle_start_id']==start,'TRACKED_START_CHANGED')
        ready=load(manager._path(start+'/ready.json'));created=load(manager._path(start+'/created.json'))
        c.require(ready['start_id']==created['start_id']==start and ready['owner_id']==owner['owner_id']
            and ready['process']==health['process'],'AUTHENTICATED_READY_IDENTITY_REQUIRED')
        self.ready=ready;self.created=created
        try:
            self.refs.append(ProcessReference(health['process']['pid'],health['process']))
            if created['transport_pid']!=health['process']['pid']:
                c.require(health['process']['parent_pid']==created['transport_pid'],'TRANSPORT_PARENT_CHANGED')
                self.refs.append(ProcessReference(created['transport_pid']))
                c.require(self.refs[1].identity['creation_time_100ns']<=self.refs[0].identity['creation_time_100ns']
                    and Path(self.refs[1].identity['image_path']).name.lower()=='python.exe','TRANSPORT_IDENTITY_UNKNOWN')
            self.verify(health,owner)
        except BaseException:self.close();raise

    def verify(self,health,owner):
        c.require(owner['owner_id']==self.owner['owner_id'] and owner['start_id']==self.owner['start_id']
            and health['lifecycle_start_id']==self.owner['start_id'] and health['process']==self.health['process'], 'RETAINED_OWNER_CHANGED')
        c.require(all(ref.exit_evidence() is None for ref in self.refs),'RETAINED_OWNER_ALREADY_EXITED')

    def exit_record(self,owner,stop):
        receipt=stop['receipt']
        c.require(receipt['owner_id']==self.owner['owner_id']==owner['owner_id'] and receipt['start_id']==self.owner['start_id']==owner['start_id']
            and receipt['state']=='STOP_COMMITTED' and stop.get('replayed') is not True,'EXACT_NATIVE_STOP_REQUIRED')
        deadline=time.monotonic()+10
        while time.monotonic()<deadline and any(ref.exit_evidence() is None for ref in self.refs):time.sleep(.05)
        exits=[ref.exit_evidence() for ref in self.refs]
        c.require(all(e and e['exit_code']==0 and e['exit_source']=='retained_windows_handle' for e in exits),'TRACKED_EXIT_UNKNOWN_NO_RETRY')
        marker=self.manager._stopped(self.manager._current())
        c.require(marker and marker['receipt']==receipt,'NATIVE_STOP_MARKER_REQUIRED')
        return dict(classification='MACHINE_EVIDENCE_NOT_INDEPENDENT_HUMAN_APPROVAL',receipt=receipt,
            identities=[r.identity for r in self.refs],exits=exits,
            member_scope='Authenticated native worker and recorded transport only',unexecuted_readmission_qualification=False)

    def record(self,plan,owner,stop,journal_root,camp):
        from abqjobpilot.local_credentials import private_value
        from abqjobpilot.service_lifecycle import write_new
        c.require('execution_window' in plan['registration'],'NEW_WINDOW_CLOSURE_ONLY')
        receipt=stop['receipt']
        c.require(receipt['owner_id']==self.owner['owner_id']==owner['owner_id'] and receipt['start_id']==self.owner['start_id']==owner['start_id']
            and receipt['state']=='STOP_COMMITTED' and stop.get('replayed') is not True,'EXACT_NATIVE_STOP_REQUIRED')
        deadline=time.monotonic()+10
        while time.monotonic()<deadline and any(ref.exit_evidence() is None for ref in self.refs):time.sleep(.05)
        exits=[ref.exit_evidence() for ref in self.refs]
        c.require(all(e and e['exit_code']==0 and e['exit_source']=='retained_windows_handle' for e in exits),'TRACKED_EXIT_UNKNOWN_NO_RETRY')
        marker=self.manager._stopped(self.manager._current())
        c.require(marker and marker['receipt']==receipt,'NATIVE_STOP_MARKER_REQUIRED')
        budget=camp.counts(camp.verified_rows())
        c.require(budget==dict(limit=2,held=1,charged=1,available=0),'BUDGET_CHANGED_DURING_CLEANUP')
        from abqjobpilot.execution.product_standard import scope
        from abqjobpilot.execution.models import digest
        payload=dict(schema=SCHEMA,classification='MACHINE_EVIDENCE_NOT_INDEPENDENT_HUMAN_APPROVAL',
            project_id=self.manager.context.project_id,project_instance_id=self.manager.context.project_instance_id,
            context_digest=self.manager.context.context_digest,plan_id=plan['plan_id'],plan_digest=plan['plan_digest'],scope_digest=digest(scope(plan)),
            execution_window=plan['registration']['execution_window'],research_project=camp.c['project'],contract=camp.pin,budget=budget,
            receipt=receipt,ready=self.ready,created=self.created,identities=[r.identity for r in self.refs],exits=exits,
            member_scope='Authenticated native worker and its recorded Python transport only; no arbitrary descendants')
        path=c.local(Path(journal_root)/'native-window-closure.json')
        write_new(path,private_value(self.manager.context,payload))
        return dict(schema=SCHEMA,path=str(path),sha256=c.sha(path))

    def close(self):
        for ref in self.refs:ref.close()
        self.refs=[]

def qualification(ref,receipt,expected,ready,created,manager):
    """Deterministic gate for new-schema evidence; historical 3-member rule stays."""
    from abqjobpilot.local_credentials import read_private
    c.require(type(ref) is dict and set(ref)=={'schema','path','sha256'} and ref['schema']==SCHEMA,'EXACT_NEW_CLOSURE_REFERENCE_REQUIRED')
    path=c.local(ref['path']);load(path)
    c.require(c.sha(path)==ref['sha256'],'CLOSURE_EVIDENCE_CHANGED')
    value=read_private(manager.context,path)
    c.require(value['schema']==SCHEMA and value['classification']=='MACHINE_EVIDENCE_NOT_INDEPENDENT_HUMAN_APPROVAL'
        and value['project_id']==expected['project_id'] and value['project_instance_id']==expected['project_instance_id']
        and value['context_digest']==manager.context.context_digest and value['receipt']==receipt
        and value['ready']==ready and value['created']==created and value['budget']==dict(limit=2,held=1,charged=1,available=0), 'CLOSURE_NATIVE_BINDING_CHANGED')
    for key in ('plan_id','plan_digest','scope_digest'):c.require(value[key]==expected[key],'CLOSURE_PLAN_CHANGED')
    import sqlite3
    db=sqlite3.connect((Path(manager.context.root)/'execution.sqlite3').as_uri()+'?mode=ro',uri=True)
    try:plan=json.loads(db.execute('SELECT body FROM plans').fetchone()[0])
    finally:db.close()
    reg=plan['registration']
    c.require(value['execution_window']==reg.get('execution_window') and value['research_project']==reg['research_project']
        and value['contract']==reg['contract'],'CLOSURE_SCIENTIFIC_BINDING_CHANGED')
    identities=value['identities'];exits=value['exits'];expected_count=1 if created['transport_pid']==ready['process']['pid'] else 2
    c.require(len(identities)==len(exits)==expected_count and len({v['pid'] for v in identities})==expected_count,'EXACT_TRACKED_MEMBERS_REQUIRED')
    c.require(all(identities[0][k]==ready['process'][k] for k in identities[0]),'CLOSURE_WORKER_CHANGED')
    if expected_count==2:
        c.require(identities[1]['pid']==created['transport_pid']==ready['process']['parent_pid']
            and identities[1]['creation_time_100ns']<=identities[0]['creation_time_100ns']
            and Path(identities[1]['image_path']).name.lower()=='python.exe','CLOSURE_TRANSPORT_CHANGED')
    from window_history import original_process_exited
    for ident,exit in zip(identities,exits):
        c.require(set(ident)=={'pid','creation_time_100ns','image_path'} and all(exit[k]==v for k,v in ident.items())
            and exit['exit_code']==0 and exit['exit_source']=='retained_windows_handle','CLOSURE_EXIT_CHANGED')
        original_process_exited(ident)
    return dict(reference=ref,identities=identities,exits=exits,scope=value['member_scope'],classification='AUTOMATED_READONLY_GATE_NOT_HUMAN_SIGNATURE')
