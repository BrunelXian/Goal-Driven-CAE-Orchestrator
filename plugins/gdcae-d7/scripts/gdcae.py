"""Installed D7 preparation CLI. No Operator, submit, Owner start or execution."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re

VERSION = '0.0.0+d7r2f'
PLUGIN_VERSION = '0.1.0-alpha.6-d7r2f'
PACKAGE = Path(__file__).resolve().parents[1]
FILES = ('plugin.json', 'scripts/gdcae.py', 'scripts/candidate.py',
         'skills/setup/SKILL.md', 'skills/research/SKILL.md',
         'references/handoff.md', 'references/runtime-contract.json',
         *(f'agents/gdcae-{role}.toml' for role in ('cae', 'results', 'inverse', 'reviewer')))


def need(ok, code):
    if not ok:
        raise ValueError(code)


def safe_path(path):
    path = Path(path)
    need(path.is_absolute() and not any(p.is_symlink() or p.is_junction()
         for p in (path, *path.parents)), 'UNSAFE_PATH')
    return path.resolve()


def package_files(root=PACKAGE):
    root = safe_path(root)
    result = {}
    for name in FILES:
        path = safe_path(root / name)
        need(path.is_file() and path.stat().st_size <= 65536, 'PACKAGE_INVALID')
        result[name] = path.read_bytes()
    manifest = json.loads(result['plugin.json'])
    contract = json.loads(result['references/runtime-contract.json'])
    need(manifest['name'] == 'gdcae-d7' and manifest['version'] == PLUGIN_VERSION
         and contract['snapshot_version'] == VERSION
         and contract['plugin_version'] == PLUGIN_VERSION
         and contract['workflow'] == 'rod-local-workflow-v2'
         and contract['trust'] == 'TRUSTED_LOCAL_HIL'
         and contract['solver_authorized'] is False, 'PACKAGE_VERSION_MISMATCH')
    return result


def package_digest():
    rows = {k: hashlib.sha256(v).hexdigest() for k, v in sorted(package_files().items())}
    return hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()


def qualified():
    from aegiscae._gdcae_plugin.scripts.gdcae import installed_package
    gd = installed_package('aegiscae', 'aegiscae', expected_version=VERSION)
    af = installed_package('abqjobpilot', 'abqjobpilot_gdcae_internal', expected_version=VERSION)
    need(package_files() == package_files(gd['origin'].parent / '_gdcae_d7_plugin'),
         'PLUGIN_INSTALLED_BYTES_MISMATCH')
    from aegiscae.research.rod_local_project import code_digest
    from abqjobpilot.execution.rod_local_hil import source_digest, plugin_digest, dependency_versions
    from abqjobpilot.execution.standard_contract import PYTHON, identity
    runtime = {'gd': code_digest(), 'af': source_digest(), 'plugin': plugin_digest(PACKAGE),
               'python': identity(PYTHON)['digest'], 'versions': dependency_versions()}
    return {'gd': gd, 'af': af, 'runtime': runtime}


def write_once(path, value):
    body = json.dumps(value, sort_keys=True, indent=2).encode()
    if path.exists():
        need(path.read_bytes() == body, 'IDEMPOTENCY_CONFLICT')
        return
    with path.open('xb') as stream:
        stream.write(body)
        stream.flush()
        os.fsync(stream.fileno())


def initialize(workspace, name, expected):
    q = qualified()
    need(expected == package_digest(), 'PACKAGE_DIGEST_MISMATCH')
    need(re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,63}', name), 'INVALID_NAME')
    root = safe_path(workspace)
    need(root.parent.is_dir() and not root.exists(), 'FRESH_WORKSPACE_REQUIRED')
    need(not root.is_relative_to(PACKAGE) and not root.is_relative_to(Path.home()/'.codex'),
         'WORKSPACE_OUT_OF_SCOPE')
    root.mkdir()
    from aegiscae.research.rod_local_project import create_local_research
    research = create_local_research(root/'research', name, q['runtime'])
    state = research.inspect()
    record = {'schema': 'gdcae-d7-workspace-v1', 'version': VERSION,
              'plugin_digest': expected, 'runtime': q['runtime'],
              'research_project_id': state['research_project_id'],
              'contract_digest': state['contract_digest'],
              'gd_record': q['gd']['receipt'], 'af_record': q['af']['receipt']}
    write_once(root/'d7-v2.json', record)
    return status(root)


def opened(workspace, *, write=False):
    root = safe_path(workspace)
    record = json.loads((root/'d7-v2.json').read_text())
    q = qualified()
    need(record['schema'] == 'gdcae-d7-workspace-v1' and record['version'] == VERSION
         and record['runtime'] == q['runtime'] and record['plugin_digest'] == package_digest()
         and record['gd_record'] == q['gd']['receipt'] and record['af_record'] == q['af']['receipt'],
         'WORKSPACE_RUNTIME_MISMATCH')
    from aegiscae.research import project
    from aegiscae.research.rod_local_project import LocalRodProject
    store = (project.open_existing_for_explicit_write if write else project.open_existing_readonly)
    research = LocalRodProject(store(root/'research'))
    view = research.inspect()
    need(view['research_project_id'] == record['research_project_id']
         and view['contract_digest'] == record['contract_digest'], 'WORKSPACE_IDENTITY_MISMATCH')
    return root, research, view


def status(workspace):
    root, _research, view = opened(workspace)
    return {'schema': 'gdcae-d7-status-v1', 'workflow': 'rod-local-workflow-v2',
            'trust': view['policy']['trust'], 'revision': view['project_revision'],
            'contract_digest': view['contract_digest'], 'candidate': view['candidates']['A'],
            'budget': view['budget'], 'preview_declined': (root/'preview-declined.json').exists(),
            'execution_authorized': False, 'core_version': VERSION, 'plugin_version': PLUGIN_VERSION}


def config_for(root, runtime):
    from abqjobpilot.execution.standard_contract import StandardConfig
    from abqjobpilot.execution.models import canonical_json
    from aegiscae.research.rod_output_v2 import PROFILE
    value = StandardConfig.fixed([
        r'D:\ABAQUS2024\product\win_b64\code\bin\SMALauncher.exe',
        r'D:\ONEAPI\compiler\2022.2.0\env\vars.bat'], managed=True).value()
    value.update(rod_profile=PROFILE, research_runtime=runtime, research_plugin_root=str(PACKAGE))
    return StandardConfig(canonical_json(value))


def prepare_a(workspace, expires_at):
    root, research, view = opened(workspace, write=True)
    need(not (root/'preview-declined.json').exists(), 'PREVIEW_DECLINED')
    from abqjobpilot.product_rod import RodProduct
    from abqjobpilot.execution.models import digest, now
    from aegiscae.research.rod_local_port import LocalReadPort
    from aegiscae.research.rod_output_v2 import TEMPLATE
    need(now() < expires_at <= now()+600, 'APPROVAL_WINDOW_INVALID')
    c = view['candidates']['A']
    nonce = 'preview_' + c['candidate_id'].removeprefix('candidate_')
    intent = {'candidate_id': c['candidate_id'], 'expires_at': expires_at,
              'contract_digest': view['contract_digest'], 'runtime': view['policy']['runtime']}
    write_once(root/'prepare-intent.json', intent)
    path = root/'af-A'
    product = RodProduct(path) if path.exists() else RodProduct.create(path, 'D7 A INERT PREPARATION')
    config = config_for(root, view['policy']['runtime'])
    args = {k: c[k] for k in ('research_project_id', 'contract_digest', 'candidate_id')}
    args.update(research_revision=c['admitted_revision'], request_nonce=nonce)
    plan = product.prepare_real(frozen_template=TEMPLATE, candidate_bytes=research.candidate_input('A'),
        load_n=c['load_n'], config=config, **args, expires_at=expires_at,
        phase='A', local_contract=c['local_contract'])
    binding = {k: plan[k] for k in ('project_id', 'project_instance_id', 'plan_id', 'plan_digest', 'backend_id')}
    binding.update(input_digest=c['input_digest'], resources_digest=digest(plan['resources']),
        output_identity=plan['output_key'], candidate_output_identity=c['output_identity'],
        request_key=nonce, request_nonce=nonce)
    port = LocalReadPort(path, config, view['policy']['runtime'])
    research.hold('A', port, binding, view['project_revision'], 'plugin-hold-A')
    write_once(root/'af-reference.json', {'binding': binding, 'expected': {**args, 'input_digest': c['input_digest']},
                                       'config': config.value()})
    return preflight_a(root)


def prepared(workspace):
    root, research, view = opened(workspace)
    need(not (root/'preview-declined.json').exists(), 'PREVIEW_DECLINED')
    ref = json.loads((root/'af-reference.json').read_text())
    from abqjobpilot.product_rod import RodProduct
    from abqjobpilot.execution.standard_contract import StandardConfig
    from abqjobpilot.execution.models import canonical_json
    need(view['attempts']['A']['binding'] == ref['binding'], 'PLAN_REFERENCE_MISMATCH')
    return root, research, view, ref, RodProduct(root/'af-A'), StandardConfig(canonical_json(ref['config']))


def preflight_a(workspace):
    _root, _research, view, ref, product, config = prepared(workspace)
    b = ref['binding']
    value = product.preflight_real(b['plan_id'], b['plan_digest'], config=config,
                                   expected_contract=ref['expected'])
    return {'schema': 'gdcae-d7-preflight-v1', 'preflight': value, 'budget': view['budget'],
            'owner_runtime': product.owner_runtime_preview(config), 'execution_authorized': False}


def approval_preview(workspace, not_before, expires_at):
    root, _research, view, ref, product, config = prepared(workspace)
    need(view['attempts']['A']['status'] == 'HELD', 'HOLD_REQUIRED')
    b = ref['binding']
    packet = product.a_only_application(b['plan_id'], b['plan_digest'], config=config,
        expected_contract=ref['expected'], nonce=b['request_nonce'],
        not_before=not_before, expires_at=expires_at)
    result = {'schema': 'gdcae-d7-review-preview-v1', 'packet': packet,
              'budget': view['budget'], 'research_revision': view['project_revision'],
              'execution_authorized': False, 'human_decision': 'NOT_ESTABLISHED'}
    write_once(root/'approval-preview.json', result)
    return result


def decline_preview(workspace):
    root, _research, view = opened(workspace)
    write_once(root/'preview-declined.json', {'contract_digest': view['contract_digest'],
        'decision': 'PREVIEW_DECLINED_NOT_AF_DECISION'})
    return {'status': 'PREVIEW_DECLINED_NOT_AF_DECISION', 'budget': view['budget'],
            'grant_issued': False, 'budget_released': False, 'execution_authorized': False}


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError('INVALID_ARGUMENTS')


def main():
    parser = Parser(prog='gdcae-d7')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('doctor')
    sub.add_parser('package-digest')
    for name in ('init-v2', 'status-v2', 'prepare-a', 'preflight-a', 'approval-preview', 'decline-preview'):
        p = sub.add_parser(name)
        p.add_argument('--workspace', type=Path, required=True)
        if name == 'init-v2':
            p.add_argument('--name', required=True)
            p.add_argument('--expected-package-digest', required=True)
        if name in ('prepare-a', 'approval-preview'):
            p.add_argument('--expires-at', type=int, required=True)
        if name == 'approval-preview':
            p.add_argument('--not-before', type=int, required=True)
    try:
        a = parser.parse_args()
        if a.command == 'doctor':
            q = qualified()
            value = {'status': 'INSTALLED_D7_VERIFIED', 'runtime': q['runtime'],
                     'gd': q['gd']['receipt'], 'af': q['af']['receipt'],
                     'entry_path': str(PACKAGE), 'plugin_version': PLUGIN_VERSION,
                     'execution_authorized': False, 'desktop_activation': 'NOT_ATTESTED'}
        elif a.command == 'package-digest':
            value = {'package_sha256': package_digest()}
        elif a.command == 'init-v2':
            value = initialize(a.workspace, a.name, a.expected_package_digest)
        elif a.command == 'status-v2':
            value = status(a.workspace)
        elif a.command == 'prepare-a':
            value = prepare_a(a.workspace, a.expires_at)
        elif a.command == 'preflight-a':
            value = preflight_a(a.workspace)
        elif a.command == 'approval-preview':
            value = approval_preview(a.workspace, a.not_before, a.expires_at)
        else:
            value = decline_preview(a.workspace)
        print(json.dumps(value, sort_keys=True))
        return 0
    except Exception as exc:
        # No paths, private store contents, credentials or traceback on rejection.
        code = getattr(exc, 'code', str(exc) if isinstance(exc, ValueError) else '')
        if not isinstance(code, str) or re.fullmatch(r'[A-Z][A-Z0-9_]{2,63}', code) is None:
            code = 'D7_PREPARATION_BLOCKED'
        print(json.dumps({'status': 'BLOCKED', 'code': code, 'execution_authorized': False}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
