"""Bounded A/B local-HIL reducer on ResearchProject's existing transaction log.

No issuer, submit, launcher or scheduler. Public ports read original AF records.
Same-user record custody is explicitly trusted, never a security attestation.
"""
import copy
import json
from decimal import Decimal
from pathlib import Path
import time

from aegiscae.contracts.research_contracts import ContractBundle, canonical_json, digest_bytes, require
from aegiscae.research import project as store
from aegiscae.research.rod_preview_rules import exact, sha, token
from aegiscae.research.rod_real_project import NUMERICAL_POLICY, real_bundle
from aegiscae.research.rod_output_v2 import (
    BASELINE, OUTPUT, PROFILE, TEMPLATE, TRUST, candidate_bytes, contract_digest,
)
from aegiscae.research.rod_local_port import LocalReadPort
from aegiscae.research.rod_local_verify import verify_a_preflight, verify_owner_artifact_set

VERSION = 'rod-local-workflow-v2'


def fingerprint(value):
    return digest_bytes(canonical_json(value))


def code_digest():
    root = Path(__file__).resolve().parents[1]
    rows = [(p.relative_to(root).as_posix(), digest_bytes(p.read_bytes()))
            for p in sorted(root.rglob('*.py'))
            if not {'_gdcae_plugin', '_gdcae_d7_plugin'} & set(p.parts)]
    return digest_bytes(json.dumps(rows, separators=(',', ':')).encode())


def policy(runtime):
    exact(runtime, ('gd', 'af', 'plugin', 'python', 'versions'))
    for name in ('gd', 'af', 'plugin', 'python'):
        sha(runtime[name])
    require(type(runtime['versions']) is dict and runtime['versions'], 'RUNTIME_REQUIRED')
    canonical_json(runtime)
    return {'schema': VERSION, 'trust': TRUST, 'runtime': copy.deepcopy(runtime),
            'output': OUTPUT, 'numerical': NUMERICAL_POLICY, 'full_budget': 2,
            'datacheck': 'DENIED', 'odb': 'DENIED', 'same_user_tamper_resistance': False}


def local_bundle(project_id, frozen):
    raw = json.loads(real_bundle(project_id).canonical_bytes())
    raw['model']['model_family'] = PROFILE
    raw['model']['artifacts'][0].update(sha256=BASELINE, size_bytes=len(TEMPLATE))
    raw['model']['integration_assumptions'].append('Local policy ' + fingerprint(frozen))
    raw['model']['applicability_limits'] = [TRUST, 'REAL_OUTPUT_FORMAT_NOT_YET_OBSERVED',
                                          'No hostile same-user isolation or V4 claim']
    for v in raw['verification']['validators']:
        v.update(version='d7_local_v2', sha256=frozen['runtime']['gd'])
    return ContractBundle.from_dict(raw)


def budget(state):
    values = list(state['attempts'].values())
    charged = sum(a.get('accepted') is not None for a in values)
    held = sum(a['status'] in ('HELD', 'INTENT', 'UNKNOWN') and a.get('accepted') is None for a in values)
    require(charged + held <= 2, 'BUDGET_EXHAUSTED')
    return {'limit': 2, 'held': held, 'charged': charged, 'available': 2-held-charged,
            'started': sum(a.get('started', False) for a in values)}


def candidate(state, phase, load, revision, causal):
    data = candidate_bytes(load)
    identity = fingerprint({'project': state['research_project_id'], 'contract': state['contract_digest'],
                            'phase': phase, 'revision': revision, 'input': digest_bytes(data), 'causal': causal})
    return {'candidate_id': 'candidate_' + identity[7:39], 'step': phase, 'load_n': load, 'unit': 'N',
            'research_project_id': state['research_project_id'], 'contract_digest': state['contract_digest'],
            'admitted_revision': revision, 'input_digest': digest_bytes(data), 'input_size': len(data),
            'output_identity': digest_bytes((identity + ':output').encode()),
            'verification_policy': NUMERICAL_POLICY, 'local_contract': {
                'schema': 'rod-local-hil-v2', 'trust': TRUST,
                'workflow_digest': state['policy']['runtime']['gd'],
                'output_digest': contract_digest(), 'runtime': state['policy']['runtime'], 'causal': causal}}


def encode(value):
    if type(value) is bytes:
        require(len(value) <= 16384, 'INPUT_LIMIT')
        raw = value.hex()
        return {'raw_hex': [raw[i:i+1024] for i in range(0, len(raw), 1024)]}
    if type(value) is int and value >= 2**63:
        return {'large_uint': str(value)}
    if type(value) is dict:
        return {k: encode(v) for k, v in value.items()}
    if type(value) is list:
        return [encode(v) for v in value]
    return value


def decode(value):
    if type(value) is dict:
        if set(value) == {'raw_hex'}:
            return bytes.fromhex(''.join(value['raw_hex']))
        if set(value) == {'large_uint'}:
            return int(value['large_uint'])
        return {k: decode(v) for k, v in value.items()}
    if type(value) is list:
        return [decode(v) for v in value]
    return value


def acceptance(evidence, binding):
    exact(evidence, ('schema', 'project_id', 'project_instance_id', 'plan_id', 'plan_digest',
                     'request_key', 'receipt', 'run', 'event', 'consumption'))
    require(evidence['schema'] == 'af-local-acceptance-v2', 'ACCEPTANCE_SOURCE')
    for key in ('project_id', 'project_instance_id', 'plan_id', 'plan_digest', 'request_key'):
        require(evidence[key] == binding[key], 'ACCEPTANCE_IDENTITY')
    receipt, run, event = (evidence[k] for k in ('receipt', 'run', 'event'))
    require(receipt['idempotency_key'] == binding['request_key'] and receipt['request_status'] == 'ACCEPTED'
            and receipt['run_id'] == run['run_id'] == event['run_id']
            and run['plan_id'] == binding['plan_id'] and run['plan_digest'] == binding['plan_digest']
            and run['project_id'] == binding['project_id']
            and run['project_instance_id'] == binding['project_instance_id']
            and run['simulation'] is False and run['backend_id'] == binding['backend_id']
            and event['type'] == 'REQUEST_ACCEPTED'
            and event['project_sequence'] == receipt['accepted_sequence']
            and evidence['consumption'] == {'grant_id': run['grant_id'], 'run_id': run['run_id']},
            'ACCEPTANCE_IDENTITY')
    return copy.deepcopy(evidence)


def causal_reference(state):
    a = state['attempts'].get('A', {})
    require(a.get('status') == 'ADMITTED' and a['decision']['V3'] == 'NOT_MET'
            and a.get('owner_stop') is not None, 'A_NOT_ELIGIBLE')
    return {'a_project_instance_id': a['binding']['project_instance_id'],
            'a_run_id': a['decision']['run_id'], 'a_decision_digest': fingerprint(a['decision']),
            'a_artifact_digest': a['decision']['artifact_set_digest'],
            'a_metric_mm': a['decision']['metrics']['displacement_mm'],
            'a_observed_revision': a['observed_revision'], 'owner_stop_digest': fingerprint(a['owner_stop']),
            'goal': 'NOT_MET'}


def apply_local(state, payload, bundle, revision, latest):
    exact(payload, ('schema_version', 'action', 'key', 'before_project_revision', 'data'))
    require(payload['schema_version'] == VERSION and payload['before_project_revision'] == revision,
            'REVISION_CONFLICT')
    token(payload['key'])
    require(latest == bundle.digests()['bundle'] and bundle.model.model_family == PROFILE, 'CONTRACT_MISMATCH')
    action, data = payload['action'], payload['data']
    if action == 'INITIALIZE':
        require(state is None and revision == 2, 'NEW_PROJECT_REQUIRED')
        frozen = policy(data['runtime'])
        require(data == frozen and local_bundle(bundle.research_project_id, frozen).canonical_bytes()
                == bundle.canonical_bytes(), 'POLICY_MISMATCH')
        state = {'research_project_id': bundle.research_project_id, 'contract_digest': latest,
                 'policy': frozen, 'attempts': {}, 'candidates': {}, 'keys': {}}
        state['candidates']['A'] = candidate(state, 'A', '1', revision+1, None)
    else:
        require(state is not None and state['contract_digest'] == latest, 'LOCAL_ROUTE_REQUIRED')
        state = copy.deepcopy(state)
        phase = data.get('phase')
        require(phase in ('A', 'B'), 'INVALID_PHASE')
        if action == 'PROPOSE_B':
            exact(data, ('phase', 'load_n', 'causal'))
            require(phase == 'B' and 'B' not in state['candidates'] and budget(state)['available'] >= 1,
                    'B_NOT_AVAILABLE')
            require(data['causal'] == causal_reference(state), 'CAUSAL_MISMATCH')
            item = candidate(state, 'B', data['load_n'], revision+1, data['causal'])
            require(item['input_digest'] != state['candidates']['A']['input_digest'], 'NEW_CANDIDATE_REQUIRED')
            state['candidates']['B'] = item
        else:
            require(phase in state['candidates'], 'CANDIDATE_MISSING')
            item = state['candidates'][phase]
            if action == 'HOLD':
                exact(data, ('phase', 'binding', 'preflight'))
                require(phase not in state['attempts'] and budget(state)['available'] >= 1, 'ATTEMPT_EXISTS')
                verify_a_preflight(data['preflight'], item, data['binding'])
                for prior in state['attempts'].values():
                    require(all(prior['binding'][k] != data['binding'][k] for k in
                        ('project_id', 'project_instance_id', 'plan_id', 'plan_digest', 'output_identity', 'request_key')),
                        'AF_IDENTITY_REUSED')
                state['attempts'][phase] = {'status': 'HELD', 'binding': data['binding'],
                                            'preflight': data['preflight'], 'accepted': None, 'started': False}
            else:
                require(phase in state['attempts'], 'RESERVATION_REQUIRED')
                attempt = state['attempts'][phase]
                if action in ('INTENT', 'UNKNOWN'):
                    exact(data, ('phase',))
                    require(attempt['status'] in (('HELD',) if action == 'INTENT' else ('INTENT', 'ACCEPTED')), 'ATTEMPT_PENDING')
                    attempt['status'] = action
                elif action == 'ACCEPTED':
                    exact(data, ('phase', 'evidence'))
                    require(attempt['status'] in ('INTENT', 'UNKNOWN', 'ACCEPTED'), 'INTENT_REQUIRED')
                    evidence = acceptance(data['evidence'], attempt['binding'])
                    if attempt['accepted'] is not None:
                        require(attempt['accepted'] == evidence, 'ACCEPTANCE_CONFLICT')
                    attempt.update(status='ACCEPTED', accepted=evidence)
                elif action == 'STARTED':
                    exact(data, ('phase', 'evidence'))
                    e = data['evidence']
                    exact(e, ('schema', 'acceptance', 'event'))
                    require(attempt['accepted'] is not None and e['schema'] == 'af-local-started-v2'
                            and acceptance(e['acceptance'], attempt['binding']) == attempt['accepted']
                            and e['event']['type'] == 'STANDARD_CREATED'
                            and e['event']['run_id'] == attempt['accepted']['run']['run_id'], 'START_UNKNOWN')
                    attempt['started'] = True
                    attempt['start_evidence'] = copy.deepcopy(e)
                elif action == 'DENIED':
                    exact(data, ('phase', 'evidence'))
                    e = data['evidence']
                    exact(e, ('schema', 'project_instance_id', 'plan_id', 'plan_digest', 'decision', 'no_acceptance'))
                    require(attempt['status'] == 'HELD' and attempt['accepted'] is None
                            and e['schema'] == 'af-local-denial-v2' and e['no_acceptance'] is True
                            and all(e[k] == attempt['binding'][k] for k in ('project_instance_id', 'plan_id', 'plan_digest'))
                            and e['decision']['decision'] == 'DENY_TERMINAL', 'DENIAL_UNQUALIFIED')
                    attempt.update(status='DENIED', denial=copy.deepcopy(e))
                elif action == 'OBSERVE':
                    exact(data, ('phase', 'evidence'))
                    require(attempt['status'] == 'ACCEPTED', 'ACCEPTANCE_REQUIRED')
                    envelope = decode(data['evidence'])
                    result = verify_owner_artifact_set(envelope, item, attempt['binding'])
                    require(result['run_id'] == attempt['accepted']['run']['run_id']
                            and envelope['owner_evidence']['run']['grant_id'] == attempt['accepted']['run']['grant_id'],
                            'ACCEPTANCE_IDENTITY')
                    metric = Decimal(result['metrics']['displacement_mm'])
                    result.update(V0='LOCAL_RECORD_CHAIN_VERIFIED', V1='PASS', V2='PASS',
                        V3='SATISFIED' if Decimal('0.019') <= metric <= Decimal('0.021') else 'NOT_MET',
                        trust=TRUST, real_goal='LOCAL_CONTRACT_VERDICT', same_user_tamper_resistance=False)
                    attempt.update(status='ADMITTED', started=True, decision=result,
                                   evidence=data['evidence'], observed_revision=revision+1)
                elif action == 'OWNER_STOP':
                    exact(data, ('phase', 'evidence'))
                    require(attempt['status'] == 'ADMITTED' and 'owner_stop' not in attempt, 'A_NOT_ELIGIBLE')
                    e = data['evidence']
                    exact(e, ('schema', 'project_instance_id', 'run_id', 'owner_id', 'receipt', 'scope'))
                    require(e['schema'] == 'af-local-orderly-stop-v2'
                            and e['project_instance_id'] == attempt['binding']['project_instance_id']
                            and e['run_id'] == attempt['decision']['run_id'] and e['scope'] == 'EMPTY_CONFIRMED'
                            and e['owner_id'] == decode(attempt['evidence'])['launch_intent']['owner_id']
                            and e['receipt']['owner_id'] == e['owner_id']
                            and e['receipt']['action'] == 'lifecycle_stop_idle_v1'
                            and e['receipt']['state'] == 'STOP_COMMITTED'
                            and e['receipt']['project_instance_id'] == e['project_instance_id'], 'OWNER_STOP_UNKNOWN')
                    attempt['owner_stop'] = copy.deepcopy(e)
                else:
                    require(False, 'INVALID_LOCAL_ACTION')
    require(payload['key'] not in state['keys'], 'DUPLICATE_EVENT')
    state['keys'][payload['key']] = fingerprint({'action': action, 'data': data})
    budget(state)
    return state


def _fault(stage):
    """Offline fault injection seam, no execution."""


class LocalRodProject:
    def __init__(self, project):
        require(type(project) is store.ResearchProject, 'INVALID_PROJECT')
        self.project = project

    def _read(self, meta, bundles, events):
        require(meta['schema_version'] == 1, 'LOCAL_ROUTE_REQUIRED')
        bundle = next((b[0] for b in bundles if b[0].model.model_family == PROFILE), None)
        require(bundle is not None, 'LOCAL_CONTRACT_REQUIRED')
        state, latest = None, None
        for e in events:
            if e['kind'] == 'BUNDLE_FROZEN':
                latest = e['bundle_digest']
            elif e['kind'] == 'WORKFLOW_RECORDED':
                state = apply_local(state, e['workflow'], bundle, e['project_revision']-1, latest)
            elif e['kind'] in ('BUDGET_RECORDED', 'CANDIDATE_PUBLICATION_OBSERVED'):
                require(False, 'LOCAL_ROUTE_REQUIRED')
        require(latest == bundle.digests()['bundle'], 'CONTRACT_MISMATCH')
        return bundle, state

    def _view(self, state, meta):
        return {**copy.deepcopy(state), 'project_revision': meta['project_revision'], 'budget': budget(state),
                'execution_authorized': False, 'host': 'HOST_NOT_QUALIFIED',
                'output_format': 'REAL_OUTPUT_FORMAT_NOT_YET_OBSERVED'}

    def inspect(self):
        with self.project._snapshot() as (_, meta, bundles, events):
            return self._view(self._read(meta, bundles, events)[1], meta)

    def _record(self, action, data, revision, key):
        token(key)
        request = fingerprint({'action': action, 'data': data})
        with self.project._snapshot(write=True) as (conn, meta, bundles, events):
            bundle, state = self._read(meta, bundles, events)
            if state is not None and key in state['keys']:
                require(state['keys'][key] == request, 'IDEMPOTENCY_CONFLICT')
                return {**self._view(state, meta), 'replayed': True}
            require(type(revision) is int and revision == meta['project_revision'], 'REVISION_CONFLICT')
            runtime = data['runtime'] if action == 'INITIALIZE' else state['policy']['runtime']
            require(runtime['gd'] == code_digest(), 'WORKFLOW_CODE_CHANGED')
            payload = {'schema_version': VERSION, 'action': action, 'data': copy.deepcopy(data),
                       'key': key, 'before_project_revision': revision}
            state = apply_local(state, payload, bundle, revision, bundle.digests()['bundle'])
            store._commit_workflow_event(conn, meta, bundle.digests()['bundle'], payload)
            _fault('before_commit')
            conn.commit()
            _fault('after_commit')
            return {**self._view(state, meta), 'replayed': False}

    def candidate_input(self, phase):
        return candidate_bytes(self.inspect()['candidates'][phase]['load_n'])

    def hold(self, phase, port, binding, revision, key):
        state = self.inspect()
        if key in state['keys']:
            a = state['attempts'][phase]
            return self._record('HOLD', {'phase': phase, 'binding': binding, 'preflight': a['preflight']}, revision, key)
        require(type(port) is LocalReadPort, 'READ_PORT_UNQUALIFIED')
        port.validate(state['policy']['runtime'])
        c = state['candidates'][phase]
        expected = {'research_project_id': c['research_project_id'], 'contract_digest': c['contract_digest'],
            'research_revision': c['admitted_revision'], 'candidate_id': c['candidate_id'],
            'request_nonce': binding['request_nonce'], 'input_digest': c['input_digest']}
        preflight = port.preflight_real(plan_id=binding['plan_id'], expected_plan_digest=binding['plan_digest'],
                                       expected_contract=expected)
        require(preflight['expires_at'] > int(time.time()), 'PREFLIGHT_EXPIRED')
        return self._record('HOLD', {'phase': phase, 'binding': binding, 'preflight': preflight}, revision, key)

    def intent(self, phase, revision, key):
        return self._record('INTENT', {'phase': phase}, revision, key)

    def unknown(self, phase, revision, key):
        return self._record('UNKNOWN', {'phase': phase}, revision, key)

    def read_event(self, phase, port, action, revision, key):
        require(action in ('ACCEPTED', 'OBSERVE', 'OWNER_STOP', 'STARTED', 'DENIED'), 'INVALID_LOCAL_ACTION')
        state = self.inspect()
        a = state['attempts'][phase]
        if key in state['keys']:
            field = {'ACCEPTED': 'accepted', 'OBSERVE': 'evidence', 'OWNER_STOP': 'owner_stop', 'STARTED': 'start_evidence', 'DENIED': 'denial'}[action]
            return self._record(action, {'phase': phase, 'evidence': a[field]}, revision, key)
        require(type(port) is LocalReadPort, 'READ_PORT_UNQUALIFIED')
        port.validate(state['policy']['runtime'])
        b = a['binding']
        refs = dict(plan_id=b['plan_id'], expected_plan_digest=b['plan_digest'], request_key=b['request_key'])
        if action == 'ACCEPTED':
            evidence = port.read_acceptance(**refs)
        elif action == 'OBSERVE':
            evidence = port.read_real_artifacts(**refs)
        elif action == 'OWNER_STOP':
            evidence = port.read_orderly_stop(**refs)
        elif action == 'STARTED':
            evidence = port.read_started(**refs)
        else:
            evidence = port.read_denial(**refs)
        return self._record(action, {'phase': phase, 'evidence': encode(evidence)}, revision, key)

    def propose_b(self, load_n, causal, revision, key):
        return self._record('PROPOSE_B', {'phase': 'B', 'load_n': load_n, 'causal': causal}, revision, key)


def create_local_research(root, name, runtime):
    frozen = policy(runtime)
    require(runtime['gd'] == code_digest(), 'WORKFLOW_CODE_CHANGED')
    project = store.create_research_project(root, name)
    project = store.open_existing_for_explicit_write(root)
    bundle = local_bundle(project.inspect()['research_project_id'], frozen)
    project.freeze_contract_bundle(bundle, 1, 'freeze-local-contract')
    result = LocalRodProject(project)
    result._record('INITIALIZE', frozen, 2, 'initialize-local-A')
    return result
