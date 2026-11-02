"""AOO v1 Project-owned session policy; native host executes, Main reasons.

No model client, scheduler, solver, AF import or general workflow engine.
The trusted host port supplies caller provenance, never chat text.
"""
import copy
import json
import os
from pathlib import Path
import re
import tomllib
import uuid

from aegiscae.contracts.research_contracts import canonical_json, digest_bytes, require
from aegiscae.research import project as projects

SCHEMA = 'aoo-scoped-sessions-v1'
FILE = 'scoped-sessions-v1.json'
ROLES = {'gdcae-cae': 'CAE', 'gdcae-results': 'Results',
         'gdcae-inverse': 'Inverse', 'gdcae-reviewer': 'Review'}
DENIED_FEATURES = dict.fromkeys(('shell_tool', 'apps', 'plugins', 'memories',
                               'request_permissions_tool'), False)
CAPABILITIES = ('create_thread', 'set_display_name', 'project_association',
                'visible_in_target_client', 'user_can_ask_scoped_question',
                'return_result_to_main', 'resume_or_read', 'configure_fixed_model')
BINDING_FIELDS = ('task_id', 'role_id', 'purpose', 'evidence_refs', 'output_required',
                  'project_id', 'agent_instance_id', 'role_definition_digest', 'role_version',
                  'profile', 'features', 'display_name', 'main_ref', 'main_display_name')


def fingerprint(value):
    return digest_bytes(canonical_json(value))


def text(value):
    require(type(value) is str and 0 < len(value) <= 1024 and '\x00' not in value,
            'SESSION_FIELD_INVALID')
    return value


def reference(value):
    require(type(value) is dict and set(value) == {'host_id', 'thread_id'}, 'THREAD_REF_INVALID')
    for item in value.values():
        text(item)
    return value


def load_roles(directory):
    result = {}
    for name, label in ROLES.items():
        path = Path(directory) / (name + '.toml')
        body = path.read_bytes()
        raw = tomllib.loads(body.decode())
        require(raw['name'] == name and raw['features'] == DENIED_FEATURES, 'ROLE_BOUNDARY_CHANGED')
        result[name] = {'role_id': name, 'label': label, 'version': 'aoo-v1',
                        'definition_digest': digest_bytes(body), 'features': raw['features'],
                        'instructions': raw['developer_instructions'].splitlines()}
        canonical_json(result[name])
    return result


def route_parts(binding, parts):
    """Codex classifies intent; this gate never infers authority from prose.

    This is a deterministic structured-policy test, not an NLP accuracy claim.
    Unclassified requests and additional engineering work default to Main.
    """
    require(type(parts) is list and 0 < len(parts) <= 16, 'QUESTION_INVALID')
    decisions = []
    for part in parts:
        kind = part.get('kind')
        same = (part.get('project_id') == binding['project_id']
                and part.get('task_id') == binding['task_id']
                and part.get('role_id') == binding['role_id'])
        if kind in ('STOP', 'RISK'):
            action = 'PAUSE_OR_ESCALATE'
        elif kind == 'CORRECTION' and same:
            action = 'RECORD_UNVERIFIED_FEEDBACK'
        elif (same and kind in ('IDENTITY', 'PROGRESS', 'RESULT', 'EXPLAIN')
              and part.get('simple') is True and part.get('new_work') is False
              and type(part.get('evidence_refs')) is list
              and set(part['evidence_refs']) <= set(binding['evidence_refs'])):
            action = 'ANSWER_LOCAL'
        else:
            action = 'REDIRECT_MAIN'
        decisions.append({'kind': kind if kind in ('STOP', 'RISK', 'CORRECTION', 'IDENTITY',
                           'PROGRESS', 'RESULT', 'EXPLAIN') else 'OTHER',
                          'action': action, 'main_ref': binding['main_ref'],
                          'main_display_name': binding['main_display_name'],
                          'solver_stopped': 'NOT_ASSERTED'})
    return decisions


def _fault(stage):
    """Developer crash seam; no runtime callback parameter."""


class SessionHub:
    def __init__(self, project, roles):
        require(type(project) is projects.ResearchProject, 'INVALID_PROJECT')
        require(set(roles) == set(ROLES), 'ROLE_CATALOG_INVALID')
        self.project, self.roles = project, copy.deepcopy(roles)

    def _path(self):
        return projects._path(self.project._root / FILE, exists=False, directory=False, scope=False)

    def _read(self):
        raw = self._path().read_bytes()
        require(len(raw) <= 65536, 'SESSION_LIMIT')
        state = json.loads(raw)
        require(canonical_json(state) == raw and state['schema'] == SCHEMA, 'SESSION_INTEGRITY')
        require(state['role_digests'] == {k: v['definition_digest'] for k, v in self.roles.items()},
                'ROLE_BINDING_CHANGED')
        require(fingerprint({k: state[k] for k in ('main_ref', 'host_project_id', 'short_name',
                'profile', 'analysis', 'authorization')}) == state['onboarding_digest'], 'ONBOARDING_CONFLICT')
        for task in state['tasks']:
            require(task['profile'] == state['profile']
                    and task['features'] == DENIED_FEATURES
                    and task['role_definition_digest'] == state['role_digests'][task['role_id']]
                    and task['project_id'] == state['project_id'] and task['main_ref'] == state['main_ref']
                    and fingerprint({k: task[k] for k in BINDING_FIELDS}) == task['binding_digest'],
                    'ROLE_OR_PROFILE_CHANGED')
        return state

    def _save(self, state):
        body = canonical_json(state)
        path = self._path()
        temporary = path.with_name(FILE + '.' + uuid.uuid4().hex + '.tmp')
        with temporary.open('xb') as stream:
            stream.write(body)
            stream.flush()
            os.fsync(stream.fileno())
        _fault('before_replace')
        os.replace(temporary, path)
        _fault('after_replace')

    def _change(self, update):
        # Reuse ResearchProject's existing lock/identity checks. No ResearchProject
        # event or scientific table is modified and no host call holds this lock.
        with self.project._snapshot(write=True) as (_, meta, _bundles, _events):
            state = self._read()
            require(state['project_id'] == meta['research_project_id'], 'PROJECT_BINDING_CHANGED')
            result = update(state)
            state['revision'] += 1
            self._save(state)
            return copy.deepcopy(result)

    def inspect(self):
        with self.project._snapshot() as (_, meta, _bundles, _events):
            state = self._read()
            require(state['project_id'] == meta['research_project_id'], 'PROJECT_BINDING_CHANGED')
            # Interrupted INTENT is never eligible for resubmission.
            for task in state['tasks']:
                if task['state'].endswith('_INTENT'):
                    task['state'] = task['state'].replace('_INTENT', '_UNKNOWN')
            return state

    def onboard(self, port, main_ref, host_project_id, short_name, profile, analysis,
                authorization, managed_names=()):
        reference(main_ref)
        text(host_project_id)
        require(type(short_name) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9 _-]{0,31}', short_name)
                and short_name == short_name.strip(), 'SHORT_NAME_INVALID')
        require(short_name.casefold() not in {n.casefold() for n in managed_names}, 'SHORT_NAME_COLLISION')
        require(set(profile) == {'revision', 'model', 'reasoning_effort', 'approval_ref'}
                and type(profile['revision']) is int and profile['revision'] > 0, 'PROFILE_INVALID')
        for key in ('model', 'reasoning_effort', 'approval_ref'):
            text(profile[key])
        require(set(analysis) == {'question', 'measurable_goal', 'trusted_assets', 'allowed_changes',
                'forbidden_changes', 'evidence_needed', 'budget_control', 'unknowns', 'delegation_reason'},
                'ANALYSIS_REQUIRED')
        for value in analysis.values():
            text(value)
        require(set(authorization) == {'user_evidence_ref', 'actions'}
                and set(authorization['actions']) <= {'rename', 'create_sessions', 'return_results'},
                'USER_AUTHORIZATION_REQUIRED')
        text(authorization['user_evidence_ref'])
        port.check_caller(main_ref, host_project_id)
        port.check_profile(profile)
        binding = {'main_ref': main_ref, 'host_project_id': host_project_id, 'short_name': short_name,
                   'profile': profile, 'analysis': analysis, 'authorization': authorization}
        with self.project._snapshot(write=True) as (_, meta, bundles, _events):
            if self._path().exists():
                state = self._read()
                require(state['onboarding_digest'] == fingerprint(binding), 'ONBOARDING_CONFLICT')
                return state
            require(meta['project_revision'] == 1 and not bundles, 'FRESH_ANALYSIS_PROJECT_REQUIRED')
            state = {'schema': SCHEMA, 'project_id': meta['research_project_id'],
                     'workspace_ref': str(self.project._root), 'revision': 1, **copy.deepcopy(binding),
                     'onboarding_digest': fingerprint(binding), 'main_display_name': short_name + ' Main',
                     'main_name_status': 'NOT_TESTED', 'main_name_receipt': None, 'paused': False,
                     'role_digests': {k: v['definition_digest'] for k, v in self.roles.items()},
                     'tasks': [], 'decisions': [], 'interactions': [], 'execution_authorized': False}
            self._save(state)
            return copy.deepcopy(state)

    def _main(self, port, state):
        port.check_caller(state['main_ref'], state['host_project_id'])

    def _authorize(self, port, state, action):
        require(action in state['authorization']['actions'], 'USER_AUTHORIZATION_REQUIRED')
        port.check_authorization(state['authorization'], action)

    def name_main(self, port):
        state = self.inspect()
        self._main(port, state)
        self._authorize(port, state, 'rename')
        if state['main_name_status'] == 'METADATA_CONFIRMED':
            return state
        # Repeating exact title assignment is safe; never creates another Main.
        receipt = port.set_display_name(state['main_ref'], state['main_display_name'])
        observed = port.observe(state['main_ref'])
        require(observed['ref'] == state['main_ref'] and observed['project_id'] == state['host_project_id']
                and observed['title'] == state['main_display_name'], 'MAIN_METADATA_MISMATCH')
        self._change(lambda s: s.update(main_name_status='METADATA_CONFIRMED', main_name_receipt=receipt))
        return self.inspect()

    def decide(self, port, decision_id, rationale, tasks):
        state = self.inspect()
        self._main(port, state)
        text(decision_id); text(rationale)
        require(type(tasks) is list and len(tasks) <= 16, 'TASK_LIMIT')
        requested = fingerprint({'rationale': rationale, 'tasks': tasks})
        def change(s):
            old = next((d for d in s['decisions'] if d['decision_id'] == decision_id), None)
            if old:
                require(old['request_digest'] == requested, 'IDEMPOTENCY_CONFLICT')
                return
            require(not s['paused'] and len(s['tasks']) + len(tasks) <= 16
                    and len(s['decisions']) < 32, 'SESSION_LIMIT_OR_PAUSED')
            ids = {t['task_id'] for t in s['tasks']}
            for request in tasks:
                require(set(request) == {'task_id', 'role_id', 'purpose', 'evidence_refs', 'output_required'},
                        'TASK_CONTRACT_INVALID')
                for key in ('task_id', 'role_id', 'purpose', 'output_required'): text(request[key])
                require(request['role_id'] in self.roles and request['task_id'] not in ids,
                        'TASK_IDENTITY_CONFLICT')
                require(type(request['evidence_refs']) is list and len(request['evidence_refs']) <= 16,
                        'EVIDENCE_LIMIT')
                for ref in request['evidence_refs']: text(ref)
                ids.add(request['task_id'])
                role = self.roles[request['role_id']]
                index = 1 + sum(t['role_id'] == request['role_id'] for t in s['tasks'])
                title = s['short_name'] + ' ' + role['label'] + (f' {index:02}' if index > 1 else '')
                task = {**copy.deepcopy(request), 'project_id': s['project_id'],
                        'agent_instance_id': 'agent_' + uuid.uuid4().hex,
                        'role_definition_digest': role['definition_digest'],
                        'role_version': role['version'], 'profile': copy.deepcopy(s['profile']),
                        'features': copy.deepcopy(role['features']), 'display_name': title,
                        'main_ref': s['main_ref'], 'main_display_name': s['main_display_name']}
                task['binding_digest'] = fingerprint(task)
                task.update(state='QUEUED', thread_ref=None, create_receipt=None,
                            name_status='NOT_TESTED', actual_model='NOT_EXPOSED',
                            result=None, delivery_receipt=None,
                            capabilities=dict.fromkeys(CAPABILITIES, 'NOT_TESTED'))
                s['tasks'].append(task)
            s['decisions'].append({'decision_id': decision_id, 'request_digest': requested,
                                   'rationale': rationale, 'task_ids': [t['task_id'] for t in tasks]})
        self._change(change)
        return self.inspect()

    def _task(self, s, task_id):
        found = [t for t in s['tasks'] if t['task_id'] == task_id]
        require(len(found) == 1, 'TASK_NOT_FOUND')
        return found[0]

    def dispatch_next(self, port):
        state = self.inspect()
        self._main(port, state)
        task = next((t for t in state['tasks'] if t['state'] != 'DELIVERED'), None)
        if state['paused'] or task is None or task['state'] not in ('QUEUED', 'HOST_BLOCKED'):
            return state
        self._authorize(port, state, 'create_sessions')
        port.check_profile(task['profile'])
        gap = port.scoped_session_gap(self.roles[task['role_id']], task['profile'])
        if gap:
            self._change(lambda s: self._task(s, task['task_id']).update(state='HOST_BLOCKED', blocker=gap))
            return self.inspect()
        request_id = fingerprint({'project_id': state['project_id'], 'task': task['binding_digest']})
        def claim(s):
            t = self._task(s, task['task_id'])
            if s['paused'] or t['state'] not in ('QUEUED', 'HOST_BLOCKED'):
                return False
            require(next(v['task_id'] for v in s['tasks'] if v['state'] != 'DELIVERED') == t['task_id'],
                    'SERIAL_PREDECESSOR_PENDING')
            t.update(state='CREATE_INTENT', request_id=request_id)
            return True
        if not self._change(claim):
            return self.inspect()
        _fault('create_intent_committed')
        try:
            created = port.create_thread(state['host_project_id'], task, self.roles[task['role_id']], request_id)
            reference(created['ref'])
            require(created['ref'] != state['main_ref'], 'INDEPENDENT_CONTEXT_REQUIRED')
            def save(s):
                t = self._task(s, task['task_id'])
                require(t['state'] == 'CREATE_INTENT' and not any(v['thread_ref'] == created['ref']
                        for v in s['tasks']), 'THREAD_IDENTITY_CONFLICT')
                t.update(state='CREATED', thread_ref=created['ref'], create_receipt=created['receipt'])
                t['capabilities']['create_thread'] = 'HOST_RECEIPT'
            self._change(save)
            _fault('created_committed')
        except Exception:
            self._change(lambda s: self._task(s, task['task_id']).update(
                             state='CREATE_UNKNOWN', creation_response_unknown=True)
                         if self._task(s, task['task_id'])['thread_ref'] is None else None)
            return self.inspect()
        return self.refresh(port, task['task_id'], rename=True)

    def reconcile_create(self, port, task_id):
        state = self.inspect(); self._main(port, state)
        task = self._task(state, task_id)
        require(task['state'] == 'CREATE_UNKNOWN', 'CREATE_NOT_UNKNOWN')
        found = port.lookup_creation(task['request_id'])
        if found is None:
            return state
        require(found['request_id'] == task['request_id']
                and found['binding_digest'] == task['binding_digest']
                and found['project_id'] == state['host_project_id'], 'CREATE_RECONCILIATION_MISMATCH')
        reference(found['ref'])
        require(found['ref'] != state['main_ref'] and not any(t['thread_ref'] == found['ref']
                for t in state['tasks']), 'THREAD_IDENTITY_CONFLICT')
        def save(s):
            t = self._task(s, task_id)
            require(t['state'] in ('CREATE_UNKNOWN', 'CREATE_INTENT'), 'CREATE_NOT_UNKNOWN')
            t.update(state='CREATED', thread_ref=found['ref'], create_receipt=found['receipt'],
                     reconciled_from_unknown=True)
        self._change(save)
        return self.refresh(port, task_id)

    def refresh(self, port, task_id, *, rename=False):
        state = self.inspect(); self._main(port, state)
        task = self._task(state, task_id)
        require(task['thread_ref'] is not None, 'CREATE_UNKNOWN_QUERY_ONLY')
        # No creation is reachable here, even when naming or metadata reads fail.
        try:
            if rename:
                self._authorize(port, state, 'rename')
                port.set_display_name(task['thread_ref'], task['display_name'])
            observed = port.observe(task['thread_ref'])
            require(observed['ref'] == task['thread_ref']
                    and observed['project_id'] == state['host_project_id'], 'HOST_PROJECT_MISMATCH')
            require(observed['role_definition_digest'] == task['role_definition_digest']
                    and observed['features'] == task['features']
                    and observed['profile'] == task['profile'], 'HOST_ROLE_OR_PROFILE_UNCONFIRMED')
            def save(s):
                t = self._task(s, task_id)
                t['name_status'] = 'METADATA_CONFIRMED' if observed['title'] == t['display_name'] else 'MISMATCH'
                t['capabilities'].update(project_association='HOST_METADATA', resume_or_read='HOST_METADATA',
                    set_display_name=t['name_status'], configure_fixed_model='HOST_METADATA')
                t['actual_model'] = observed.get('actual_model', 'NOT_EXPOSED')
                if t['state'] in ('CREATED', 'NAMING_UNKNOWN', 'BINDING_BLOCKED'):
                    t['state'] = 'RUNNING' if t['name_status'] == 'METADATA_CONFIRMED' else 'NAMING_UNKNOWN'
            self._change(save)
        except Exception:
            self._change(lambda s: self._task(s, task_id).update(
                             state='BINDING_BLOCKED', binding_failure_observed=True)
                         if self._task(s, task_id)['state'] in ('CREATED', 'RUNNING', 'NAMING_UNKNOWN') else None)
        return self.inspect()

    def collect(self, port, task_id):
        state = self.refresh(port, task_id)
        self._main(port, state)
        task = self._task(state, task_id)
        if task['state'] != 'RUNNING':
            return state
        envelope = port.read_result(task['thread_ref'])
        if envelope is None:
            return state
        require(envelope['source_ref'] == task['thread_ref'] and envelope['source'] == 'HOST_ASSISTANT_FINAL',
                'RESULT_SOURCE_UNCONFIRMED')
        result = envelope['result']
        require(set(result) == {'project_id', 'task_id', 'role_id', 'binding_digest', 'status',
                               'findings', 'unknowns', 'evidence_refs'}, 'RESULT_CONTRACT_INVALID')
        require(all(result[k] == task[k] for k in ('project_id', 'task_id', 'role_id', 'binding_digest')),
                'RESULT_IDENTITY_MISMATCH')
        require(result['status'] in ('REVIEW_COMPLETE', 'BLOCKED', 'INCONCLUSIVE')
                and type(result['evidence_refs']) is list
                and set(result['evidence_refs']) <= set(task['evidence_refs']), 'RESULT_SCOPE_MISMATCH')
        text(result['findings']); text(result['unknowns'])
        def save(s):
            t = self._task(s, task_id)
            if t['result'] is not None:
                require(t['result'] == result, 'RESULT_CONFLICT')
                return
            require(t['state'] == 'RUNNING', 'RESULT_CONFLICT')
            t.update(result=copy.deepcopy(result), state='RESULT_READY')
        self._change(save)
        return self.return_result(port, task_id)

    def return_result(self, port, task_id):
        state = self.inspect(); self._main(port, state)
        self._authorize(port, state, 'return_results')
        task = self._task(state, task_id)
        if task['state'] != 'RESULT_READY':
            return state
        delivery = {'schema': 'aoo-result-delivery-v1', 'source_ref': task['thread_ref'],
                    'main_ref': state['main_ref'], 'result': task['result'],
                    'delivery_id': fingerprint({'binding': task['binding_digest'], 'result': task['result']}),
                    'execution_authorized': False}
        def claim(s):
            t = self._task(s, task_id)
            if t['state'] != 'RESULT_READY': return False
            t.update(state='RETURN_INTENT', delivery=delivery)
            return True
        if not self._change(claim): return self.inspect()
        _fault('return_intent_committed')
        try:
            receipt = port.return_result_to_main(state['main_ref'], delivery)
            require(receipt['target_ref'] == state['main_ref'] and receipt['accepted'] is True,
                    'DELIVERY_UNKNOWN')
            self._change(lambda s: self._task(s, task_id).update(state='DELIVERED', delivery_receipt=receipt))
        except Exception:
            self._change(lambda s: self._task(s, task_id).update(state='RETURN_UNKNOWN', delivery_unknown=True))
        return self.inspect()

    def interact(self, port, task_id, parts):
        state = self.inspect(); task = self._task(state, task_id)
        require(task['thread_ref'] is not None, 'SESSION_NOT_BOUND')
        port.check_caller(task['thread_ref'], state['host_project_id'])
        try:
            observed = port.observe(task['thread_ref'])
            qualified = (observed['ref'] == task['thread_ref']
                and observed['project_id'] == state['host_project_id']
                and observed['role_definition_digest'] == task['role_definition_digest']
                and observed['features'] == task['features'] and observed['profile'] == task['profile'])
        except Exception:
            qualified = False
        # Stops and risks are still acknowledged if role revalidation is unavailable;
        # the trusted caller binding limits which local hub can be paused.
        decisions = route_parts(task, parts if qualified else [p if p.get('kind') in ('STOP', 'RISK')
                                      else {'kind': 'OTHER'} for p in parts])
        stop = any(d['action'] == 'PAUSE_OR_ESCALATE' for d in decisions)
        def save(s):
            require(len(s['interactions']) < 64, 'SESSION_LIMIT')
            s['interactions'].append({'task_id': task_id, 'decisions': decisions})
            if stop: s['paused'] = True
        self._change(save)
        # This pauses only this hub's future dispatch. No Solver control claim.
        return {'decisions': decisions, 'local_dispatch_paused': stop or state['paused'],
                'main_notification': 'PENDING_MAIN_COLLECTION', 'solver_stopped': 'NOT_ASSERTED',
                'local_context': {'role_id': task['role_id'], 'task_id': task_id,
                                  'state': task['state'], 'result': task['result']}}
