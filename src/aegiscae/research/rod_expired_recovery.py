"""D7 A-only expired preparation recovery. No authority or execution operations.

One compatibility transition per ResearchProject; original contracts/candidates
and AF stores remain immutable. Evidence custody is TRUSTED_LOCAL_HIL.
"""
import ast
import copy
import json
from pathlib import Path
import time

from aegiscae.contracts.research_contracts import digest_bytes, require
from aegiscae.research.rod_preview_rules import exact, token

SCHEMA = 'd7-expired-a-compatibility-v1'
LEGACY_VERSION = 'd7-expired-a-recovery-v1'
VERSION = 'd7-expired-a-recovery-v2'
PROOF_SCHEMA = 'd7-original-af-expired-empty-v2'
PROJECT = 'research/rod_local_project.py'
ADDITION = 'research/rod_expired_recovery.py'
LEGACY_ZERO_TABLES = ('grants', 'runs', 'receipts', 'consumption', 'events',
                      'management_receipts', 'reconciliations')
ZERO_TABLES = (*LEGACY_ZERO_TABLES, 'observations', 'validations',
               'management_grants', 'management_consumption', 'control_events')


def active_runtime(state):
    return state.get('compatibility', {}).get('new_runtime', state['policy']['runtime'])


def execution_candidate(state, phase):
    item = copy.deepcopy(state['candidates'][phase])
    item['local_contract']['runtime'] = copy.deepcopy(active_runtime(state))
    item['local_contract']['workflow_digest'] = active_runtime(state)['gd']
    return item


def inventory(root):
    root = Path(root).resolve()
    require(root.is_dir(), 'SOURCE_REQUIRED')
    return {p.relative_to(root).as_posix(): digest_bytes(p.read_bytes())
            for p in sorted(root.rglob('*.py'))
            if not {'_gdcae_plugin', '_gdcae_d7_plugin'} & set(p.parts)}


def inventory_digest(rows):
    return digest_bytes(json.dumps(sorted(rows.items()), separators=(',', ':')).encode())


def scientific_projection(body):
    """Compare actual acceptance code, ignoring only explicit runtime projection.

    All top-level functions except code_digest and creation remain in the proof;
    the reducer's only permitted scientific-code edit is this exact adapter.
    Imports and constants are compared too. Class methods are orchestration.
    """
    tree = ast.parse(body)
    recovery_hook = ast.parse("""if payload.get('action') == 'REBIND_EXPIRED_A':
    from aegiscae.research.rod_expired_recovery import reduce_event
    return reduce_event(state, payload, bundle, revision, latest)
""").body[0]
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == 'apply_local':
            node.body = [n for n in node.body if ast.dump(n) != ast.dump(recovery_hook)]
    tree.body = [n for n in tree.body if not isinstance(n, ast.ClassDef)
                 and not (isinstance(n, ast.FunctionDef)
                          and n.name in ('code_digest', 'create_local_research'))]
    for node in ast.walk(tree):
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                value[:] = [n for n in value if not (
                    isinstance(n, ast.ImportFrom)
                    and n.module == 'aegiscae.research.rod_expired_recovery'
                    and [a.name for a in n.names] == ['execution_candidate'])]
        if (isinstance(node, ast.Assign) and isinstance(node.value, ast.Call)
                and ast.dump(node.value) == ast.dump(ast.parse(
                    'execution_candidate(state, phase)', mode='eval').body)):
            node.value = ast.parse("state['candidates'][phase]", mode='eval').body
    return digest_bytes(ast.dump(tree, include_attributes=False).encode())


def build_compatibility(state, old_source_root, new_runtime):
    from .rod_local_project import code_digest, fingerprint, policy
    policy(new_runtime)
    old = inventory(old_source_root)
    new_root = Path(__file__).resolve().parents[1]
    new = inventory(new_root)
    original = state['policy']['runtime']
    require(inventory_digest(old) == original['gd'], 'OLD_SOURCE_IDENTITY_MISMATCH')
    require(inventory_digest(new) == new_runtime['gd'] == code_digest(), 'WORKFLOW_CODE_CHANGED')
    require(all(original[k] == new_runtime[k] for k in ('af', 'plugin', 'python', 'versions')),
            'UNSUPPORTED_RUNTIME_CHANGE')
    changed = sorted(k for k in set(old) | set(new) if old.get(k) != new.get(k))
    require(set(changed) <= {PROJECT, ADDITION} and ADDITION in changed,
            'SCIENTIFIC_SOURCE_CHANGED')
    before = scientific_projection((Path(old_source_root) / PROJECT).read_bytes())
    after = scientific_projection((new_root / PROJECT).read_bytes())
    require(before == after, 'SCIENTIFIC_RULES_CHANGED')
    return {'schema': SCHEMA, 'version': VERSION,
            'research_project_id': state['research_project_id'],
            'contract_digest': state['contract_digest'],
            'candidate_digest': fingerprint(state['candidates']['A']),
            'old_runtime': copy.deepcopy(original), 'new_runtime': copy.deepcopy(new_runtime),
            'old_validator': {'version': 'd7_local_v2', 'sha256': original['gd']},
            'new_validator': {'version': VERSION, 'sha256': new_runtime['gd']},
            'old_sources': old, 'new_sources': new, 'changed_files': changed,
            'equivalence': {'method': 'unchanged-closure-and-acceptance-AST-v1',
                            'old_acceptance': before, 'new_acceptance': after},
            'execution_authorized': False}


def validate_compatibility(record, state):
    from .rod_local_project import fingerprint, policy
    exact(record, ('schema', 'version', 'research_project_id', 'contract_digest',
                  'candidate_digest', 'old_runtime', 'new_runtime', 'old_validator',
                  'new_validator', 'old_sources', 'new_sources', 'changed_files',
                  'equivalence', 'execution_authorized'))
    require(record['schema'] == SCHEMA and record['version'] in (LEGACY_VERSION, VERSION)
            and record['execution_authorized'] is False, 'COMPATIBILITY_INVALID')
    require(record['research_project_id'] == state['research_project_id']
            and record['contract_digest'] == state['contract_digest']
            and record['candidate_digest'] == fingerprint(state['candidates']['A'])
            and record['old_runtime'] == state['policy']['runtime'], 'COMPATIBILITY_IDENTITY')
    for label in ('old', 'new'):
        runtime = record[label + '_runtime']
        policy(runtime)
        require(inventory_digest(record[label + '_sources']) == runtime['gd'],
                'COMPATIBILITY_SOURCE_DIGEST')
        require(record[label + '_validator'] == {
            'version': 'd7_local_v2' if label == 'old' else record['version'],
            'sha256': runtime['gd']}, 'COMPATIBILITY_VALIDATOR')
    require(all(record['old_runtime'][k] == record['new_runtime'][k]
                for k in ('af', 'plugin', 'python', 'versions')), 'UNSUPPORTED_RUNTIME_CHANGE')
    old, new = record['old_sources'], record['new_sources']
    changed = sorted(k for k in set(old) | set(new) if old.get(k) != new.get(k))
    require(changed == record['changed_files'] and ADDITION in changed
            and set(changed) <= {PROJECT, ADDITION}, 'SCIENTIFIC_SOURCE_CHANGED')
    e = record['equivalence']
    exact(e, ('method', 'old_acceptance', 'new_acceptance'))
    require(e['method'] == 'unchanged-closure-and-acceptance-AST-v1'
            and e['old_acceptance'] == e['new_acceptance'], 'SCIENTIFIC_RULES_CHANGED')


def require_unstarted_files(af_project):
    """Pinned AF lifecycle markers, without connecting to or starting an Owner."""
    root = Path(af_project)
    require(root.is_absolute() and root.is_dir()
            and not any(p.is_symlink() or p.is_junction() for p in (root, *root.parents)),
            'UNSAFE_PATH')
    private = root / 'private'
    require(private.is_dir() and not private.is_symlink() and not private.is_junction(),
            'NONEXECUTION_UNPROVEN')
    require(not any(p.exists() or p.is_symlink() or p.is_junction() for p in (
        root / 'owner.json', private / 'connection.json', private / 'lifecycle-current.json'))
        and not any(private.glob('start_*')), 'NONEXECUTION_UNPROVEN')


def require_eligible(state):
    require('compatibility' not in state and set(state['attempts']) == {'A'}
            and set(state['candidates']) == {'A'}, 'RECOVERY_NOT_AVAILABLE')
    old = state['attempts']['A']
    require(old['status'] == 'HELD' and old['accepted'] is None and old['started'] is False,
            'RECOVERY_NOT_AVAILABLE')


def read_expired_evidence(af_project, binding):
    """Read original AF format-3 tables in one read-only snapshot.

    Narrow adapter to existing AF reader, deliberately no private DB path guess,
    write lease, Owner, or caller-provided boolean nonacceptance assertion.
    """
    from abqjobpilot.product_rod import RodProduct
    from abqjobpilot.execution.store import document
    from abqjobpilot.execution.models import digest
    require_unstarted_files(af_project)
    reader = RodProduct(af_project)._reader()
    with reader.store.read() as conn:
        conn.execute('BEGIN')
        plan = document(conn, 'plans', 'plan_id', binding['plan_id'])
        body = dict(plan)
        require(body.pop('plan_digest') == binding['plan_digest'] == digest(body), 'PLAN_IDENTITY')
        require(reader.context.project_id == binding['project_id']
                and reader.context.project_instance_id == binding['project_instance_id']
                == plan['project_instance_id'], 'PLAN_IDENTITY')
        counts = {t: conn.execute('SELECT COUNT(*) FROM ' + t).fetchone()[0] for t in ZERO_TABLES}
        require(all(v == 0 for v in counts.values()), 'NONEXECUTION_UNPROVEN')
        require([tuple(row) for row in conn.execute("SELECT value FROM meta WHERE key='supervisor_started'")]
                == [('0',)], 'NONEXECUTION_UNPROVEN')
        require(conn.execute('SELECT COUNT(*) FROM plans').fetchone()[0] == 1,
                'OLD_PLAN_AMBIGUOUS')
        require(conn.execute('SELECT state FROM dispatch_gate WHERE id=1').fetchone()[0] == 'PAUSED'
                and conn.execute('SELECT run_id FROM slot WHERE id=1').fetchone()[0] is None,
                'NONEXECUTION_UNPROVEN')
        observed = int(time.time())
        require(plan['expires_at'] < observed, 'OLD_PLAN_NOT_EXPIRED')
    require_unstarted_files(af_project)
    return {'schema': PROOF_SCHEMA, 'binding': copy.deepcopy(binding),
            'plan': plan, 'counts': counts, 'observed_at': observed,
            'gate': 'PAUSED', 'slot': None, 'supervisor_started': '0',
            'owner_start_markers': []}


def reduce_event(state, payload, bundle, revision, latest):
    from .rod_local_project import VERSION as WORKFLOW, apply_local, budget, fingerprint
    from .rod_local_verify import verify_a_preflight
    if payload['action'] != 'REBIND_EXPIRED_A':
        return apply_local(state, payload, bundle, revision, latest)
    exact(payload, ('schema_version', 'action', 'key', 'before_project_revision', 'data'))
    token(payload['key'])
    require(payload['schema_version'] == WORKFLOW and payload['before_project_revision'] == revision,
            'REVISION_CONFLICT')
    require(state is not None and latest == state['contract_digest'] == bundle.digests()['bundle'],
            'CONTRACT_MISMATCH')
    data = payload['data']
    exact(data, ('phase', 'compatibility', 'nonexecution', 'binding', 'preflight'))
    require(data['phase'] == 'A' and 'compatibility' not in state
            and set(state['attempts']) == {'A'} and set(state['candidates']) == {'A'},
            'RECOVERY_NOT_AVAILABLE')
    old = state['attempts']['A']
    require(old['status'] == 'HELD' and old['accepted'] is None and old['started'] is False,
            'RECOVERY_NOT_AVAILABLE')
    validate_compatibility(data['compatibility'], state)
    e = data['nonexecution']
    legacy = data['compatibility']['version'] == LEGACY_VERSION
    fields = ('schema', 'binding', 'plan', 'counts', 'observed_at', 'gate', 'slot')
    exact(e, fields if legacy else (*fields, 'supervisor_started', 'owner_start_markers'))
    if not legacy:
        require(e['supervisor_started'] == '0' and e['owner_start_markers'] == [],
                'NONEXECUTION_UNPROVEN')
    require(e['schema'] == ('d7-original-af-expired-empty-v1' if legacy else PROOF_SCHEMA)
            and e['binding'] == old['binding']
            and type(e['observed_at']) is int and e['observed_at'] > 0
            and e['counts'] == dict.fromkeys(LEGACY_ZERO_TABLES if legacy else ZERO_TABLES, 0)
            and all(type(v) is int for v in e['counts'].values())
            and e['gate'] == 'PAUSED' and e['slot'] is None, 'NONEXECUTION_UNPROVEN')
    from .rod_evidence import af_digest
    plan = dict(e['plan'])
    require(plan.pop('plan_digest') == old['binding']['plan_digest'] == af_digest(plan)
            and plan['plan_id'] == old['binding']['plan_id']
            and plan['project_instance_id'] == old['binding']['project_instance_id']
            and plan['rod_contract']['local_contract'] == state['candidates']['A']['local_contract']
            and plan['expires_at'] == old['preflight']['expires_at'] < e['observed_at'],
            'OLD_PLAN_NOT_EXPIRED')
    require(all(old['binding'][k] != data['binding'][k] for k in
                ('project_id', 'project_instance_id', 'plan_id', 'plan_digest',
                 'request_key', 'request_nonce', 'output_identity')), 'AF_IDENTITY_REUSED')
    state = copy.deepcopy(state)
    state['compatibility'] = copy.deepcopy(data['compatibility'])
    verify_a_preflight(data['preflight'], execution_candidate(state, 'A'), data['binding'])
    require(data['preflight']['expires_at'] > e['observed_at'], 'PREFLIGHT_EXPIRED')
    state['retired_attempts'] = [dict(copy.deepcopy(old), status='EXPIRED_UNEXECUTED',
                                      nonexecution=copy.deepcopy(e))]
    state['attempts']['A'] = {'status': 'HELD', 'binding': copy.deepcopy(data['binding']),
                            'preflight': copy.deepcopy(data['preflight']),
                            'accepted': None, 'started': False}
    require(payload['key'] not in state['keys'], 'DUPLICATE_EVENT')
    state['keys'][payload['key']] = fingerprint({'action': payload['action'], 'data': data})
    require(budget(state)['held'] == 1 and budget(state)['charged'] == 0, 'BUDGET_EXHAUSTED')
    return state


def rebind_expired_a(research, old_af_project, old_source_root, port, binding,
                     new_runtime, revision, key):
    """Commit only after independent source comparison and original AF reads.

    Caller prepares a fresh inert AF Project/Plan with execution_candidate's
    new runtime projection. No production preparation is performed on import.
    """
    from .rod_local_port import LocalReadPort
    from .rod_local_project import LocalRodProject
    require(type(research) is LocalRodProject and type(port) is LocalReadPort,
            'READ_PORT_UNQUALIFIED')
    state = research.inspect()
    require_eligible(state)
    require(state['project_revision'] == revision, 'REVISION_CONFLICT')
    compatibility = build_compatibility(state, old_source_root, new_runtime)
    port.validate(new_runtime)
    c = state['candidates']['A']
    expected = {k: c[k] for k in ('research_project_id', 'contract_digest', 'candidate_id', 'input_digest')}
    expected.update(research_revision=c['admitted_revision'], request_nonce=binding['request_nonce'])
    preflight = port.preflight_real(plan_id=binding['plan_id'], expected_plan_digest=binding['plan_digest'],
                                   expected_contract=expected)
    e = read_expired_evidence(old_af_project, state['attempts']['A']['binding'])
    require(preflight['expires_at'] > int(time.time()), 'PREFLIGHT_EXPIRED')
    return research._record('REBIND_EXPIRED_A', {'phase': 'A', 'compatibility': compatibility,
                           'nonexecution': e, 'binding': binding, 'preflight': preflight}, revision, key)


def assess_expired_a(workspace, old_source_root, new_runtime):
    """Read-only readiness evidence. No Plan, intent, reservation or expiry creation.

    This snapshot is informational: preparation always reads the original AF again.
    AF/runtime qualification remains mandatory at the explicit preparation entry.
    """
    from . import project
    from .rod_local_project import LocalRodProject
    root = Path(workspace)
    require(root.is_absolute() and not any(p.is_symlink() or p.is_junction()
            for p in (root, *root.parents)), 'UNSAFE_PATH')
    frozen = json.loads((root / 'd7-v2.json').read_text())
    state = LocalRodProject(project.open_existing_readonly(root / 'research')).inspect()
    require(frozen['schema'] == 'gdcae-d7-workspace-v1'
            and frozen['runtime'] == state['policy']['runtime']
            and frozen['research_project_id'] == state['research_project_id']
            and frozen['contract_digest'] == state['contract_digest'], 'WORKSPACE_RUNTIME_MISMATCH')
    require_eligible(state)
    return {'schema': VERSION, 'project_revision': state['project_revision'], 'budget': state['budget'],
            'compatibility': build_compatibility(state, old_source_root, new_runtime),
            'nonexecution': read_expired_evidence(root / 'af-A', state['attempts']['A']['binding']),
            'execution_authorized': False}


def prepare_expired_a(workspace, old_source_root, new_runtime, config, expires_at):
    """Explicit recovery entry; old installed plugin guard remains fail-closed.

    Resumable fixed v2 output directory with write-once intent. Only inert AF
    preparation and the atomic GD event are permitted here.
    """
    from . import project
    from .rod_local_project import LocalRodProject, fingerprint
    from .rod_local_port import LocalReadPort
    from .rod_output_v2 import TEMPLATE
    from .rod_preview_rules import token
    from abqjobpilot.product_rod import RodProduct
    from abqjobpilot.execution.models import digest
    from abqjobpilot.execution.rod_local_hil import check_runtime
    root = Path(workspace)
    require(root.is_absolute() and not any(p.is_symlink() or p.is_junction()
            for p in (root, *root.parents)), 'UNSAFE_PATH')
    root = root.resolve()
    frozen = json.loads((root / 'd7-v2.json').read_text())
    research = LocalRodProject(project.open_existing_for_explicit_write(root / 'research'))
    state = research.inspect()
    require(frozen['schema'] == 'gdcae-d7-workspace-v1'
            and frozen['runtime'] == state['policy']['runtime']
            and frozen['research_project_id'] == state['research_project_id']
            and frozen['contract_digest'] == state['contract_digest'], 'WORKSPACE_RUNTIME_MISMATCH')
    check_runtime(config, new_runtime)
    compatibility = build_compatibility(state, old_source_root, new_runtime)
    # A partial legacy preparation cannot be silently replaced by a v2 request.
    require(not (root / 'expired-a-recovery-v1').exists(), 'LEGACY_RECOVERY_RECONCILIATION_REQUIRED')
    destination = root / 'expired-a-recovery-v2'
    intent = {'schema': VERSION, 'compatibility_digest': fingerprint(compatibility),
              'expires_at': expires_at, 'config_digest': digest(config.value())}
    body = json.dumps(intent, sort_keys=True).encode()
    key = 'rebind-expired-A-v2'
    if destination.exists():
        require(not destination.is_symlink() and not destination.is_junction()
                and (destination / 'intent.json').is_file()
                and not (destination / 'intent.json').is_symlink()
                and (destination / 'intent.json').read_bytes() == body, 'IDEMPOTENCY_CONFLICT')
        if key in state['keys']:
            require(state.get('compatibility') == compatibility, 'IDEMPOTENCY_CONFLICT')
            return {**state, 'replayed': True}
    require_eligible(state)
    read_expired_evidence(root / 'af-A', state['attempts']['A']['binding'])
    require(type(expires_at) is int and int(time.time()) < expires_at <= int(time.time()) + 600,
            'APPROVAL_WINDOW_INVALID')
    if not destination.exists():
        destination.mkdir()
        with (destination / 'intent.json').open('xb') as stream:
            stream.write(body)
            stream.flush()
            import os
            os.fsync(stream.fileno())
    path = destination / 'af-A'
    product = RodProduct(path) if path.exists() else RodProduct.create(path, 'D7 expired A recovery')
    require_unstarted_files(path)
    projected = {**state, 'compatibility': compatibility}
    c = execution_candidate(projected, 'A')
    nonce = 'recovery_' + fingerprint(intent)[7:39]
    token(nonce)
    args = {k: c[k] for k in ('research_project_id', 'contract_digest', 'candidate_id')}
    args.update(research_revision=c['admitted_revision'], request_nonce=nonce)
    plan = product.prepare_real(frozen_template=TEMPLATE, candidate_bytes=research.candidate_input('A'),
        load_n=c['load_n'], config=config, **args, expires_at=expires_at,
        phase='A', local_contract=c['local_contract'])
    require_unstarted_files(path)
    binding = {k: plan[k] for k in ('project_id', 'project_instance_id', 'plan_id', 'plan_digest', 'backend_id')}
    binding.update(input_digest=c['input_digest'], resources_digest=digest(plan['resources']),
        output_identity=plan['output_key'], candidate_output_identity=c['output_identity'],
        request_key=nonce, request_nonce=nonce)
    return rebind_expired_a(research, root / 'af-A', old_source_root,
        LocalReadPort(path, config, new_runtime), binding, new_runtime, state['project_revision'], key)
