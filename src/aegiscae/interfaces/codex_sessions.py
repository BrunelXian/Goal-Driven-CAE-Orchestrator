"""Thin Codex app tool mapping; no HTTP client or alternate Agent Runtime.

Injected call/context/authorization providers belong to the trusted host bridge,
never to a user-message JSON body. The currently observed app API cannot bind
role/tool restrictions: creation remains blocked even with user authorization.
"""
import json

from aegiscae.contracts.research_contracts import digest_bytes, require
from aegiscae.research.scoped_sessions import reference

TOOLS = {'create_thread': 'mcp__codex_app__create_thread',
         'set_display_name': 'mcp__codex_app__set_thread_title',
         'resume_or_read': 'mcp__codex_app__read_thread',
         'return_result_to_main': 'mcp__codex_app__send_message_to_thread'}


def capability_map():
    """Observed schema facts, not Desktop or model-behavior test results."""
    return {
        'create_thread': {'desktop': 'SOURCE_VERIFIED', 'tool': TOOLS['create_thread'],
                          'production_gate': 'BLOCKED_DESKTOP_ROLE_TOOL_BINDING_NOT_EXPOSED'},
        'set_display_name': {'desktop': 'SOURCE_VERIFIED', 'tool': TOOLS['set_display_name'],
                             'client_result': 'NOT_TESTED'},
        'project_association': {'desktop': 'SOURCE_VERIFIED', 'field': 'target.projectId from list_projects',
                                'client_result': 'NOT_TESTED'},
        'visible_in_target_client': {'desktop': 'NOT_TESTED', 'proof': 'Testing client observation required'},
        'user_can_ask_scoped_question': {'desktop': 'NOT_TESTED', 'proof': 'Testing interactive exchange required'},
        'return_result_to_main': {'desktop': 'SOURCE_VERIFIED', 'tool': TOOLS['return_result_to_main'],
                                  'authorization': 'DIRECT_USER_EVIDENCE_REQUIRED'},
        'resume_or_read': {'desktop': 'SOURCE_VERIFIED', 'tool': TOOLS['resume_or_read'],
                           'limitation': 'read is not resume or user interaction'},
        'configure_fixed_model': {'desktop': 'SOURCE_VERIFIED', 'fields': ['model', 'thinking'],
                                  'actual_model': 'NOT_EXPOSED'},
        'native_subagent': {'api': 'collaboration.spawn_agent', 'role_selector': 'SOURCE_VERIFIED',
            'isolated_context': 'fork_turns=none', 'scope': 'inherited permissions, not OS isolation',
            'returned_identity': 'agent_id and canonical task path; no exposed Desktop thread_ref mapping',
            'display_name': 'NOT_EXPOSED', 'desktop_project_association': 'NOT_EXPOSED',
            'user_scoped_question': 'NOT_TESTED',
            'return_to_parent': 'SOURCE_VERIFIED automatic native result notification',
            'selection': 'PREFERRED_WHEN_COMPLETE_SESSION_REQUIREMENTS_ARE_QUALIFIED'},
        'caller_origin': 'HOST_CALLER_CONTEXT_PROVIDER_REQUIRED_NOT_CHAT_TEXT',
        'create_idempotency': 'NO_HOST_KEY_EXPOSED_INTENT_UNKNOWN_NEVER_RECREATE'}


def unpack(value):
    require(type(value) is dict and not value.get('isError'), 'HOST_TOOL_ERROR')
    if 'content' in value:
        blocks = [c['text'] for c in value['content'] if c.get('type') == 'text']
        require(len(blocks) == 1, 'HOST_RESPONSE_AMBIGUOUS')
        return json.loads(blocks[0])
    return value


def receipt(value):
    return {'host_response_digest': digest_bytes(json.dumps(value, sort_keys=True).encode())}


class CodexAppSessions:
    """SOURCE_VERIFIED mapping; missing role binding is not user-overridable."""
    def __init__(self, call, *, caller_context=None, authorize=None, models=None):
        self.call, self.caller_context, self.authorize, self.models = call, caller_context, authorize, models

    def check_caller(self, expected, project_id):
        require(self.caller_context is not None, 'HOST_CALLER_CONTEXT_NOT_EXPOSED')
        actual = self.caller_context()
        require(actual.get('source') == 'TRUSTED_HOST_CONTEXT' and actual.get('ref') == expected
                and actual.get('project_id') == project_id, 'MAIN_OR_SESSION_CALLER_MISMATCH')

    def check_profile(self, profile):
        require(self.models is not None, 'HOST_MODEL_QUALIFICATION_REQUIRED')
        # Supplied current host catalog, not an embedded model-name list.
        catalog = self.models()
        require(profile['model'] in catalog and profile['reasoning_effort'] in catalog[profile['model']],
                'PROJECT_PRESET_UNAVAILABLE')

    def check_authorization(self, authorization, action):
        require(self.authorize is not None and self.authorize(authorization['user_evidence_ref'], action) is True,
                'DIRECT_USER_AUTHORIZATION_REQUIRED')

    def scoped_session_gap(self, role, profile):
        return 'BLOCKED_DESKTOP_ROLE_TOOL_BINDING_NOT_EXPOSED'

    def create_thread(self, project_id, task, role, request_id):
        # Prompt text/RoleBinding JSON cannot enable this path. Current create
        # schema has neither native role selection nor denied-feature controls.
        require(False, 'BLOCKED_DESKTOP_ROLE_TOOL_BINDING_NOT_EXPOSED')

    def lookup_creation(self, request_id):
        # No supported request-key lookup in the observed Desktop tool schema.
        # Do not scan unrelated history or equate a title match with ownership.
        return None

    @staticmethod
    def creation_spec(project_id, task, role, request_id):
        """Reviewable mapping only, never calls the host. Not an execution permit."""
        prompt = ('AOO scoped assignment. Request correlation: ' + request_id + '\n'
                  + '\n'.join(role['instructions']) + '\n'
                  + json.dumps({k: task[k] for k in ('project_id', 'task_id', 'role_id', 'binding_digest',
                     'purpose', 'evidence_refs', 'output_required', 'main_ref', 'main_display_name')}, sort_keys=True))
        return {'tool': TOOLS['create_thread'], 'args': {
            'target': {'type': 'project', 'projectId': project_id, 'environment': {'type': 'local'}},
            'title': task['display_name'], 'model': task['profile']['model'],
            'thinking': task['profile']['reasoning_effort'], 'prompt': prompt},
            'dispatch_allowed': False, 'blocker': 'BLOCKED_DESKTOP_ROLE_TOOL_BINDING_NOT_EXPOSED'}

    def set_display_name(self, ref, title):
        reference(ref)
        require(self.caller_context is not None and self.caller_context()['ref']['host_id'] == ref['host_id'],
                'CROSS_HOST_RENAME_UNSUPPORTED')
        result = self.call(TOOLS['set_display_name'], {'threadId': ref['thread_id'], 'title': title})
        unpack(result)
        return receipt(result)

    def _read(self, ref):
        reference(ref)
        return unpack(self.call(TOOLS['resume_or_read'], {'threadId': ref['thread_id'],
            'hostId': ref['host_id'], 'turnLimit': 4, 'includeOutputs': False}))

    def observe(self, ref):
        value = self._read(ref)
        thread = value['thread']
        require(thread['id'] == ref['thread_id'] and thread['hostId'] == ref['host_id'], 'HOST_THREAD_MISMATCH')
        return {'ref': ref, 'project_id': thread.get('projectId', 'NOT_EXPOSED'), 'title': thread['title'],
                'role_definition_digest': 'NOT_EXPOSED', 'features': 'NOT_EXPOSED',
                'profile': 'NOT_EXPOSED', 'actual_model': 'NOT_EXPOSED',
                'visible_in_target_client': 'NOT_TESTED', 'user_can_ask_scoped_question': 'NOT_TESTED'}

    def read_result(self, ref):
        value = self._read(ref)
        require(value['thread']['id'] == ref['thread_id'] and value['thread']['hostId'] == ref['host_id'],
                'HOST_THREAD_MISMATCH')
        turns = value.get('turns', [])
        if not turns or turns[0].get('status') != 'completed': return None
        messages = [m for m in turns[0].get('items', []) if m.get('type') == 'agentMessage'
                    and m.get('phase') in ('final', 'final_answer')]
        require(len(messages) == 1, 'RESULT_FINAL_UNAVAILABLE')
        return {'source_ref': ref, 'source': 'HOST_ASSISTANT_FINAL',
                'result': json.loads(messages[0]['text'])}

    def return_result_to_main(self, ref, delivery):
        value = unpack(self.call(TOOLS['return_result_to_main'], {'threadId': ref['thread_id'],
            'hostId': ref['host_id'], 'prompt': json.dumps(delivery, sort_keys=True)}))
        require(value.get('threadId') == ref['thread_id'], 'DELIVERY_UNKNOWN')
        return {'target_ref': ref, 'accepted': True, **receipt(value)}
