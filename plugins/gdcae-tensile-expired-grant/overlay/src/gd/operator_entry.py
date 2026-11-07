"""One local Candidate B handoff; every execution effect uses the native AF API.

No executor, retry loop, authority ledger, or automatic recovery is implemented.
The scope file records prior operator/Main/Testing readiness; it is NOT a Grant.
Only the exact live Plan's native authorize call can issue an execution Grant.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import time
import traceback
import uuid


def require(value, reason):
    if not value:
        raise ValueError(reason)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read_bound_json(path, expected):
    from main import safe
    path = safe(path)
    require(path.stat().st_size <= 1048576, 'REFERENCE_FILE_LIMIT')
    with path.open('rb') as stream:
        raw = stream.read(1048577)
    require(len(raw) <= 1048576 and hashlib.sha256(raw).hexdigest() == expected, 'REFERENCE_FILE_DIGEST_MISMATCH')
    return json.loads(raw)


def check_decision_reference(value):
    require(isinstance(value, dict) and set(value) == {'path', 'sha256'}
            and isinstance(value['path'], str) and Path(value['path']).is_absolute()
            and isinstance(value['sha256'], str) and re.fullmatch('[a-f0-9]{64}', value['sha256']),
            'EXACT_B_DECISION_REFERENCE_REQUIRED')
    return value


def check_qualification(value):
    if isinstance(value,dict) and value.get('schema')=='expired-unconsumed-grant-reference-v1':
        require(set(value)=={'schema','operation_id','body_digest','workspace'}
                and re.fullmatch('[a-f0-9]{32}',value['operation_id']) is not None
                and re.fullmatch('[a-f0-9]{64}',value['body_digest']) is not None
                and Path(value['workspace']).is_absolute(),'EXACT_EXPIRED_GRANT_REFERENCE_REQUIRED')
        return value
    if isinstance(value,dict) and value.get('schema') in ('execution-window-stop-reference-v1','af-cross-boot-terminal-reference-v1'):
        require(set(value)=={'schema','path','sha256'},'EXACT_WINDOW_STOP_REFERENCE_REQUIRED')
        check_decision_reference(dict(path=value['path'],sha256=value['sha256']))
        return value
    require(isinstance(value,dict) and set(value)=={'schema','pre_call','final','review','index'}
            and value['schema']=='retained-stop-review-reference-v1','EXACT_STOP_QUALIFICATION_REQUIRED')
    for key in ('pre_call','final','review','index'):check_decision_reference(value[key])
    return value


def check_cleanup_delegation(value,*,operation,work,package):
    require(isinstance(value,dict) and set(value)=={'permitted_actions','reference'}
            and value['permitted_actions']==['normal_idle_stop_unexecuted'],'EXACT_CLEANUP_DELEGATION_REQUIRED')
    ref=check_decision_reference(value['reference'])
    source=read_bound_json(ref['path'],ref['sha256'])
    require(set(source)=={'schema','operation_id','workspace','package_pin','permitted_actions','solver_grant','source_reference'}
            and source['schema']=='local-operation-delegation-v1' and source['operation_id']==operation
            and source['workspace']==str(work) and source['package_pin']==package
            and source['permitted_actions']==value['permitted_actions'] and source['solver_grant'] is False
            and isinstance(source['source_reference'],str) and source['source_reference'].strip(), 'CLEANUP_DELEGATION_BINDING_MISMATCH')
    # This is a pinned record of prior delegation, not a permission issuer.
    # Native lifecycle capability and atomic idle checks remain authoritative.
    return dict(value,source=source)


def write_new(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())


class Journal:
    """Exclusive operation evidence directory, not a second authoritative store."""
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=False, exist_ok=False)

    def put(self, name, value):
        write_new(self.root / (name + '.json'), value)
        return value

    def call(self, name, arguments, action):
        key = name.replace('-', '_') + '_' + uuid.uuid4().hex
        self.put(name + '-request', dict(operation_key=key, arguments=arguments))
        # Request survives exceptions and process death. Never create another key.
        result = action(key)
        return self.put(name + '-result', result)


RESOURCES = dict(slots=1, cpus=1, gpus=0, memory_mb=2048,
                 observation_seconds=300, launch_budget=1)
ACTIONS = ['jit_candidate_b_execution_window', 'owner_start', 'human_exact_grant', 'submit_once',
           'dispatch_once', 'observe_bounded', 'normal_completed_idle_stop',
           'raw_evidence', 'native_odb_observation']


def check_scope(scope, *, package, contract, work, operation, checker):
    require(set(scope) == {'schema', 'workspace', 'contract_pin', 'package_pin',
                           'operation_id', 'checker_sha256', 'actions',
                           'independent_readiness_reference', 'site_authorization_reference',
                           'operator_ready', 'retry', 'resources', 'purpose', 'decision_reference','qualification','cleanup_delegation'}, 'EXACT_SCOPE_FIELDS_REQUIRED')
    require(scope['schema'] == 'tensile-b-execution-window-local-scope-v1'
            and scope['workspace'] == str(work) and scope['contract_pin'] == contract
            and scope['package_pin'] == package and scope['operation_id'] == operation
            and scope['checker_sha256'] == checker and scope['actions'] == ACTIONS
            and scope['operator_ready'] is True and scope['retry'] == 0
            and scope['resources'] == RESOURCES and scope['purpose'] == 'JIT_HUMAN_REVIEW',
            'EXACT_SCOPE_MISMATCH')
    require(all(isinstance(scope[k], str) and scope[k].strip() for k in
                ('independent_readiness_reference', 'site_authorization_reference')),
            'PREWINDOW_REVIEW_REFERENCES_REQUIRED')
    check_decision_reference(scope['decision_reference'])
    check_qualification(scope['qualification'])
    check_cleanup_delegation(scope['cleanup_delegation'],operation=operation,work=work,package=package)
    return scope


class Native:
    """Installed APIs only. No command line Solver launch is present here."""
    def __init__(self, camp):
        from r3_bridge import trusted_af
        trusted_af()
        import execution_windows
        from abqjobpilot.service_lifecycle import ServiceLifecycleManager
        from abqjobpilot.product_standard import StandardOperator, inspect_preparation
        from abqjobpilot.execution.product_standard import scope
        from abqjobpilot.execution.models import digest
        from abqjobpilot.local_credentials import user_sid
        self.camp, self.b_admission = camp, execution_windows
        self.tracked=None
        self.package_pin=sha(Path(__file__).resolve().parent/'package-manifest.json')
        self.Manager, self.Operator, self.inspect = ServiceLifecycleManager, StandardOperator, inspect_preparation
        self.scope, self.digest, self.sid = scope, digest, user_sid

    def static(self, operation):
        return self.b_admission.static(self.camp, operation, self.camp.b_readmission_qualification)

    def prepare(self, proposal, pin, expires):
        return self.b_admission.prepare(self.camp, proposal, pin, expires)

    def dynamic(self, path):
        return self.b_admission.dynamic(self.camp, path)

    def review_binding(self):
        return self.b_admission.snapshot(self.camp,'--committed')['result']

    def installation(self):
        from types import SimpleNamespace
        from main import verify
        from r3_bridge import trusted_af
        from af_installation import ROOT
        root=Path(__file__).resolve().parent
        verify(root,SimpleNamespace(package_pin=self.package_pin,python_exe=sys.executable))
        trusted_af()
        return dict(gd_installed=str(root),gd_package_sha256=sha(root/'package-manifest.json'),
                    af_installed=ROOT,af_identity=sha(root/'af_installation.py'))

    def record_acceptance(self):
        from native_accounting import record_acceptance
        return record_acceptance(self.camp,phase='B')

    def cleanup_preflight(self,plan,owner):
        """Read current durable Plan without reviving its expired authorization."""
        from abqjobpilot.execution.store import open_existing_read_only,document,gate_view
        from abqjobpilot.execution.lifecycle import require_idle
        self.installation()
        budget=self.camp.inspect()['budget']
        require(budget==dict(limit=2,held=1,charged=1,available=0),'CLEANUP_SCIENTIFIC_STATE_CHANGED')
        connected=self.connect(owner)
        require(connected['project_instance_id']==plan['project_instance_id'],'CLEANUP_INSTANCE_CHANGED')
        current=self.manager._current()
        require(current and current['start_id']==owner['start_id'] and self.manager._stopped(current) is None,'CLEANUP_LIFECYCLE_CHANGED')
        client,context,health=self.manager.connect()
        require(context==self.manager.context and client.endpoint['owner_id']==owner['owner_id']
                and health['lifecycle_start_id']==owner['start_id'] and 'lifecycle_stop' in health['operations'], 'CLEANUP_NATIVE_CAPABILITY_REQUIRED')
        extension=self.manager._profile()['standard_extension']
        binding=extension['binding']
        require(binding['plan_id']==plan['plan_id'] and binding['plan_digest']==plan['plan_digest'],'CLEANUP_PROFILE_CHANGED')
        tables=('grants','runs','receipts','consumption','events','management_grants','management_receipts','management_consumption')
        with open_existing_read_only(self.manager.context).read() as conn:
            actual=document(conn,'plans','plan_id',plan['plan_id'])
            counts={name:conn.execute('SELECT COUNT(*) FROM '+name).fetchone()[0] for name in tables}
            gate=gate_view(conn);slot=conn.execute('SELECT run_id FROM slot WHERE id=1').fetchone()[0]
            require(actual==plan and conn.execute('SELECT COUNT(*) FROM plans').fetchone()[0]==1
                    and all(n==0 for n in counts.values()) and gate['state']=='PAUSED'
                    and gate['owner_id']==owner['owner_id'] and slot is None,'CLEANUP_NOT_EXACT_UNEXECUTED_IDLE')
            require_idle(conn,standard_binding=binding)
        return dict(plan_id=plan['plan_id'],owner=connected,counts=counts,gate=gate,slot_run_id=slot,budget=budget,
                    active_dispatches='NOT_OBSERVED_HERE_RECHECKED_AT_NATIVE_STOP',execution_authorized=False)

    def cleanup_records(self,plan):
        from abqjobpilot.execution.store import open_existing_read_only,document,gate_view
        with open_existing_read_only(self.manager.context).read() as conn:
            require(document(conn,'plans','plan_id',plan['plan_id'])==plan,'CLEANUP_POST_PLAN_CHANGED')
            counts={name:conn.execute('SELECT COUNT(*) FROM '+name).fetchone()[0]
                    for name in ('grants','runs','receipts','consumption','events')}
            gate=gate_view(conn);slot=conn.execute('SELECT run_id FROM slot WHERE id=1').fetchone()[0]
        require(all(n==0 for n in counts.values()) and gate['state']=='PAUSED' and slot is None,'CLEANUP_POST_EXECUTION_UNKNOWN')
        budget=self.camp.inspect()['budget']
        require(budget==dict(limit=2,held=1,charged=1,available=0),'CLEANUP_POST_SCIENTIFIC_STATE_CHANGED')
        return dict(counts=counts,gate=gate,slot_run_id=slot,budget=budget,process_exit='NOT_INDEPENDENTLY_VERIFIED')


    def attach(self, project):
        self.manager = self.Manager(project)
        self.operator = self.Operator(project)

    def start(self):
        return self.manager.start(wait_seconds=8)

    def connect(self, owner):
        self.client, context, health = self.manager.connect()
        require(self.client.endpoint['owner_id'] == owner['owner_id']
                and health['lifecycle_start_id'] == owner['start_id'], 'CONNECTED_IDENTITY_MISMATCH')
        from window_closure import TrackedOwner
        if self.tracked is None:self.tracked=TrackedOwner(self.manager,health,owner)
        else:self.tracked.verify(health,owner)
        return dict(project_instance_id=context.project_instance_id,
                    owner_id=self.client.endpoint['owner_id'], start_id=health['lifecycle_start_id'])

    def completion_exits(self,owner,stop):
        require(self.tracked is not None,'RETAINED_OWNER_REFERENCES_REQUIRED')
        return self.tracked.exit_record(owner,stop)

    def closure(self,plan,owner,stop,journal_root):
        require(self.tracked is not None,'RETAINED_OWNER_REFERENCES_REQUIRED')
        return self.tracked.record(plan,owner,stop,journal_root,self.camp)

    def close(self):
        if self.tracked is not None:self.tracked.close()

    def authorize(self, args, key, owner):
        return self.operator.request('authorize', args, operation_key=key, owner_id=owner)

    def submit(self, request):
        return self.client.submit(request)

    def run(self, run_id):
        return self.client.run(run_id)

    def gate(self):
        return self.client.dispatch_gate()

    def project_view(self):
        return self.client.project_view(limit=1)

    def dispatch(self, args, key, owner):
        return self.operator.request('dispatch_once', args, operation_key=key, owner_id=owner)

    def stop(self, owner, key):
        return self.manager.stop(owner_id=owner, operation_key=key)

    def stopped(self):
        # No reconnect/poll against a stopped Owner. Require the native persistent receipt/marker pair.
        marker = self.manager._stopped(self.manager._current())
        return marker

    def observe(self, request):
        from native_accounting import feedback_once
        return feedback_once(self.camp,request)


def check_plan(plan, checked, now):
    require(plan == checked['new']['plan'] and checked['plan_id'] == plan['plan_id']
            and checked['plan_digest'] == plan['plan_digest']
            and checked['scope_digest'] == checked['new']['scope_digest'], 'GATE_PLAN_MISMATCH')
    require(plan['registration']['purpose'] == 'JIT_HUMAN_REVIEW' and plan['registration']['phase'] == 'B'
            and plan['resources'] == RESOURCES and plan['expires_at'] > now
            and checked['execution_authorized'] is False
            and checked['budget'] == dict(limit=2, held=1, charged=1, available=0), 'PLAN_SCOPE_OR_EXPIRY')


def raw_artifacts(plan):
    from main import safe
    root = safe(plan['engineering'])
    require(not (root / (plan['job_name'] + '.lck')).exists(), 'OUTPUT_STILL_LOCKED')
    values = {}
    for ext in ('inp', 'odb', 'sta', 'msg', 'dat'):
        path = safe(root / (plan['job_name'] + '.' + ext))
        if ext == 'dat' and not path.exists():
            values[ext] = dict(status='NOT_PRESENT', path=str(path),
                               reason='Not generated or missing; existence check cannot distinguish')
            continue
        require(path.is_file() and path.stat().st_size > 0 and path.stat().st_nlink == 1, 'RAW_ARTIFACT_REQUIRED')
        values[ext] = dict(status='PRESENT', path=str(path), sha256=sha(path), size=path.stat().st_size)
    return values


def _execute(native, journal, operation, *, confirmation=None, emit=print, wall=time.time,
            clock=time.monotonic, sleep=time.sleep, artifacts=raw_artifacts):
    """Bounded orchestration, testable with in-memory native substitutes only."""
    static = journal.put('static', native.static(operation))
    require(static['status'] == 'STATIC_READONLY_READY' and static['plan_created'] is False,
            'STATIC_NOT_READY')
    require(static['proposal']['purpose'] == 'JIT_HUMAN_REVIEW', 'LIVE_SCOPE_REQUIRED_BEFORE_JIT')
    from approval_dialog import ApprovalDialog,packet_digest
    if confirmation is None:confirmation=ApprovalDialog()
    ready=journal.put('human-ready',confirmation.ready(static,operation))
    require(ready['status']=='READY_RECEIVED_NO_EXECUTION_AUTHORITY' and ready['operation_id']==operation
            and ready['proposal_digest']==static['proposal_digest'],'PRE_JIT_HUMAN_READINESS_REQUIRED')
    confirmation.check_cancelled()
    confirmation.status('正在创建 JIT Plan 并执行本地独立门控。尚未批准执行。')
    # Actual human handshake completed. TTL begins only now, not at launch.
    jit_wall,jit_clock=wall(),clock()
    jit_expires=int(jit_wall)+600
    jit_deadline=jit_clock+(jit_expires-jit_wall)
    journal.put('jit-clock-anchor',dict(epoch=jit_wall,monotonic=jit_clock,expires_epoch=jit_expires,monotonic_deadline=jit_deadline))
    result = journal.call('jit', dict(operation_id=operation, proposal_digest=static['proposal_digest']),
                          lambda key: native.prepare(static['proposal'], static['proposal_digest'], jit_expires))
    path = journal.root / 'jit-result.json'
    checked = journal.put('dynamic-gate', native.dynamic(path))
    require(checked['status'] == 'DYNAMIC_READONLY_PASS' and checked['operation_id'] == operation,
            'DYNAMIC_GATE_REQUIRED')
    plan = checked['new']['plan']
    check_plan(plan, checked, wall())
    require(native.digest(native.scope(plan)) == checked['scope_digest'], 'NATIVE_SCOPE_CHANGED')
    native.attach(checked['new']['af_project'])
    view = native.inspect(checked['new']['af_project'])
    require(view['plan'] == plan and view['counts'] == dict(plans=1, grants=0, runs=0, receipts=0, consumption=0)
            and view['gate']['state'] == 'PAUSED' and view['supervisor_started'] == '0', 'NATIVE_PREFLIGHT_CHANGED')
    require(wall() < plan['expires_at'] and clock()<jit_deadline, 'PLAN_EXPIRED_BEFORE_START')
    confirmation.check_cancelled()
    confirmation.status('本地门控通过。正在连接原生 Owner；此操作不创建 Solver Grant。')
    owner = journal.call('owner-start', dict(project=checked['new']['af_project'], plan_id=plan['plan_id']), lambda key: native.start())
    require(owner['state'] == 'CONNECTED' and owner['created'] is True, 'OWNER_START_UNKNOWN')
    connected = journal.put('connected', native.connect(owner))
    require(connected['project_instance_id'] == plan['project_instance_id'], 'PROJECT_INSTANCE_CHANGED')
    # Full exact identity displayed locally. The text itself is not native permission.
    display = dict(plan_id=plan['plan_id'], plan_digest=plan['plan_digest'], scope_digest=checked['scope_digest'],
                   resources=plan['resources'], expires_at=plan['expires_at'], input_manifest=plan['input_manifest'],
                   job_id=plan['job_id'], job_revision=plan['job_revision'], job_name=plan['job_name'],
                   engineering=plan['engineering'], scratch=plan['scratch'], output_key=plan['output_key'],
                   expected_outputs={ext:str(Path(plan['engineering'])/(plan['job_name']+'.'+ext)) for ext in ('odb','sta','msg','dat')},
                   project=checked['project'], candidate=checked['candidate'], budget=checked['budget'],
                   af_project=checked['new']['af_project'], owner=owner)
    packet=json.loads(json.dumps(dict(display,operation_id=operation,parameters=plan['registration']['parameters'],
                                     plan=plan,installation=native.installation()),allow_nan=False))
    packet_pin=packet_digest(packet)
    journal.put('confirmation-packet',packet)
    proof=journal.put('human-confirmation',confirmation.authorize(packet,monotonic_deadline=jit_deadline))
    require(proof['status']=='USER_DECISION_CAPTURED' and proof['packet_sha256']==packet_pin
            and proof['operation_id']==operation
            and packet_digest(packet)==packet_pin,'CONFIRMATION_PACKET_CHANGED')
    # A button click is only a decision, never permission to skip native checks.
    saved_packet_path=journal.root/'confirmation-packet.json'
    require(saved_packet_path.stat().st_size<=1048576,'CONFIRMATION_PACKET_FILE_LIMIT')
    with saved_packet_path.open('rb') as stream: saved_packet_raw=stream.read(1048577)
    require(len(saved_packet_raw)<=1048576,'CONFIRMATION_PACKET_FILE_LIMIT')
    saved_packet=json.loads(saved_packet_raw)
    require(saved_packet==packet and packet_digest(saved_packet)==packet_pin,'PERSISTED_CONFIRMATION_PACKET_CHANGED')
    review_binding=journal.put('pre-authorize-binding',native.review_binding())
    require(review_binding['new']==checked['new'] and review_binding['budget']==checked['budget']
            and review_binding['candidate']==checked['candidate'] and review_binding['original_request']==checked['original_request'],
            'PRE_AUTHORIZE_BINDING_OR_BUDGET_CHANGED')
    require(native.installation()==packet['installation'],'PRE_AUTHORIZE_INSTALLATION_CHANGED')
    fresh=journal.put('pre-authorize-inspection',native.inspect(checked['new']['af_project']))
    require(fresh['plan']==packet['plan'] and fresh['counts']==dict(plans=1,grants=0,runs=0,receipts=0,consumption=0)
            and fresh['gate']['state']=='PAUSED' and fresh['gate']['owner_id']==owner['owner_id']
            and fresh['supervisor_started']=='1'
            and native.digest(native.scope(plan))==packet['scope_digest'],'PRE_AUTHORIZE_NATIVE_STATE_CHANGED')
    reconnected=journal.put('pre-authorize-connected',native.connect(owner))
    require(reconnected==connected and reconnected['owner_id']==owner['owner_id']
            and reconnected['start_id']==owner['start_id'],'PRE_AUTHORIZE_OWNER_CHANGED')
    project_view=journal.put('pre-authorize-project-view',native.project_view())
    require(project_view['project_id']==plan['registration']['project_id']
            and project_view['project_instance_id']==plan['project_instance_id']
            and project_view['gate']['state']=='PAUSED' and project_view['gate']['owner_id']==owner['owner_id']
            and project_view['slot_run_id'] is None and project_view['runs']==[], 'PRE_AUTHORIZE_SLOT_OR_RUN_CHANGED')
    require(wall() < plan['expires_at'] and clock()<jit_deadline, 'PLAN_EXPIRED_DURING_CONFIRMATION')
    confirmation.before_native_authorize(expires=plan['expires_at'],monotonic_deadline=jit_deadline)
    args = dict(plan_id=plan['plan_id'], plan_digest=plan['plan_digest'], expires_at=plan['expires_at'],
                subject=native.sid(), source=checked['scope_digest'])
    from grant_response import authorize_once
    grant = authorize_once(native, journal, args, owner['owner_id'], deadline=jit_deadline)
    gr = grant['receipt']
    require(gr['scope_digest'] == checked['scope_digest'] and grant['replayed'] is False
            and wall() < min(plan['expires_at'], gr['expires_at']) and clock()<jit_deadline, 'GRANT_RESPONSE_MISMATCH')
    confirmation.native_granted(grant)
    emit('Native Grant received: '+gr['grant_id']+'; submitting exactly once.')
    confirmation.check_cancelled()
    submit = dict(contract_version='af-experiment-v1', operation='submit', project_id=plan['registration']['project_id'],
                  project_instance_id=plan['project_instance_id'], job_id=plan['job_id'], job_revision=plan['job_revision'],
                  plan_id=plan['plan_id'], plan_digest=plan['plan_digest'], grant_id=gr['grant_id'], retry_of=None)
    accepted = journal.call('submit', submit, lambda key: native.submit(dict(submit, idempotency_key=key)))
    require(accepted['request_status'] == 'ACCEPTED', 'SUBMIT_UNKNOWN')
    journal.call('native-acceptance-fact',dict(run_id=accepted['receipt']['run_id'],phase='B'),lambda key:native.record_acceptance())
    run_id = accepted['receipt']['run_id']
    run, gate = native.run(run_id), native.gate()
    require(run['plan_id'] == plan['plan_id'] and run['plan_digest'] == plan['plan_digest']
            and run['grant_id'] == gr['grant_id'] and run['execution'] == 'PLANNED'
            and run['queue_state'] == 'PENDING' and run['launch_state'] == 'NOT_CALLED'
            and gate['state'] == 'PAUSED' and gate['owner_id'] == owner['owner_id'], 'PRE_DISPATCH_CHANGED')
    require(wall() < min(plan['expires_at'], gr['expires_at']) and clock()<jit_deadline, 'PLAN_OR_GRANT_EXPIRED')
    confirmation.check_cancelled()
    confirmation.status('原生 Run 已接受。正在单次 Dispatch；科研记账仍遵循原冻结合同，不会自动重试。')
    dispatch = dict(run_id=run_id, revision=run['revision'], gate_version=gate['version'],
                    start_not_after=min(int(wall()) + 30, plan['expires_at'], gr['expires_at']))
    started = clock()
    dispatched = journal.call('dispatch', dispatch, lambda key: native.dispatch(dispatch, key, owner['owner_id']))
    require(dispatched['receipt']['run_id'] == run_id and dispatched['receipt']['grant_id'] == gr['grant_id'], 'DISPATCH_UNKNOWN')
    observations = []
    confirmation.status('已单次 Dispatch。正在读取原生运行状态（最多 300 秒）；关闭窗口不等于停止 Solver。')
    while clock() < started + 294:
        confirmation.check_cancelled()
        run = native.run(run_id)
        item = dict(at=wall(), elapsed=clock() - started, run=run)
        journal.put('observation-%04d' % len(observations), item)
        observations.append(item)
        if run['reconciliation'] != 'NONE' or run['execution'] in ('BLOCKED', 'FINISHED'):
            break
        sleep(min(2, max(0, started + 294 - clock())))
    elapsed = clock() - started
    journal.put('observation-elapsed', dict(elapsed=elapsed, over_300_seconds=elapsed > 300))
    require(observations and elapsed <= 300 and run['execution'] == 'FINISHED'
            and run['reconciliation'] == 'NONE' and run.get('managed_completion') == 'COMMITTED_EMPTY_SCOPE',
            'OBSERVATION_UNKNOWN_NO_CLEANUP')
    final = native.run(run_id)
    require(final['execution'] == 'FINISHED' and final['reconciliation'] == 'NONE'
            and final.get('managed_completion') == 'COMMITTED_EMPTY_SCOPE', 'COMPLETION_CHANGED')
    stop = journal.call('normal-stop', dict(owner_id=owner['owner_id'], start_id=owner['start_id'], run_id=run_id),
                        lambda key: native.stop(owner['owner_id'], key))
    require(stop['receipt']['state'] == 'STOP_COMMITTED' and stop['receipt']['owner_id'] == owner['owner_id']
            and stop['receipt']['start_id'] == owner['start_id'], 'STOP_UNKNOWN')
    deadline = clock() + 10
    marker = None
    while clock() < deadline:
        marker = native.stopped()
        if marker:
            break
        sleep(.25)
    require(marker and marker['receipt'] == stop['receipt'], 'ORDERLY_STOP_NOT_RECORDED')
    journal.put('stopped-marker', marker)
    journal.put('owner-exit-status', native.completion_exits(owner,stop))
    journal.put('raw-artifact-identities', artifacts(plan))
    feedback = journal.call('native-observation', dict(original_request=checked['original_request']),
                            lambda key: native.observe(checked['original_request']))
    confirmation.status('原生运行、正常收尾和新 ODB 反馈已返回。等待独立科研验收；不自动生成下一候选。')
    return journal.put('handoff', dict(status='NATIVE_FEEDBACK_PENDING_INDEPENDENT_REVIEW', result=feedback,
                                      independent_acceptance='NOT_PERFORMED', next_candidate='NOT_PROPOSED',
                                      execution_retry=False, operation_id=operation))


def cleanup_unexecuted(native,journal,delegation,reason,*,clock=time.monotonic,sleep=time.sleep):
    require(reason in {'HUMAN_CANCELLED_NO_RETRY','APPROVAL_EXPIRED_NO_GRANT','PLAN_EXPIRED_DURING_CONFIRMATION'},'CLEANUP_REASON_NOT_PERMITTED')
    require(delegation and delegation['permitted_actions']==['normal_idle_stop_unexecuted'],'CLEANUP_NOT_DELEGATED')
    require(not any((journal.root/(name+'.json')).exists() for name in
                    ('authorize-request','authorize-result','submit-request','submit-result','dispatch-request','dispatch-result',
                     'cancel-idle-stop-request','cancel-idle-stop-result')), 'CLEANUP_EXECUTION_OR_PRIOR_STOP_UNKNOWN')
    owner_path=journal.root/'owner-start-result.json';gate_path=journal.root/'dynamic-gate.json'
    require(owner_path.is_file() and gate_path.is_file(),'CLEANUP_OWNER_NOT_CONFIRMED')
    owner=json.loads(owner_path.read_bytes());checked=json.loads(gate_path.read_bytes());plan=checked['new']['plan']
    require(owner['state']=='CONNECTED' and owner['created'] is True,'CLEANUP_OWNER_NOT_CONFIRMED')
    fresh=journal.put('cancel-idle-preflight',native.cleanup_preflight(plan,owner))
    require(fresh['plan_id']==plan['plan_id'] and fresh['owner']['owner_id']==owner['owner_id']
            and fresh['owner']['start_id']==owner['start_id'] and all(n==0 for n in fresh['counts'].values())
            and fresh['gate']['state']=='PAUSED' and fresh['slot_run_id'] is None, 'CLEANUP_PREFLIGHT_NOT_IDLE')
    journal.put('cancel-idle-delegation',dict(delegation=delegation,reason=reason,native_capability_required=True,solver_grant=False))
    stopped=journal.call('cancel-idle-stop',dict(owner_id=owner['owner_id'],start_id=owner['start_id'],plan_id=plan['plan_id'],reason=reason),
                         lambda key:native.stop(owner['owner_id'],key))
    require(stopped.get('replayed') is not True and stopped['receipt']['state']=='STOP_COMMITTED'
            and stopped['receipt']['owner_id']==owner['owner_id'] and stopped['receipt']['start_id']==owner['start_id'],'CLEANUP_STOP_UNKNOWN')
    deadline=clock()+10;marker=None
    while clock()<deadline:
        marker=native.stopped()
        if marker:break
        sleep(.25)
    require(marker and marker['receipt']==stopped['receipt'],'CLEANUP_MARKER_UNKNOWN')
    journal.put('cancel-idle-stopped-marker',marker)
    records=journal.put('cancel-idle-post-records',native.cleanup_records(plan))
    qualification=check_qualification(native.closure(plan,owner,stopped,journal.root))
    journal.put('cancel-idle-qualification',qualification)
    return journal.put('cancel-idle-result',dict(status='NATIVE_UNEXECUTED_IDLE_STOP_RECORDED',receipt=stopped['receipt'],
        records=records,qualification_reference=qualification,process_exit='RETAINED_HANDLE_FACTS_RECORDED',
        independent_acceptance='NOT_PERFORMED',new_plan_created=False,solver_authorized=False))


def execute(native,journal,operation,*,cleanup_delegation=None,**kwargs):
    try:return _execute(native,journal,operation,**kwargs)
    except BaseException as exc:
        eligible=isinstance(exc,ValueError) and str(exc) in {'HUMAN_CANCELLED_NO_RETRY','APPROVAL_EXPIRED_NO_GRANT','PLAN_EXPIRED_DURING_CONFIRMATION'}
        if eligible and cleanup_delegation is not None and (journal.root/'owner-start-result.json').is_file():
            try:cleanup_unexecuted(native,journal,cleanup_delegation,str(exc),clock=kwargs.get('clock',time.monotonic),sleep=kwargs.get('sleep',time.sleep))
            except BaseException as cleanup_exc:
                journal.put('cancel-idle-blocked',dict(status='UNKNOWN_OR_REFUSED_NO_RETRY',error=str(cleanup_exc),traceback=traceback.format_exc()))
        raise


def native_context(project):
    from r3_bridge import trusted_af
    trusted_af()
    from abqjobpilot.service_lifecycle import ServiceLifecycleManager
    # Constructor only: resolve the native product/project layout, never connect.
    return ServiceLifecycleManager(project).context


def reconcile(evidence):
    """Existing artifacts and durable native records only; never reconnect/restart."""
    root = Path(evidence)
    require(root.is_dir(), 'EVIDENCE_REQUIRED')
    records = {p.name: json.loads(p.read_bytes()) for p in root.glob('*.json')}
    result = records.get('jit-result.json')
    if not result:
        return dict(status='READONLY_JOURNAL_ONLY', records=records, automatic_resume=False)
    from main import safe
    project = safe(result['new']['af_project'])
    require(project.parent == safe(root.parent), 'RECONCILIATION_PROJECT_OUTSIDE_WORKSPACE')
    context = native_context(project)
    require(safe(context.test_root) == project and safe(context.root).is_relative_to(project),
            'RECONCILIATION_CONTEXT_MISMATCH')
    db = sqlite3.connect(safe(Path(context.root) / 'execution.sqlite3').as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    try:
        db.execute('BEGIN')
        native = {table: [dict(row) for row in db.execute('SELECT * FROM ' + table)]
                  for table in ('plans', 'runs', 'receipts', 'management_receipts', 'dispatch_gate', 'slot')}
        require(len(native['plans']) == 1 and json.loads(native['plans'][0]['body']) == result['new']['plan'],
                'RECONCILIATION_PLAN_IDENTITY_MISMATCH')
    finally:
        db.close()
    markers = {str(p.relative_to(project)): json.loads(p.read_bytes())
               for p in project.glob('private/start_*/stopped.json')}
    return dict(status='READONLY_RECONCILIATION_REQUIRED', records=records, native=native, stopped_markers=markers,
                receipt_actions=['product_standard_authorize', 'product_standard_dispatch_once', 'lifecycle_stop_idle_v1'],
                automatic_resume=False, execution_authorized=False)


def main():
    from types import SimpleNamespace
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('static', 'run', 'reconcile'))
    for field in ('workspace', 'contract-pin', 'package-pin', 'python-exe', 'operation-id', 'evidence'):
        parser.add_argument('--' + field, required=True)
    parser.add_argument('--scope'); parser.add_argument('--scope-pin')
    parser.add_argument('--decision'); parser.add_argument('--decision-pin')
    parser.add_argument('--qualification'); parser.add_argument('--qualification-pin')
    a = parser.parse_args()
    root = Path(__file__).resolve().parent
    sys.path[:0] = [str(root), str(root / 'runtime')]
    from main import verify, safe
    verify(root, SimpleNamespace(python_exe=a.python_exe, package_pin=a.package_pin))
    work, evidence = safe(a.workspace), safe(a.evidence)
    require(Path(a.workspace).is_absolute() and Path(a.evidence).is_absolute()
            and evidence.parent == work and not evidence.is_relative_to(root), 'RESEARCH_OPERATION_DIRECTORY_REQUIRED')
    require(re.fullmatch('[a-f0-9]{32}', a.operation_id) is not None, 'EXACT_OPERATION_ID_REQUIRED')
    if a.action == 'reconcile':
        return reconcile(evidence)
    import workflow
    camp = workflow.Campaign(work, a.contract_pin, a.package_pin, readonly=a.action == 'static', candidate_b_admission=True)
    native=None
    try:
        native = Native(camp)
        if a.action == 'static':
            require(a.decision and a.decision_pin, 'EXACT_B_DECISION_REFERENCE_REQUIRED')
            ref = check_decision_reference(dict(path=a.decision, sha256=a.decision_pin))
            camp.b_decision = read_bound_json(ref['path'], ref['sha256'])
            require(a.qualification and a.qualification_pin,'EXACT_STOP_QUALIFICATION_REQUIRED')
            camp.b_readmission_qualification=check_qualification(read_bound_json(a.qualification,a.qualification_pin))
            return native.static(a.operation_id)
        from approval_dialog import ApprovalDialog
        require(a.scope and a.scope_pin, 'REVIEWED_SCOPE_FILE_REQUIRED')
        scope = check_scope(read_bound_json(a.scope, a.scope_pin), package=a.package_pin, contract=a.contract_pin,
                            work=work, operation=a.operation_id, checker=sha(root / 'execution_windows.py'))
        ref = scope['decision_reference']
        if a.decision or a.decision_pin:
            require(dict(path=a.decision, sha256=a.decision_pin) == ref, 'B_DECISION_OVERRIDE_DENIED')
        camp.b_decision = read_bound_json(ref['path'], ref['sha256'])
        camp.b_readmission_qualification=scope['qualification']
        cleanup_delegation=check_cleanup_delegation(scope['cleanup_delegation'],operation=a.operation_id,work=work,package=a.package_pin)
        journal = Journal(evidence)
        journal.put('scope-reference', dict(scope=scope, scope_sha256=a.scope_pin,
                                           statement='Prior scope reference is not a native execution Grant'))
        confirmation=ApprovalDialog()
        try:
            result=execute(native, journal, a.operation_id, confirmation=confirmation,cleanup_delegation=cleanup_delegation)
            confirmation.finish()
            return result
        except BaseException as exc:
            journal.put('halt', dict(status='UNKNOWN_STOPPED_NO_RETRY', error_type=type(exc).__name__,
                                     error=str(exc), traceback=traceback.format_exc(), automatic_resume=False))
            confirmation.status('停止：'+str(exc)+'。未自动重试或终止进程；保留证据并只读对账。')
            confirmation.finish()
            raise
    finally:
        try:
            if native is not None:native.close()
        finally:camp.db.close()


if __name__ == '__main__':
    try:
        print(json.dumps(main(), indent=2, allow_nan=False))
    except BaseException as exc:
        print(json.dumps(dict(status='BLOCKED_OR_UNKNOWN_NO_RETRY', error=str(exc), traceback=traceback.format_exc())))
        sys.exit(2)
