"""OFFLINE ONLY: original AF stores with TEST_ONLY authority and synthetic bytes.

No Supervisor, native scope, live credential, real Grant or solver is created.
The fixture's local-contract verdict is not a report of real scientific evidence.
"""
import copy
import importlib
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from aegiscae.contracts.research_contracts import ContractError, digest_bytes
from aegiscae.research.rod_local_project import (
    LocalRodProject, causal_reference, code_digest, create_local_research,
)
from aegiscae.research.rod_output_v2 import TEMPLATE, candidate_bytes
from aegiscae.research.rod_output_dat_v2 import verify_dat
from aegiscae.research.rod_real_project import NUMERICAL_POLICY, create_real_research
from aegiscae.research import project


@pytest.fixture
def af_modules(monkeypatch):
    source = os.environ.get('GDCAE_G2_AF_SOURCE')
    assert source == 'D:/Projects/abqjobpilot_dev', 'Explicit Develop source required'
    monkeypatch.syspath_prepend(source)
    monkeypatch.syspath_prepend(str(Path(source) / 'tests'))
    helper = importlib.import_module('test_d4_rod_trusted')
    output = importlib.import_module('abqjobpilot.execution.rod_output_v2')
    from abqjobpilot.execution.managed_process import ManagedScope
    from abqjobpilot.execution.supervisor import FakeSupervisor
    def deny(*_a, **_k):
        raise AssertionError('NATIVE_OR_REAL_ISSUANCE_DENIED')
    monkeypatch.setattr(FakeSupervisor, '__init__', deny)
    monkeypatch.setattr(ManagedScope, 'create_standard', deny)
    monkeypatch.setattr(helper, 'TEMPLATE', output.TEMPLATE)
    monkeypatch.setattr(helper, 'PROFILE', output.PROFILE)
    monkeypatch.setattr(helper, 'compile_candidate', output.compile_candidate)
    original_prepare = helper.rod.prepare
    def offline_prepare(service, *args, **kwargs):
        config = service._standard_backend.config.value()
        config['research_runtime'] = kwargs['local_contract']['runtime']
        service._standard_backend.config = helper.standard.StandardConfig(helper.canonical_json(config))
        return original_prepare(service, *args, **kwargs)
    monkeypatch.setattr(helper.rod, 'prepare', offline_prepare)
    from abqjobpilot.execution import rod_local_hil
    monkeypatch.setattr(helper, 'd7_original_runtime_check', rod_local_hil.check_runtime, raising=False)
    def offline_runtime(config, runtime):
        assert config.value()['research_runtime'] == runtime
        assert rod_local_hil.source_digest() == runtime['af']
        assert runtime['versions']['test_source'] == 'SYNTHETIC_ONLY'
    monkeypatch.setattr(rod_local_hil, 'check_runtime', offline_runtime)
    from abqjobpilot.execution import rod_local_read
    monkeypatch.setattr(helper, 'd7_real_grant_check', rod_local_read.check_accepted_grant, raising=False)
    def test_grant_only(grant, plan, run, receipt):
        assert grant['grant_kind'] == 'TEST_ONLY' and grant['issuer'] == 'FakeGrantFixture'
        assert grant['plan_digest'] == plan['plan_digest'] == run['plan_digest']
    monkeypatch.setattr(rod_local_read, 'check_accepted_grant', test_grant_only)
    return helper, output


def synthetic_dat(helper, force='1'):
    """Transform authored fixture layout only, never read historical real DAT."""
    from decimal import Decimal
    value = helper.complete_dat().decode('cp936')
    lines = value.splitlines()
    u = next(i for i, s in enumerate(lines) if 'NODE' in s and 'U1' in s and 'RF1' not in s)
    rf = next(i for i, s in enumerate(lines) if 'NODE' in s and 'RF1' in s)
    end = rf + 2
    while end < len(lines) and not lines[end].strip():
        end += 1
    while end < len(lines) and lines[end].strip():
        end += 1
    start = u-1
    while not lines[start].strip():
        start -= 1
    new = ['THE FOLLOWING TABLE IS PRINTED FOR NODES BELONGING TO NODE SET', 'VERIFY',
           'NODE FOOT- U1 U2 U3 RF1 RF2 RF3', 'NOTE', '',
           f'1 0 0 0 -{force} 0 0', f'2 {Decimal(force)/100} 0 0 0 0 0', '']
    result = lines[:start] + new + lines[end:]
    stress = next(i for i, s in enumerate(result) if 'ELEMENT' in s and 'S11' in s)+2
    while not result[stress].strip():
        stress += 1
    result[stress] = f'1 1 {force}'
    return ('\n'.join(result)+'\n').encode('cp936')


@pytest.fixture
def research(tmp_path, af_modules):
    from abqjobpilot.execution.rod_local_hil import source_digest
    runtime = {'gd': code_digest(), 'af': source_digest(),
        'plugin': digest_bytes(b'OFFLINE_PLUGIN'), 'python': digest_bytes(b'OFFLINE_PYTHON'),
        'versions': {'python': '3.12.10', 'test_source': 'SYNTHETIC_ONLY'}}
    return create_local_research(tmp_path/'research', 'D7 R1 SYNTHETIC ONLY', runtime)


def make_case(tmp_path, monkeypatch, af_modules, research, phase):
    helper, _output = af_modules
    view = research.inspect()
    candidate = view['candidates'][phase]
    # Original helper is fixed to 1 N; override only its pure compiler scalar.
    from abqjobpilot.execution.rod_output_v2 import compile_candidate
    monkeypatch.setattr(helper, 'compile_candidate', lambda template, _load: compile_candidate(template, candidate['load_n']))
    target = tmp_path/phase
    target.mkdir()
    args = {'research_project_id': view['research_project_id'], 'contract_digest': view['contract_digest'],
        'research_revision': candidate['admitted_revision'], 'candidate_id': candidate['candidate_id'],
        'request_nonce': 'nonce_'+phase, 'phase': phase, 'local_contract': candidate['local_contract']}
    generator = helper.make_case(target, monkeypatch, args)
    case = next(generator)
    from abqjobpilot.execution.product_standard import ProductStandardControl
    from abqjobpilot.execution.models import digest
    case.service.product_control = ProductStandardControl({'plan_id': case.plan['plan_id'],
        'plan_digest': case.plan['plan_digest'], 'operator_digest': digest(case.token),
        'local_policy_digest': digest(candidate['local_contract'])})
    binding = {'project_id': case.context.project_id, 'project_instance_id': case.context.project_instance_id,
        'plan_id': case.plan['plan_id'], 'plan_digest': case.plan['plan_digest'],
        'input_digest': candidate['input_digest'], 'resources_digest': digest(case.plan['resources']),
        'output_identity': case.plan['output_key'], 'candidate_output_identity': candidate['output_identity'],
        'request_key': 'request_'+phase, 'request_nonce': 'nonce_'+phase, 'backend_id': case.plan['backend_id']}
    from abqjobpilot.execution import rod_trusted, rod_local_read
    class Port:
        def preflight_real(self, **kwargs):
            return rod_trusted.preflight(case.service, case.context, **kwargs)
        def read_started(self, **kwargs):
            return rod_local_read.started(case.service, **kwargs)
        def read_denial(self, **kwargs):
            return rod_local_read.denial(case.service, **kwargs)
        def read_acceptance(self, **kwargs):
            return rod_local_read.acceptance(case.service, **kwargs)
        def read_real_artifacts(self, **kwargs):
            return rod_trusted.acquire(case.service, case.context, include_completion_artifacts=True, **kwargs)
    from aegiscae.research.rod_local_port import LocalReadPort
    stub = Port()
    port = object.__new__(LocalReadPort)
    # Private test-only substitution; production requires exact pinned LocalReadPort.
    monkeypatch.setattr(LocalReadPort, 'validate', lambda self, runtime: None)
    for name in ('preflight_real', 'read_acceptance', 'read_started', 'read_denial', 'read_real_artifacts'):
        setattr(port, name, getattr(stub, name))
    return case, binding, port, generator


def review(case, choice='APPROVE_EXACT', key='review'):
    from abqjobpilot.execution.product_standard import scope
    from abqjobpilot.execution.models import digest, now
    return case.service.product_control.invoke(case.service, {'action': 'review_a',
        'owner_id': case.store._session.owner_id, 'operation_key': key, 'operator_token': case.token,
        'arguments': {'plan_id': case.plan['plan_id'], 'plan_digest': case.plan['plan_digest'],
            'scope_digest': digest(scope(case.plan)), 'decision': choice, 'nonce': case.plan['rod_contract']['request_nonce'],
            'not_before': now()-1, 'expires_at': now()+120}})


def execute_fixture(case, helper, monkeypatch, binding, load):
    review(case)
    grant = helper.fake_authority(case, monkeypatch)
    request = helper.request(case, grant, key=binding['request_key'])
    accepted = case.service.submit(case.context, request)
    helper.arm(case, accepted['receipt']['run_id'])
    monkeypatch.setattr(helper, 'DAT', synthetic_dat(helper, load))
    monkeypatch.setattr(case.service._standard_backend, 'execute', helper.synthetic_runner)
    return accepted


def test_output_and_legacy_replay(af_modules, tmp_path):
    helper, output = af_modules
    assert output.TEMPLATE == TEMPLATE
    assert b'*NSET, NSET=VERIFY\n1,2\n' in TEMPLATE
    assert b'U1,U2,U3,RF1,RF2,RF3\n' in TEMPLATE
    for load in ('0.5', '1', '2', '2.5'):
        assert output.compile_candidate(TEMPLATE, load).input_bytes == candidate_bytes(load)
        raw = synthetic_dat(helper, load)
        assert verify_dat(raw, load, NUMERICAL_POLICY)['analytical_crosscheck'] == 'PASS'
        from abqjobpilot.execution.rod_output_dat_v2 import parse
        assert parse(raw, load)['full_frozen_checks'] == 'PASS'
    old = create_real_research(tmp_path/'legacy', 'legacy')
    assert project.open_existing_readonly(tmp_path/'legacy').inspect()['research_project_id'] == old.inspect()['research_project_id']


@pytest.mark.parametrize('corruption', ['missing', 'duplicate', 'zero', 'wrong_set', 'nan', 'force', 'tail'])
def test_output_rejects(af_modules, corruption):
    helper, _ = af_modules
    raw = synthetic_dat(helper)
    replacements = {'missing': (b'1 0 0 0 -1 0 0\n', b''),
        'duplicate': (b'1 0 0 0 -1 0 0\n', b'1 0 0 0 -1 0 0\n1 0 0 0 -1 0 0\n'),
        'zero': (b'1 0 0 0 -1 0 0', b'1 1 0 0 -1 0 0'), 'wrong_set': (b'VERIFY', b'OTHER'),
        'nan': (b'2 0.01', b'2 NaN'), 'force': (b'-1 0 0', b'-2 0 0'), 'tail': (b'JOB TIME SUMMARY', b'BAD FOOTER')}
    raw = raw.replace(*replacements[corruption])
    with pytest.raises(ContractError):
        verify_dat(raw, '1', NUMERICAL_POLICY)
    from abqjobpilot.execution.rod_output_dat_v2 import parse
    assert parse(raw, '1')['numerical'] != 'PRIMARY_THREE_PASS'


def test_two_projects_offline_accept_budget_and_b(tmp_path, monkeypatch, af_modules, research):
    helper, _ = af_modules
    generators = []
    try:
        for phase, load in [('A', '1'), ('B', '2')]:
            case, binding, port, generator = make_case(tmp_path, monkeypatch, af_modules, research, phase)
            generators.append(generator)
            before = research.inspect()['project_revision']
            research.hold(phase, port, binding, before, 'hold_'+phase)
            assert research.hold(phase, port, binding, before, 'hold_'+phase)['replayed']
            research.intent(phase, before+1, 'intent_'+phase)
            accepted = execute_fixture(case, helper, monkeypatch, binding, load)
            research.unknown(phase, before+2, 'unknown_'+phase)
            assert research.inspect()['budget']['held'] == 1
            research.read_event(phase, port, 'ACCEPTED', before+3, 'accepted_'+phase)
            assert research.inspect()['budget']['held'] == 0
            assert research.inspect()['budget']['charged'] == (1 if phase == 'A' else 2)
            assert research.inspect()['budget']['started'] == (0 if phase == 'A' else 1)
            case.service.execute_pending(case.context, accepted['receipt']['run_id'])
            state = research.read_event(phase, port, 'OBSERVE', before+4, 'observe_'+phase)
            assert state['attempts'][phase]['decision']['V2'] == 'PASS'
            if phase == 'A':
                assert state['attempts']['A']['decision']['V3'] == 'NOT_MET'
                with pytest.raises(ContractError):
                    research.propose_b('2', {}, state['project_revision'], 'early_b')
                # Explicit synthetic lifecycle receipt via the original lifecycle API;
                # no Owner process or native stop is executed.
                from abqjobpilot.execution.lifecycle import LifecycleControl
                from abqjobpilot.execution.models import digest
                lifecycle = LifecycleControl(digest('OFFLINE_STOP'), 'offline_start',
                    standard_binding=case.service.product_control.binding)
                stop = lifecycle.stop(case.service, {'owner_id': case.store._session.owner_id,
                    'operation_key': 'stop_a', 'operator_token': 'OFFLINE_STOP'})
                from abqjobpilot.execution.rod_local_read import orderly_stop
                manager = SimpleNamespace(_current=lambda: {}, _stopped=lambda _c: {'receipt': stop['receipt']})
                port.read_orderly_stop = lambda **kw: orderly_stop(case.service, manager, **kw)
                state = research.read_event('A', port, 'OWNER_STOP', state['project_revision'], 'stop_a')
                b = research.propose_b('2', causal_reference(state), state['project_revision'], 'propose_b')
                assert b['candidates']['B']['admitted_revision'] == b['project_revision'] != 3
            else:
                assert state['attempts']['B']['decision']['V3'] == 'SATISFIED'
                assert state['budget'] == {'limit': 2, 'held': 0, 'charged': 2, 'available': 0, 'started': 2}
        reopened = LocalRodProject(project.open_existing_for_explicit_write(research.project._root))
        assert reopened.inspect() == research.inspect()
    finally:
        for generator in generators:
            generator.close()


def test_deny_terminal_and_missing_capability(tmp_path, monkeypatch, af_modules, research):
    case, _binding, _port, generator = make_case(tmp_path, monkeypatch, af_modules, research, 'A')
    try:
        review(case, 'DENY_TERMINAL')
        from abqjobpilot.execution.models import ExecutionError
        with pytest.raises(ExecutionError) as error:
            review(case, 'APPROVE_EXACT', 'new_key')
        assert error.value.code == 'HIL_DECISION_FINAL'
        from abqjobpilot.execution.rod_local_hil import require_decision
        with case.store.read() as conn, pytest.raises(ExecutionError):
            require_decision(case.service, conn, case.plan, case.service.product_control.binding)
        with case.store.read() as conn:
            assert conn.execute('SELECT COUNT(*) FROM grants').fetchone()[0] == 0
    finally:
        generator.close()


def test_model_and_revision_rejects(tmp_path, monkeypatch, af_modules, research):
    case, binding, port, generator = make_case(tmp_path, monkeypatch, af_modules, research, 'A')
    try:
        with pytest.raises(ContractError):
            research.hold('A', port, binding, 2, 'stale')
        research.hold('A', port, binding, 3, 'hold_a')
        other = copy.deepcopy(binding)
        other['request_key'] = 'different'
        with pytest.raises(ContractError, match='IDEMPOTENCY_CONFLICT'):
            research.hold('A', port, other, 3, 'hold_a')
        with pytest.raises(ContractError):
            research.hold('A', port, binding, 4, 'new_key')
        with pytest.raises(ContractError):
            research.propose_b('2', {}, 4, 'b')
    finally:
        generator.close()


@pytest.mark.parametrize('stage', ['before_commit', 'after_commit'])
def test_hold_interruption_replay(tmp_path, monkeypatch, af_modules, research, stage):
    from aegiscae.research import rod_local_project as module
    case, binding, port, generator = make_case(tmp_path, monkeypatch, af_modules, research, 'A')
    try:
        def fault(point):
            if point == stage:
                raise OSError('OFFLINE_INTERRUPTION')
        monkeypatch.setattr(module, '_fault', fault)
        with pytest.raises(project.ProjectError, match="STORE_UNAVAILABLE"):
            research.hold('A', port, binding, 3, 'hold_a')
        monkeypatch.setattr(module, '_fault', lambda _stage: None)
        result = research.hold('A', port, binding, 3, 'hold_a')
        assert result['replayed'] == (stage == 'after_commit')
        assert result['budget']['held'] == 1 and result['project_revision'] == 4
    finally:
        generator.close()


def test_competing_holds_one_attempt(tmp_path, monkeypatch, af_modules, research):
    from concurrent.futures import ThreadPoolExecutor
    _case, binding, port, generator = make_case(tmp_path, monkeypatch, af_modules, research, 'A')
    try:
        def hold(key):
            try:
                research.hold('A', port, binding, 3, key)
                return 'COMMITTED'
            except ContractError:
                return 'REJECTED'
        with ThreadPoolExecutor(2) as pool:
            assert sorted(pool.map(hold, ('one', 'two'))) == ['COMMITTED', 'REJECTED']
        assert research.inspect()['budget'] == {'limit': 2, 'held': 1, 'charged': 0, 'available': 1, 'started': 0}
    finally:
        generator.close()


@pytest.mark.parametrize('with_intent', [False, True])
def test_denial_release_only_before_intent(tmp_path, monkeypatch, af_modules, research, with_intent):
    case, binding, port, generator = make_case(tmp_path, monkeypatch, af_modules, research, 'A')
    try:
        research.hold('A', port, binding, 3, 'hold_a')
        if with_intent:
            research.intent('A', 4, 'intent_a')
        review(case, 'DENY_TERMINAL')
        if with_intent:
            with pytest.raises(ContractError):
                research.read_event('A', port, 'DENIED', 5, 'deny')
            assert research.inspect()['budget']['held'] == 1
        else:
            state = research.read_event('A', port, 'DENIED', 4, 'deny')
            assert state['budget']['available'] == 2 and state['budget']['held'] == 0
            with pytest.raises(ContractError):
                research.hold('A', port, binding, 5, 'new_key')
    finally:
        generator.close()


def test_unknown_no_receipt_and_started_separate(tmp_path, monkeypatch, af_modules, research):
    helper, _ = af_modules
    case, binding, port, generator = make_case(tmp_path, monkeypatch, af_modules, research, 'A')
    try:
        from abqjobpilot.execution.models import ExecutionError
        research.hold('A', port, binding, 3, 'hold_a')
        research.intent('A', 4, 'intent_a')
        research.unknown('A', 5, 'unknown_a')
        with pytest.raises(ExecutionError):
            research.read_event('A', port, 'ACCEPTED', 6, 'absent')
        assert research.inspect()['budget']['held'] == 1
        accepted = execute_fixture(case, helper, monkeypatch, binding, '1')
        research.read_event('A', port, 'ACCEPTED', 6, 'accepted')
        with pytest.raises(ExecutionError):
            research.read_event('A', port, 'STARTED', 7, 'premature')
        assert research.inspect()['budget']['charged'] == 1 and research.inspect()['budget']['started'] == 0
        case.service.execute_pending(case.context, accepted['receipt']['run_id'])
        state = research.read_event('A', port, 'STARTED', 7, 'started')
        assert state['budget']['started'] == 1 and state['budget']['charged'] == 1
        assert research.read_event('A', port, 'STARTED', 7, 'started')['replayed']
    finally:
        generator.close()


@pytest.mark.parametrize('field', ['run_id', 'plan_digest', 'simulation'])
def test_wrong_acceptance_does_not_charge(tmp_path, monkeypatch, af_modules, research, field):
    helper, _ = af_modules
    case, binding, port, generator = make_case(tmp_path, monkeypatch, af_modules, research, 'A')
    try:
        research.hold('A', port, binding, 3, 'hold_a')
        research.intent('A', 4, 'intent_a')
        execute_fixture(case, helper, monkeypatch, binding, '1')
        raw = port.read_acceptance(plan_id=binding['plan_id'], expected_plan_digest=binding['plan_digest'],
                                   request_key=binding['request_key'])
        raw['run'][field] = True if field == 'simulation' else 'mismatched'
        monkeypatch.setattr(port, 'read_acceptance', lambda **_kw: raw)
        with pytest.raises(ContractError):
            research.read_event('A', port, 'ACCEPTED', 5, 'corrupt')
        assert research.inspect()['budget']['held'] == 1 and research.inspect()['budget']['charged'] == 0
    finally:
        generator.close()


def test_duck_port_and_mutation_refused(tmp_path, monkeypatch, af_modules, research):
    case, binding, _port, generator = make_case(tmp_path, monkeypatch, af_modules, research, 'A')
    try:
        with pytest.raises(ContractError, match='READ_PORT_UNQUALIFIED'):
            research.hold('A', SimpleNamespace(), binding, 3, 'bad_port')
        from abqjobpilot.execution.rod_trusted import check_plan
        from abqjobpilot.execution.models import ExecutionError
        source = case.engineering/'axial_bar.inp'
        source.write_bytes(source.read_bytes().replace(b'1000,0.3', b'900,0.3'))
        with pytest.raises(ExecutionError):
            check_plan(case.service, case.plan)
    finally:
        generator.close()


def test_output_digest_and_runtime_downgrade_refused(tmp_path, monkeypatch, af_modules, research):
    case, _binding, _port, generator = make_case(tmp_path, monkeypatch, af_modules, research, 'A')
    try:
        from abqjobpilot.execution.rod_local_hil import check_contract
        from abqjobpilot.execution.models import ExecutionError, digest
        c = copy.deepcopy(case.plan['rod_contract'])
        c['local_contract']['output_digest'] = digest('wrong_output')
        with pytest.raises(ExecutionError):
            check_contract(c['local_contract'], 'A', c['candidate'])
        from aegiscae.research import rod_local_project as module
        monkeypatch.setattr(module, 'code_digest', lambda: digest_bytes(b'changed_after_A'))
        with pytest.raises(ContractError, match='WORKFLOW_CODE_CHANGED'):
            research.propose_b('2', {}, 3, 'changed')
    finally:
        generator.close()


def test_empty_runtime_materials_rejected(af_modules, research, monkeypatch):
    helper, _ = af_modules
    from abqjobpilot.execution.models import ExecutionError
    monkeypatch.setattr(helper.standard.StandardConfig, 'verify', lambda self: None)
    config = helper.standard.StandardConfig(helper.canonical_json({'materials': []}))
    # No file or process is accessed: rejection must precede any material lookup.
    with pytest.raises(ExecutionError) as error:
        helper.d7_original_runtime_check(config, research.inspect()['policy']['runtime'])
    assert error.value.code == 'LOCAL_RUNTIME_MISMATCH'


def test_console_requires_human_terminal_before_any_project_access(af_modules, monkeypatch):
    import sys
    from abqjobpilot import rod_local_console
    from abqjobpilot.execution.models import ExecutionError
    monkeypatch.setattr(sys, 'stdin', SimpleNamespace(isatty=lambda: False))
    monkeypatch.setattr(sys, 'argv', ['console', 'review', 'NONEXISTENT', 'plan', 'digest', 'research'])
    with pytest.raises(ExecutionError) as error:
        rod_local_console.main()
    assert error.value.code == 'HUMAN_TERMINAL_REQUIRED'


@pytest.mark.parametrize('choice', ['APPROVE', 'DENY'])
def test_console_exact_human_scope_without_grant_creation(tmp_path, monkeypatch, af_modules, research, choice):
    import io
    import sys
    from abqjobpilot import rod_local_console as console
    case, binding, port, generator = make_case(tmp_path, monkeypatch, af_modules, research, 'A')
    try:
        research.hold('A', port, binding, 3, 'hold_a')
        class Terminal(io.StringIO):
            def isatty(self):
                return True
        out = Terminal()
        monkeypatch.setattr(sys, 'stdin', Terminal())
        monkeypatch.setattr(sys, 'stdout', out)
        monkeypatch.setattr(sys, 'argv', ['console', 'review', 'OFFLINE_PROJECT', case.plan['plan_id'],
            case.plan['plan_digest'], str(research.project._root)])
        monkeypatch.setattr(console, 'ServiceLifecycleManager', lambda _p: SimpleNamespace(
            context=case.context, _profile=lambda: {}))
        monkeypatch.setattr(console, 'open_existing_read_only', lambda _c: case.store)
        calls = []
        def request(action, arguments, **kwargs):
            calls.append((action, arguments, kwargs))
            if action == 'review_a':
                return case.service.product_control.invoke(case.service, {'action': action,
                    'arguments': arguments, 'operation_key': kwargs['operation_key'],
                    'owner_id': case.store._session.owner_id, 'operator_token': case.token})
            return {'receipt': {'decision_digest': 'OFFLINE_DECISION', 'grant_id': 'OFFLINE_NOT_A_GRANT'}}
        monkeypatch.setattr(console, 'StandardOperator', lambda _p: SimpleNamespace(request=request))
        monkeypatch.setattr('builtins.input', lambda _prompt: 'APPROVE '+case.plan['plan_digest'] if choice == 'APPROVE' else 'DENY')
        console.main()
        assert calls[0][0] == 'review_a'
        args = calls[0][1]
        assert args['nonce'] == binding['request_nonce'] and args['plan_digest'] == binding['plan_digest']
        assert 'not_before' in out.getvalue() and 'expires_at' in out.getvalue()
        assert [c[0] for c in calls] == (['review_a', 'authorize'] if choice == 'APPROVE' else ['review_a'])
        with case.store.read() as conn:
            assert conn.execute('SELECT COUNT(*) FROM grants').fetchone()[0] == 0
        if choice == 'DENY':
            state = research.read_event('A', port, 'DENIED', 4, 'console_denied')
            assert state['budget']['held'] == 0 and state['budget']['available'] == 2
    finally:
        generator.close()


def test_dependency_metadata_explicit_path_without_site_hooks(af_modules, monkeypatch):
    import importlib.metadata
    from abqjobpilot.execution.rod_local_hil import dependency_versions
    paths = []
    def metadata(*, path):
        paths.append(path)
        return [SimpleNamespace(metadata={'Name': k}, version=v)
                for k, v in [('mcp', '2.3.0'), ('pydantic', '2.13.4'), ('pywin32', '312')]]
    monkeypatch.setattr(importlib.metadata, 'distributions', metadata)
    result = dependency_versions()
    assert result['mcp'] == '2.3.0' and result['pywin32'] == '312'
    assert len(paths) == 1 and Path(paths[0][0]) == Path('D:/XianLab/envs/LangChainEnv/Lib/site-packages')


def test_legacy_choice_adapter_cannot_approve_local(tmp_path, monkeypatch, af_modules, research):
    case, _binding, _port, generator = make_case(tmp_path, monkeypatch, af_modules, research, 'A')
    try:
        from abqjobpilot import product_standard
        from abqjobpilot.execution.product_standard import scope
        from abqjobpilot.execution.models import digest, now, ExecutionError
        packet = {'schema': 'rod-a-only-application-v1', 'execution_authorized': False,
            'plan_id': case.plan['plan_id'], 'plan_digest': case.plan['plan_digest'],
            'scope': scope(case.plan), 'scope_digest': digest(scope(case.plan)), 'nonce': 'offline',
            'not_before': now(), 'expires_at': now()+60}
        monkeypatch.setattr(product_standard, 'inspect_preparation', lambda _p: {'plan': case.plan})
        with pytest.raises(ExecutionError) as error:
            product_standard.review_rod_a_console('UNUSED', packet, choice='APPROVE_EXACT', operation_key='bad')
        assert error.value.code == 'LOCAL_HUMAN_TERMINAL_REQUIRED'
    finally:
        generator.close()


def test_public_reader_qualification_is_exact(tmp_path, monkeypatch, af_modules, research):
    case, _binding, _port, generator = make_case(tmp_path, monkeypatch, af_modules, research, 'A')
    try:
        from abqjobpilot.product_rod import RodProduct, validate_local_reader
        from abqjobpilot.execution.models import ExecutionError
        product = object.__new__(RodProduct)
        runtime = research.inspect()['policy']['runtime']
        validate_local_reader(product, case.service._standard_backend.config, runtime)
        with pytest.raises(ExecutionError):
            validate_local_reader(SimpleNamespace(), case.service._standard_backend.config, runtime)
        with pytest.raises(ExecutionError):
            validate_local_reader(product, SimpleNamespace(), runtime)
    finally:
        generator.close()


def test_real_acceptance_rejects_test_only_grant(af_modules):
    helper, _ = af_modules
    from abqjobpilot.execution.models import ExecutionError
    with pytest.raises(ExecutionError) as error:
        helper.d7_real_grant_check({'issuer': 'FakeGrantFixture', 'grant_kind': 'TEST_ONLY'}, {}, {}, {})
    assert error.value.code == 'REAL_GRANT_REQUIRED'
