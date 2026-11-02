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
    evidence = {'schema': 'd7-original-af-expired-empty-v1', 'binding': binding, 'plan': plan,
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


def test_preparation_entry_crash_retry_uses_one_inert_plan(case, monkeypatch):
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
    class Product:
        def __init__(self, path): self.path = path
        @classmethod
        def create(cls, path, name):
            path.mkdir()
            calls.append('create')
            return cls(path)
        def prepare_real(self, **args):
            calls.append('prepare')
            assert args['candidate_id'] == before['candidates']['A']['candidate_id']
            assert args['local_contract']['runtime'] == runtime
            data['preflight']['research_contract']['request_nonce'] = args['request_nonce']
            data['preflight']['expires_at'] = args['expires_at']
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
    def fault(stage):
        if stage == 'after_commit': raise RuntimeError('injected')
    monkeypatch.setattr(local, '_fault', fault)
    with pytest.raises(RuntimeError):
        recovery.prepare_expired_a(root, old_source, runtime, config, expires)
    monkeypatch.setattr(local, '_fault', lambda stage: None)
    result = recovery.prepare_expired_a(root, old_source, runtime, config, expires)
    assert result['replayed'] and result['budget']['held'] == 1
    assert calls == ['create', 'prepare']
    assert (root / 'd7-v2.json').read_bytes() == frozen


@pytest.mark.parametrize('nonzero', [None, *recovery.ZERO_TABLES])
def test_original_reader_uses_one_transaction_and_rejects_side_effects(case, monkeypatch, nonzero):
    import sqlite3
    import sys
    from contextlib import contextmanager
    from types import SimpleNamespace
    _, data, before, _ = case
    conn = sqlite3.connect(':memory:')
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
                recovery.read_expired_evidence('SYNTHETIC', binding)
        else:
            result = recovery.read_expired_evidence('SYNTHETIC', binding)
            assert result['counts'] == dict.fromkeys(recovery.ZERO_TABLES, 0)
    finally:
        conn.close()
