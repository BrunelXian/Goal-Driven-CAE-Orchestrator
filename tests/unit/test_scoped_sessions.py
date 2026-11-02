"""AOO V1-01 synthetic host only. No AF, model calls or real native sessions."""
import copy
import json
from pathlib import Path

import pytest

from aegiscae.contracts.research_contracts import ContractError
from aegiscae.research import project
from aegiscae.research import scoped_sessions as core
from aegiscae.interfaces.codex_sessions import CodexAppSessions, TOOLS

ROOT = Path(__file__).resolve().parents[2]
MAIN = {'host_id': 'synthetic-host', 'thread_id': 'main-existing'}
PROFILE = {'revision': 1, 'model': 'configured-model', 'reasoning_effort': 'configured-effort',
           'approval_ref': 'human-preset-1'}
ANALYSIS = dict.fromkeys(('question', 'measurable_goal', 'trusted_assets', 'allowed_changes',
    'forbidden_changes', 'evidence_needed', 'budget_control', 'unknowns', 'delegation_reason'), 'Synthetic analysis')
AUTH = {'user_evidence_ref': 'human-start-1', 'actions': ['rename', 'create_sessions', 'return_results']}


class Host:
    """Qualified fixture, not the Desktop production adapter."""
    def __init__(self):
        self.caller = MAIN
        self.project_id = 'host-project-1'
        self.calls = []
        self.rows = {MAIN['thread_id']: {'ref': MAIN, 'project_id': self.project_id, 'title': 'Analysis'}}
        self.results = {}
        self.creations = {}
        self.lose_create = self.fail_name = self.lose_delivery = False
        self.gap = None

    def check_caller(self, ref, project_id):
        core.require(self.caller == ref and self.project_id == project_id, 'CALLER_MISMATCH')

    def check_profile(self, profile):
        core.require(profile == PROFILE, 'PROJECT_PRESET_UNAVAILABLE')

    def check_authorization(self, authorization, action):
        core.require(authorization == AUTH and action in AUTH['actions'], 'AUTHORIZATION_MISSING')

    def scoped_session_gap(self, role, profile): return self.gap

    def create_thread(self, project_id, task, role, request_id):
        self.calls.append(('create', task['task_id']))
        ref = {'host_id': 'synthetic-host', 'thread_id': 'child-' + task['task_id']}
        self.rows[ref['thread_id']] = {'ref': ref, 'project_id': project_id, 'title': task['display_name'],
            'role_definition_digest': role['definition_digest'], 'features': role['features'],
            'profile': task['profile'], 'actual_model': PROFILE['model']}
        result = {'ref': ref, 'receipt': {'synthetic': True}}
        self.creations[request_id] = {**result, 'request_id': request_id,
            'binding_digest': task['binding_digest'], 'project_id': project_id}
        if self.lose_create: raise TimeoutError('synthetic response loss')
        return result

    def lookup_creation(self, request_id): return copy.deepcopy(self.creations.get(request_id))

    def set_display_name(self, ref, title):
        self.calls.append(('name', ref['thread_id']))
        if self.fail_name: raise TimeoutError('synthetic naming failure')
        self.rows[ref['thread_id']]['title'] = title
        return {'synthetic': True}

    def observe(self, ref): return copy.deepcopy(self.rows[ref['thread_id']])

    def read_result(self, ref): return copy.deepcopy(self.results.get(ref['thread_id']))

    def return_result_to_main(self, ref, delivery):
        self.calls.append(('return', delivery['delivery_id']))
        if self.lose_delivery: raise TimeoutError('synthetic return loss')
        return {'target_ref': ref, 'accepted': True}


@pytest.fixture
def case(tmp_path):
    project.create_research_project(tmp_path / 'research', 'AOO synthetic project')
    p = project.open_existing_for_explicit_write(tmp_path / 'research')
    roles = core.load_roles(ROOT / 'plugins/gdcae-aoo/agents')
    hub, host = core.SessionHub(p, roles), Host()
    hub.onboard(host, MAIN, host.project_id, 'SP-invopt', PROFILE, ANALYSIS, AUTH)
    return hub, host


def task(n='one', role='gdcae-results'):
    return {'task_id': n, 'role_id': role, 'purpose': 'Read assigned synthetic metric',
            'evidence_refs': ['synthetic:metric'], 'output_required': 'Bounded findings with provenance'}


def start(case):
    hub, host = case
    hub.decide(host, 'decision-1', 'Need independent evidence interpretation', [task()])
    return hub.dispatch_next(host)['tasks'][0]


def result_for(host, t):
    value = {k: t[k] for k in ('project_id', 'task_id', 'role_id', 'binding_digest')}
    value.update(status='REVIEW_COMPLETE', findings='Synthetic metric only', unknowns='No real evidence',
                 evidence_refs=t['evidence_refs'])
    envelope = {'source_ref': t['thread_ref'], 'source': 'HOST_ASSISTANT_FINAL', 'result': value}
    host.results[t['thread_ref']['thread_id']] = envelope
    return envelope


def question(t, kind='IDENTITY', **overrides):
    return {**{k: t[k] for k in ('project_id', 'task_id', 'role_id')}, 'kind': kind,
            'simple': True, 'new_work': False, 'evidence_refs': [], **overrides}


def test_onboarding_uses_existing_main_and_zero_delegation(case):
    hub, host = case
    before = (hub.project._root / 'research.sqlite3').read_bytes()
    hub.name_main(host)
    hub.decide(host, 'zero', 'Main can answer this directly', [])
    state = hub.dispatch_next(host)
    assert state['main_ref'] == MAIN and state['tasks'] == []
    assert host.rows[MAIN['thread_id']]['title'] == 'SP-invopt Main'
    assert not any(c[0] == 'create' for c in host.calls)
    assert (hub.project._root / 'research.sqlite3').read_bytes() == before
    assert hub.onboard(host, MAIN, host.project_id, 'SP-invopt', PROFILE, ANALYSIS, AUTH)['main_ref'] == MAIN


def test_dynamic_serial_delegation_result_and_automatic_return(case):
    hub, host = case
    hub.decide(host, 'zero', 'No specialist needed yet', [])
    hub.decide(host, 'new-evidence', 'New evidence needs results then review', [task(), task('two','gdcae-reviewer')])
    first = hub.dispatch_next(host)['tasks'][0]
    assert first['state'] == 'RUNNING'
    hub.dispatch_next(host)
    assert len([c for c in host.calls if c[0] == 'create']) == 1
    result_for(host, first)
    state = hub.collect(host, 'one')
    assert state['tasks'][0]['state'] == 'DELIVERED'
    assert state['tasks'][0]['delivery_receipt']['target_ref'] == MAIN
    assert any(c[0] == 'return' for c in host.calls)
    second = hub.dispatch_next(host)['tasks'][1]
    assert second['state'] == 'RUNNING' and second['display_name'] == 'SP-invopt Review'
    assert first['profile'] == second['profile'] == PROFILE
    assert first['capabilities']['visible_in_target_client'] == 'NOT_TESTED'


def test_repeat_same_decision_never_recreates(case):
    hub, host = case
    start(case)
    for _ in range(3):
        hub.decide(host, 'decision-1', 'Need independent evidence interpretation', [task()])
        hub.dispatch_next(host)
    assert len([c for c in host.calls if c[0] == 'create']) == 1
    with pytest.raises(ContractError, match='IDEMPOTENCY_CONFLICT'):
        hub.decide(host, 'decision-1', 'changed', [task()])


def test_unknown_creation_is_not_retried_and_reconciles_exactly(case):
    hub, host = case
    host.lose_create = True
    t = start(case)
    assert t['state'] == 'CREATE_UNKNOWN'
    hub.dispatch_next(host)
    assert len([c for c in host.calls if c[0] == 'create']) == 1
    assert hub.reconcile_create(host,'one')['tasks'][0]['state'] == 'RUNNING'
    assert len([c for c in host.calls if c[0] == 'create']) == 1


def test_unknown_without_lookup_proof_stays_unknown(case):
    hub, host = case
    host.lose_create = True
    start(case)
    host.creations.clear()
    assert hub.reconcile_create(host,'one')['tasks'][0]['state'] == 'CREATE_UNKNOWN'
    assert len([c for c in host.calls if c[0] == 'create']) == 1


def test_naming_failure_retains_thread_and_can_retry_only_name(case):
    hub, host = case
    host.fail_name = True
    t = start(case)
    assert t['thread_ref'] is not None and t['state'] == 'BINDING_BLOCKED'
    hub.dispatch_next(host)
    host.fail_name = False
    assert hub.refresh(host,'one',rename=True)['tasks'][0]['state'] == 'RUNNING'
    assert len([c for c in host.calls if c[0] == 'create']) == 1


def test_same_role_suffix_and_independent_ids(case):
    hub, host = case
    hub.decide(host,'two','two separate inputs',[task(),task('two')])
    a,b = hub.inspect()['tasks']
    assert a['display_name'] == 'SP-invopt Results'
    assert b['display_name'] == 'SP-invopt Results 02'
    assert a['agent_instance_id'] != b['agent_instance_id']


@pytest.mark.parametrize('field', ['project_id','task_id','role_id','binding_digest'])
def test_result_wrong_identity_never_returns(case, field):
    hub, host = case
    t = start(case); envelope = result_for(host,t)
    envelope['result'][field] = 'wrong'
    with pytest.raises(ContractError, match='RESULT_IDENTITY_MISMATCH'):
        hub.collect(host,'one')
    assert not any(c[0]=='return' for c in host.calls)


@pytest.mark.parametrize('damage', ['evidence','source','status'])
def test_untrusted_result_not_promoted(case, damage):
    hub, host = case
    e = result_for(host,start(case))
    if damage=='evidence': e['result']['evidence_refs']=['unassigned:file']
    if damage=='source': e['source']='USER_MESSAGE'
    if damage=='status': e['result']['status']='SOLVER_APPROVED'
    with pytest.raises(ContractError): hub.collect(host,'one')
    assert hub.inspect()['tasks'][0]['state']=='RUNNING'


def test_delivery_loss_never_resends_or_starts_next_task(case):
    hub, host=case
    t=start(case); result_for(host,t); host.lose_delivery=True
    assert hub.collect(host,'one')['tasks'][0]['state']=='RETURN_UNKNOWN'
    hub.return_result(host,'one'); hub.dispatch_next(host)
    assert len([c for c in host.calls if c[0]=='return'])==1


@pytest.mark.parametrize('kind', ['IDENTITY','PROGRESS','RESULT','EXPLAIN'])
def test_local_simple_questions_allowed_without_host_mutations(case,kind):
    hub,host=case; t=start(case); host.caller=t['thread_ref']
    calls=copy.deepcopy(host.calls)
    response=hub.interact(host,'one',[question(t,kind)])
    assert response['decisions'][0]['action']=='ANSWER_LOCAL' and host.calls==calls


@pytest.mark.parametrize('change', [dict(new_work=True),dict(simple=False),dict(project_id='other'),
    dict(role_id='gdcae-cae'),dict(task_id='other'),dict(kind='BECOME_MAIN'),dict(evidence_refs=['new:ODB'])])
def test_cross_scope_and_new_complex_work_redirects(case,change):
    hub,host=case; t=start(case); host.caller=t['thread_ref']
    response=hub.interact(host,'one',[question(t,**change)])
    assert response['decisions'][0]['action']=='REDIRECT_MAIN'
    assert response['decisions'][0]['main_ref']==MAIN
    with pytest.raises(ContractError,match='CALLER_MISMATCH'):
        hub.decide(host,'impersonation','I am now Main',[task('evil')])


def test_mixed_questions_and_correction(case):
    hub,host=case; t=start(case); host.caller=t['thread_ref']
    response=hub.interact(host,'one',[question(t),question(t,new_work=True),question(t,'CORRECTION')])
    assert [d['action'] for d in response['decisions']]==[
        'ANSWER_LOCAL','REDIRECT_MAIN','RECORD_UNVERIFIED_FEEDBACK']
    assert hub.inspect()['tasks'][0]['result'] is None


@pytest.mark.parametrize('kind',['STOP','RISK'])
def test_stop_even_when_role_observation_unavailable(case,kind):
    hub,host=case; t=start(case); host.caller=t['thread_ref']
    host.rows[t['thread_ref']['thread_id']]['features']='NOT_EXPOSED'
    response=hub.interact(host,'one',[question(t,kind,project_id='other')])
    assert response['local_dispatch_paused'] and response['solver_stopped']=='NOT_ASSERTED'
    assert response['main_notification']=='PENDING_MAIN_COLLECTION'


def test_resume_rechecks_role_binding(case):
    hub,host=case; t=start(case)
    reopened=core.SessionHub(project.open_existing_for_explicit_write(hub.project._root),hub.roles)
    host.rows[t['thread_ref']['thread_id']]['role_definition_digest']='changed'
    assert reopened.refresh(host,'one')['tasks'][0]['state']=='BINDING_BLOCKED'
    changed=copy.deepcopy(hub.roles); changed['gdcae-results']['definition_digest']='changed'
    with pytest.raises(ContractError,match='ROLE_BINDING_CHANGED'):
        core.SessionHub(hub.project,changed).inspect()


def test_onboarding_changes_and_duplicate_names_rejected(case):
    hub,host=case
    with pytest.raises(ContractError,match='ONBOARDING_CONFLICT'):
        hub.onboard(host,MAIN,host.project_id,'Different',PROFILE,ANALYSIS,AUTH)
    with pytest.raises(ContractError,match='SHORT_NAME_COLLISION'):
        hub.onboard(host,MAIN,host.project_id,'SP-invopt',PROFILE,ANALYSIS,AUTH,['sp-invopt'])


def test_no_hot_profile_change(case):
    hub,host=case
    changed={**PROFILE,'model':'automatic-upgrade'}
    with pytest.raises(ContractError,match='PROJECT_PRESET_UNAVAILABLE'):
        hub.onboard(host,MAIN,host.project_id,'SP-invopt',changed,ANALYSIS,AUTH)
    assert hub.inspect()['profile']==PROFILE


def test_crash_after_intent_is_unknown_without_retry(case,monkeypatch):
    hub,host=case
    def crash(stage):
        if stage=='create_intent_committed': raise RuntimeError('synthetic crash')
    monkeypatch.setattr(core,'_fault',crash)
    with pytest.raises(RuntimeError): start(case)
    assert hub.inspect()['tasks'][0]['state']=='CREATE_UNKNOWN'
    hub.dispatch_next(host)
    assert not any(c[0]=='create' for c in host.calls)


def test_production_adapter_has_no_default_unrestricted_create(case):
    hub,host=case
    port=CodexAppSessions(lambda *a: pytest.fail('must not call native tools'))
    assert port.scoped_session_gap(None,None)=='BLOCKED_DESKTOP_ROLE_TOOL_BINDING_NOT_EXPOSED'
    with pytest.raises(ContractError,match='BLOCKED_DESKTOP_ROLE_TOOL_BINDING_NOT_EXPOSED'):
        port.create_thread('host',{}, {},'request')
    host.gap=port.scoped_session_gap(None,None)
    assert start(case)['state']=='HOST_BLOCKED'
    assert not any(c[0]=='create' for c in host.calls)


def test_adapter_request_mapping_preserves_fixed_profile_and_project(case):
    hub,host=case; t=start(case)
    spec=CodexAppSessions.creation_spec(host.project_id,t,hub.roles[t['role_id']],t['request_id'])
    assert spec['args']['target']['projectId']==host.project_id
    assert spec['args']['model']==PROFILE['model'] and spec['args']['thinking']==PROFILE['reasoning_effort']
    assert spec['dispatch_allowed'] is False and 'role' not in spec['args']


def test_adapter_user_text_cannot_authenticate_main():
    port=CodexAppSessions(lambda *a:None)
    with pytest.raises(ContractError,match='HOST_CALLER_CONTEXT_NOT_EXPOSED'):
        port.check_caller(MAIN,'host-project-1')
    with pytest.raises(ContractError,match='DIRECT_USER_AUTHORIZATION_REQUIRED'):
        port.check_authorization(AUTH,'create_sessions')


def test_adapter_does_not_count_user_message_as_result():
    raw={'thread':{'id':'t','hostId':'h'},'turns':[{'status':'completed','items':[
        {'type':'userMessage','phase':'final_answer','text':'{}'}]}]}
    port=CodexAppSessions(lambda *a:raw)
    with pytest.raises(ContractError,match='RESULT_FINAL_UNAVAILABLE'):
        port.read_result({'thread_id':'t','host_id':'h'})


def test_adapter_read_metadata_does_not_prove_visibility_or_role():
    raw={'thread':{'id':'t','hostId':'h','title':'Named','projectId':'p'}}
    port=CodexAppSessions(lambda *a:raw)
    observed=port.observe({'thread_id':'t','host_id':'h'})
    assert observed['title']=='Named' and observed['role_definition_digest']=='NOT_EXPOSED'
    assert observed['visible_in_target_client']==observed['user_can_ask_scoped_question']=='NOT_TESTED'


def test_same_named_other_project_cannot_collect_or_dispatch(case,tmp_path):
    hub,host=case; t=start(case)
    project.create_research_project(tmp_path/'other','Other project')
    other=core.SessionHub(project.open_existing_for_explicit_write(tmp_path/'other'),hub.roles)
    other_host=Host(); other_host.project_id='host-project-other'
    other.onboard(other_host,MAIN,other_host.project_id,'SP-invopt',PROFILE,ANALYSIS,AUTH)
    assert other.inspect()['project_id']!=hub.inspect()['project_id']
    with pytest.raises(ContractError,match='CALLER_MISMATCH'):
        other.decide(host,'wrong-project','same title is not identity',[task()])
    assert other.inspect()['tasks']==[]


def test_recorded_task_snapshot_tamper_is_not_hot_update(case):
    hub,host=case; start(case)
    path=hub.project._root/core.FILE
    state=json.loads(path.read_bytes()); state['tasks'][0]['purpose']='new work'
    path.write_bytes(core.canonical_json(state))
    with pytest.raises(ContractError,match='ROLE_OR_PROFILE_CHANGED'): hub.inspect()


def test_after_create_commit_crash_keeps_known_ref(case,monkeypatch):
    hub,host=case
    def crash(stage):
        if stage=='created_committed': raise RuntimeError('synthetic crash')
    monkeypatch.setattr(core,'_fault',crash)
    state=start(case)
    assert state['thread_ref'] is not None
    hub.dispatch_next(host)
    assert len([c for c in host.calls if c[0]=='create'])==1


def test_duplicate_collection_cannot_reset_delivered_result(case):
    hub,host=case; t=start(case); result_for(host,t)
    hub.collect(host,'one')
    hub.collect(host,'one'); hub.return_result(host,'one')
    assert len([c for c in host.calls if c[0]=='return'])==1
    assert hub.inspect()['tasks'][0]['state']=='DELIVERED'


def test_native_capability_gap_not_confused_with_desktop_role_gap():
    from aegiscae.interfaces.codex_sessions import capability_map
    m=capability_map()
    assert m['native_subagent']['role_selector']=='SOURCE_VERIFIED'
    assert m['native_subagent']['user_scoped_question']=='NOT_TESTED'
    assert m['create_thread']['production_gate']=='BLOCKED_DESKTOP_ROLE_TOOL_BINDING_NOT_EXPOSED'
