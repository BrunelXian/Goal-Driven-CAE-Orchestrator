"""Developer-only synthetic reducer tests; no AF preparation or authority."""
import copy
import shutil
from pathlib import Path

import pytest

from aegiscae.contracts.research_contracts import ContractError, digest_bytes
from aegiscae.research import rod_expired_recovery as recovery
from aegiscae.research import rod_local_project as local
from aegiscae.research import project
from aegiscae.research.rod_evidence import af_digest
from test_d6_a_only import fixture_preflight


@pytest.fixture
def case(tmp_path, monkeypatch):
    # Restore the reviewed pre-change adapter statements, not scientific code.
    source = Path(local.__file__).resolve().parents[1]
    old = tmp_path / 'old-source'
    shutil.copytree(source, old, ignore=shutil.ignore_patterns('__pycache__'))
    (old / recovery.ADDITION).unlink()
    body = (old / recovery.PROJECT).read_text()
    body = body.replace('            from aegiscae.research.rod_expired_recovery import execution_candidate\n'
                        '            item = execution_candidate(state, phase)',
                        "            item = state['candidates'][phase]")
    (old / recovery.PROJECT).write_text(body)
    current = local.code_digest()
    old_digest = recovery.inventory_digest(recovery.inventory(old))
    runtime = dict(gd=old_digest, af=digest_bytes(b'af'), plugin=digest_bytes(b'plugin'),
                   python=digest_bytes(b'python'), versions={'test': 'synthetic-v1'})
    monkeypatch.setattr(local, 'code_digest', lambda: old_digest)
    research = local.create_local_research(tmp_path / 'research', 'Expired synthetic', runtime)
    binding, raw = fixture_preflight(research)
    raw['local_contract'] = research.inspect()['candidates']['A']['local_contract']
    raw['expires_at'] = 1
    plan = {'plan_id': binding['plan_id'], 'project_instance_id': binding['project_instance_id'],
            'expires_at': 1, 'rod_contract': {'local_contract': raw['local_contract']}}
    plan['plan_digest'] = af_digest(plan)
    raw['plan_digest'] = binding['plan_digest'] = plan['plan_digest']
    research._record('HOLD', dict(phase='A', binding=binding, preflight=raw), 3, 'old-hold')
    monkeypatch.setattr(local, 'code_digest', lambda: current)
    state = research.inspect()
    new_runtime = {**runtime, 'gd': current}
    compatibility = recovery.build_compatibility(state, old, new_runtime)
    new_binding, preflight = copy.deepcopy(binding), copy.deepcopy(raw)
    for k in ('project_id', 'project_instance_id', 'plan_id', 'request_key', 'request_nonce'):
        new_binding[k] += '_new'
    new_binding['plan_digest'] = digest_bytes(b'new-plan')
    preflight['engineering'] = preflight['engineering'].replace('SyntheticD6', 'SyntheticRecovery')
    preflight['input_path'] = preflight['input_path'].replace('SyntheticD6', 'SyntheticRecovery')
    preflight['scratch'] = preflight['scratch'].replace('SyntheticD6', 'SyntheticRecovery')
    for out in preflight['declared_outputs']:
        out['path'] = out['path'].replace('SyntheticD6', 'SyntheticRecovery')
    new_binding['output_identity'] = af_digest({'cwd': preflight['engineering'].casefold(),
                                               'job': 'rod_' + 'a' * 32})
    preflight.update({k: new_binding[k] for k in ('project_id','project_instance_id','plan_id','plan_digest')})
    preflight['output_key'] = new_binding['output_identity']
    preflight['research_contract']['request_nonce'] = new_binding['request_nonce']
    preflight['expires_at'] = 9999999999
    preflight['local_contract'] = recovery.execution_candidate({**state, 'compatibility': compatibility}, 'A')['local_contract']
    evidence = {'schema': recovery.PROOF_SCHEMA, 'binding': binding, 'plan': plan,
                'supervisor_started': '0', 'owner_start_markers': [],
                'counts': dict.fromkeys(recovery.ZERO_TABLES, 0), 'observed_at': 2, 'gate': 'PAUSED', 'slot': None}
    data = dict(phase='A', compatibility=compatibility, nonexecution=evidence,
                binding=new_binding, preflight=preflight)
    return research, data, state, old


def test_atomic_rebind_preserves_frozen_candidate_history_and_replay(case):
    research, data, before, _ = case
    result = research._record('REBIND_EXPIRED_A', data, 4, 'recover')
    assert result['budget'] == before['budget']
    assert result['candidates'] == before['candidates']
    assert result['policy'] == before['policy']
    assert result['contract_digest'] == before['contract_digest']
    assert result['retired_attempts'][0]['binding'] == before['attempts']['A']['binding']
    assert result['retired_attempts'][0]['status'] == 'EXPIRED_UNEXECUTED'
    assert research._record('REBIND_EXPIRED_A', data, 4, 'recover')['replayed']
    assert research.hold('A', None, before['attempts']['A']['binding'], 3, 'old-hold')['replayed']
    reopened = local.LocalRodProject(project.open_existing_readonly(research.project._root))
    assert reopened.inspect()['budget']['held'] == 1
    research.intent('A', 5, 'new-intent')
    assert research.inspect()['attempts']['A']['status'] == 'INTENT'


@pytest.mark.parametrize('table', recovery.ZERO_TABLES)
def test_nonzero_original_evidence_rejected(case, table):
    research, data, before, _ = case
    data['nonexecution']['counts'][table] = 1
    with pytest.raises(ContractError, match='NONEXECUTION_UNPROVEN'):
        research._record('REBIND_EXPIRED_A', data, 4, 'recover')
    assert research.inspect() == before


@pytest.mark.parametrize('status', ['INTENT', 'UNKNOWN', 'ACCEPTED', 'DENIED', 'ADMITTED'])
def test_pending_or_terminal_state_cannot_recover(case, status):
    research, data, before, _ = case
    before['attempts']['A']['status'] = status
    with research.project._snapshot() as (_, meta, bundles, events):
        bundle, _ = research._read(meta, bundles, events)
    payload = dict(schema_version=local.VERSION, action='REBIND_EXPIRED_A', key='recover',
                   before_project_revision=4, data=data)
    with pytest.raises(ContractError, match='RECOVERY_NOT_AVAILABLE'):
        recovery.reduce_event(before, payload, bundle, 4, before['contract_digest'])


@pytest.mark.parametrize('field', ['plan_id','plan_digest','project_id','project_instance_id',
                                   'request_key','request_nonce','output_identity'])
def test_old_execution_identity_never_reused(case, field):
    research, data, before, _ = case
    data['binding'][field] = before['attempts']['A']['binding'][field]
    with pytest.raises(ContractError, match='AF_IDENTITY_REUSED'):
        research._record('REBIND_EXPIRED_A', data, 4, 'recover')


@pytest.mark.parametrize('damage', ['unexpired', 'new_expired', 'ast', 'contract', 'validator', 'source'])
def test_incomplete_or_incompatible_proof_fails(case, damage):
    research, data, before, _ = case
    if damage == 'unexpired': data['nonexecution']['observed_at'] = 1
    if damage == 'new_expired': data['preflight']['expires_at'] = 1
    if damage == 'ast': data['compatibility']['equivalence']['new_acceptance'] = digest_bytes(b'changed')
    if damage == 'contract': data['compatibility']['contract_digest'] = digest_bytes(b'changed')
    if damage == 'validator': data['compatibility']['new_validator']['sha256'] = before['policy']['runtime']['gd']
    if damage == 'source': data['compatibility']['old_sources']['research/rod_local_verify.py'] = digest_bytes(b'changed')
    with pytest.raises(ContractError):
        research._record('REBIND_EXPIRED_A', data, 4, 'recover')
    assert research.inspect() == before


def test_scientific_projection_detects_numeric_rule_change():
    body = Path(local.__file__).read_text()
    assert recovery.scientific_projection(body) != recovery.scientific_projection(body.replace("Decimal('0.019')", "Decimal('0.018')"))


def test_commit_failure_rolls_back(case, monkeypatch):
    research, data, before, _ = case
    def fault(stage):
        if stage == 'before_commit': raise RuntimeError('injected')
    monkeypatch.setattr(local, '_fault', fault)
    with pytest.raises(RuntimeError):
        research._record('REBIND_EXPIRED_A', data, 4, 'recover')
    assert research.inspect() == before


def test_unapproved_code_change_still_blocked(case, monkeypatch):
    research, _, _, _ = case
    monkeypatch.setattr(local, 'code_digest', lambda: digest_bytes(b'unreviewed'))
    with pytest.raises(ContractError, match='WORKFLOW_CODE_CHANGED'):
        research.intent('A', 4, 'intent')


def test_after_commit_crash_replays_once(case, monkeypatch):
    research, data, _, _ = case
    def fault(stage):
        if stage == 'after_commit': raise RuntimeError('injected')
    monkeypatch.setattr(local, '_fault', fault)
    with pytest.raises(RuntimeError):
        research._record('REBIND_EXPIRED_A', data, 4, 'recover')
    monkeypatch.setattr(local, '_fault', lambda stage: None)
    result = research._record('REBIND_EXPIRED_A', data, 4, 'recover')
    assert result['replayed'] and result['budget']['held'] == 1
    assert len(result['retired_attempts']) == 1


def test_second_recovery_and_stale_revision_rejected(case):
    research, data, before, _ = case
    with pytest.raises(ContractError, match='REVISION_CONFLICT'):
        research._record('REBIND_EXPIRED_A', data, 3, 'recover')
    assert research.inspect() == before
    research._record('REBIND_EXPIRED_A', data, 4, 'recover')
    with pytest.raises(ContractError, match='RECOVERY_NOT_AVAILABLE'):
        research._record('REBIND_EXPIRED_A', data, 5, 'recover-again')


@pytest.mark.parametrize('failure', ['before_commit', 'after_commit', 'after_prepare'])
def test_preparation_entry_crash_retry_uses_one_inert_plan(case, monkeypatch, failure):
    import json
    import sys
    from types import SimpleNamespace
    from aegiscae.research import rod_local_port
    research, data, before, old_source = case
    root = research.project._root.parent
    workspace = {'schema': 'gdcae-d7-workspace-v1', 'runtime': before['policy']['runtime'],
                 'research_project_id': before['research_project_id'],
                 'contract_digest': before['contract_digest']}
    frozen = json.dumps(workspace).encode()
    (root / 'd7-v2.json').write_bytes(frozen)
    runtime = data['compatibility']['new_runtime']
    calls = []
    prepared = []
    failed = []
    class Product:
        def __init__(self, path): self.path = path
        @classmethod
        def create(cls, path, name):
            path.mkdir()
            (path / 'private').mkdir()
            calls.append('create')
            return cls(path)
        def prepare_real(self, **args):
            calls.append('prepare')
            if prepared:
                assert prepared[0] == args
            else:
                prepared.append(copy.deepcopy(args))
            assert args['candidate_id'] == before['candidates']['A']['candidate_id']
            assert args['local_contract']['runtime'] == runtime
            data['preflight']['research_contract']['request_nonce'] = args['request_nonce']
            data['preflight']['expires_at'] = args['expires_at']
            if failure == 'after_prepare' and not failed:
                failed.append(True)
                raise RuntimeError('injected')
            return {**{k: data['binding'][k] for k in
                    ('project_id', 'project_instance_id', 'plan_id', 'plan_digest', 'backend_id')},
                    'resources': data['preflight']['resources'],
                    'output_key': data['binding']['output_identity']}
    class Port:
        def __init__(self, *args): pass
        def validate(self, value): assert value == runtime
        def preflight_real(self, **kwargs): return copy.deepcopy(data['preflight'])
    monkeypatch.setattr(rod_local_port, 'LocalReadPort', Port)
    monkeypatch.setitem(sys.modules, 'abqjobpilot.product_rod', SimpleNamespace(RodProduct=Product))
    monkeypatch.setitem(sys.modules, 'abqjobpilot.execution.models', SimpleNamespace(digest=af_digest))
    monkeypatch.setitem(sys.modules, 'abqjobpilot.execution.rod_local_hil',
                        SimpleNamespace(check_runtime=lambda config, value: None))
    monkeypatch.setattr(recovery, 'read_expired_evidence', lambda *args: data['nonexecution'])
    config = SimpleNamespace(value=lambda: {'research_runtime': runtime})
    expires = int(recovery.time.time()) + 300
    assessed = recovery.assess_expired_a(root, old_source, runtime)
    assert assessed['budget'] == before['budget'] and calls == []
    assert assessed['compatibility'] == data['compatibility']
    assert not (root / 'expired-a-recovery-v2').exists()
    legacy = root / 'expired-a-recovery-v1'
    legacy.mkdir()
    with pytest.raises(ContractError, match='LEGACY_RECOVERY_RECONCILIATION_REQUIRED'):
        recovery.prepare_expired_a(root, old_source, runtime, config, expires)
    legacy.rmdir()
    incomplete = root / 'expired-a-recovery-v2'
    incomplete.mkdir()
    with pytest.raises(ContractError, match='IDEMPOTENCY_CONFLICT'):
        recovery.prepare_expired_a(root, old_source, runtime, config, expires)
    incomplete.rmdir()
    assert calls == []
    def fault(stage):
        if stage == failure: raise RuntimeError('injected')
    monkeypatch.setattr(local, '_fault', fault)
    with pytest.raises(RuntimeError):
        recovery.prepare_expired_a(root, old_source, runtime, config, expires)
    monkeypatch.setattr(local, '_fault', lambda stage: None)
    result = recovery.prepare_expired_a(root, old_source, runtime, config, expires)
    assert result['replayed'] is (failure == 'after_commit') and result['budget']['held'] == 1
    assert calls == ['create', 'prepare'] + ([] if failure == 'after_commit' else ['prepare'])
    assert len(prepared) == 1
    assert (root / 'd7-v2.json').read_bytes() == frozen
    assert recovery.prepare_expired_a(root, old_source, runtime, config, expires)['replayed']
    with pytest.raises(ContractError, match='IDEMPOTENCY_CONFLICT'):
        recovery.prepare_expired_a(root, old_source, runtime, config, expires + 1)


@pytest.mark.parametrize('nonzero', [None, *recovery.ZERO_TABLES])
def test_original_reader_uses_one_transaction_and_rejects_side_effects(case, monkeypatch, nonzero, tmp_path):
    import sqlite3
    import sys
    from contextlib import contextmanager
    from types import SimpleNamespace
    _, data, before, _ = case
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.execute('CREATE TABLE meta(key TEXT, value TEXT)')
    conn.execute("INSERT INTO meta VALUES('supervisor_started', '0')")
    af = tmp_path / 'synthetic-af'
    (af / 'private').mkdir(parents=True)
    for table in (*recovery.ZERO_TABLES, 'plans'):
        conn.execute('CREATE TABLE ' + table + '(id INTEGER)')
    conn.execute('INSERT INTO plans VALUES(1)')
    if nonzero: conn.execute('INSERT INTO ' + nonzero + ' VALUES(1)')
    conn.execute('CREATE TABLE dispatch_gate(id INTEGER, state TEXT)')
    conn.execute("INSERT INTO dispatch_gate VALUES(1, 'PAUSED')")
    conn.execute('CREATE TABLE slot(id INTEGER, run_id TEXT)')
    conn.execute('INSERT INTO slot VALUES(1, NULL)')
    conn.commit()
    @contextmanager
    def read():
        try: yield conn
        finally: conn.rollback()
    binding = before['attempts']['A']['binding']
    reader = SimpleNamespace(store=SimpleNamespace(read=read), context=SimpleNamespace(
        project_id=binding['project_id'], project_instance_id=binding['project_instance_id']))
    def document(connection, *args):
        assert connection.in_transaction
        return data['nonexecution']['plan']
    monkeypatch.setitem(sys.modules, 'abqjobpilot.product_rod', SimpleNamespace(
        RodProduct=lambda path: SimpleNamespace(_reader=lambda: reader)))
    monkeypatch.setitem(sys.modules, 'abqjobpilot.execution.store', SimpleNamespace(document=document))
    monkeypatch.setitem(sys.modules, 'abqjobpilot.execution.models', SimpleNamespace(digest=af_digest))
    try:
        if nonzero:
            with pytest.raises(ContractError, match='NONEXECUTION_UNPROVEN'):
                recovery.read_expired_evidence(af, binding)
        else:
            result = recovery.read_expired_evidence(af, binding)
            assert result['counts'] == dict.fromkeys(recovery.ZERO_TABLES, 0)
            conn.execute("UPDATE meta SET value='1'")
            conn.commit()
            with pytest.raises(ContractError, match='NONEXECUTION_UNPROVEN'):
                recovery.read_expired_evidence(af, binding)
            conn.execute('DELETE FROM meta')
            conn.commit()
            with pytest.raises(ContractError, match='NONEXECUTION_UNPROVEN'):
                recovery.read_expired_evidence(af, binding)
    finally:
        conn.close()


@pytest.mark.parametrize('marker', ['owner.json', 'private/connection.json',
                                   'private/lifecycle-current.json', 'private/start_incomplete'])
def test_owner_and_start_intent_markers_block(tmp_path, marker):
    (tmp_path / 'private').mkdir()
    recovery.require_unstarted_files(tmp_path)
    (tmp_path / marker).write_bytes(b'no sensitive content needed')
    with pytest.raises(ContractError, match='NONEXECUTION_UNPROVEN'):
        recovery.require_unstarted_files(tmp_path)


@pytest.mark.parametrize('damage', ['started', 'candidate_b', 'accepted', 'unknown'])
def test_early_eligibility_refuses_unsafe_state(case, damage):
    _, _, state, _ = case
    if damage == 'started': state['attempts']['A']['started'] = True
    if damage == 'candidate_b': state['candidates']['B'] = {}
    if damage == 'accepted': state['attempts']['A']['accepted'] = {}
    if damage == 'unknown': state['attempts']['A']['status'] = 'UNKNOWN'
    with pytest.raises(ContractError, match='RECOVERY_NOT_AVAILABLE'):
        recovery.require_eligible(state)


@pytest.mark.parametrize('damage', ['supervisor', 'markers', 'missing'])
def test_incomplete_startup_proof_refused(case, damage):
    research, data, before, _ = case
    if damage == 'supervisor': data['nonexecution']['supervisor_started'] = '1'
    if damage == 'markers': data['nonexecution']['owner_start_markers'] = ['start_intent']
    if damage == 'missing': del data['nonexecution']['supervisor_started']
    with pytest.raises(ContractError):
        research._record('REBIND_EXPIRED_A', data, 4, 'recover')
    assert research.inspect() == before


def test_legacy_recovery_replay_without_legacy_new_write(case, monkeypatch):
    research, data, _, _ = case
    data['compatibility']['version'] = recovery.LEGACY_VERSION
    data['compatibility']['new_validator']['version'] = recovery.LEGACY_VERSION
    proof = data['nonexecution']
    proof['schema'] = 'd7-original-af-expired-empty-v1'
    proof['counts'] = dict.fromkeys(recovery.LEGACY_ZERO_TABLES, 0)
    del proof['supervisor_started'], proof['owner_start_markers']
    with pytest.raises(ContractError, match='LEGACY_RECOVERY_REPLAY_ONLY'):
        research._record('REBIND_EXPIRED_A', data, 4, 'legacy')
    # Synthesize an already-recorded historical v1 event, then restore v2 writer.
    with monkeypatch.context() as legacy:
        legacy.setattr(recovery, 'VERSION', recovery.LEGACY_VERSION)
        legacy.setattr(recovery, 'PROOF_SCHEMA', proof['schema'])
        research._record('REBIND_EXPIRED_A', data, 4, 'legacy')
    assert research.inspect()['budget']['held'] == 1
    assert research._record('REBIND_EXPIRED_A', data, 4, 'legacy')['replayed']


@pytest.mark.parametrize('damage', ['runtime', 'research_project_id', 'contract_digest'])
def test_assessment_refuses_wrong_workspace_without_preparation(case, damage):
    import json
    research, data, before, old = case
    root = research.project._root.parent
    frozen = {'schema': 'gdcae-d7-workspace-v1', 'runtime': before['policy']['runtime'],
              'research_project_id': before['research_project_id'], 'contract_digest': before['contract_digest']}
    frozen[damage] = 'wrong'
    (root / 'd7-v2.json').write_text(json.dumps(frozen))
    with pytest.raises(ContractError, match='WORKSPACE_RUNTIME_MISMATCH'):
        recovery.assess_expired_a(root, old, data['compatibility']['new_runtime'])
    assert research.inspect() == before
    assert not (root / 'expired-a-recovery-v2').exists()
