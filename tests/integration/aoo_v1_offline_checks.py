"""Exact AOO whitelist under a fresh-run write and SQLite boundary.

Launch via the absolute approved interpreter with -I -B and --source-root.
No discovery from environment/config/conftest, and no real host or AF tests.
"""
import argparse
import contextlib
import json
import os
from pathlib import Path
import sys
import uuid


def main():
    if not (sys.flags.isolated and sys.flags.ignore_environment and sys.flags.dont_write_bytecode):
        raise RuntimeError('AOO_ISOLATED_MINUS_I_MINUS_B_REQUIRED')
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--evidence-root', type=Path, required=True)
    parser.add_argument('--label', required=True)
    args = parser.parse_args()
    source, root = args.source_root, args.evidence_root
    for path in (source, root):
        if not path.is_absolute() or any(p.is_symlink() or p.is_junction() for p in (path, *path.parents)):
            raise ValueError('AOO_ABSOLUTE_REGULAR_ROOT_REQUIRED')
    source, root = source.resolve(), root.resolve()
    if source != Path(__file__).resolve().parents[2]:
        raise ValueError('AOO_RUNNER_SOURCE_ROOT_MISMATCH')
    if (root.parent != Path('D:/Projects/GDCAETEST').resolve()
            or not root.name.startswith('AOO-V1-01-') or not root.is_dir()
            or not args.label.isascii() or not args.label.isalnum()):
        raise ValueError('AOO_EVIDENCE_SCOPE_REQUIRED')
    sys.path[:0] = [str(source/'src'), str(source/'tests/integration')]
    import aoo_v1_guard as boundary
    cleared = boundary.clean_environment()
    run = root/args.label
    run.mkdir()
    guard = boundary.Guard(run)
    guard.expected = dict.fromkeys(guard.counts, 0)
    guard.install()
    import tempfile
    tempfile.tempdir = str(run)
    os.environ['TEMP'] = os.environ['TMP'] = str(run)
    config_path = run/'pytest-empty.ini'
    config_path.write_text('[pytest]\n', encoding='utf-8')
    tests = [source/'tests/unit'/name for name in boundary.TEST_NAMES]
    boundary.validate_selection(tests, source)
    import pytest
    collected = []

    class Collection:
        @pytest.fixture
        def tmp_path(self):
            # Standard fixture override: no pytest "current" symlink attempts,
            # no retention cleanup, and every case stays in this fresh run.
            parent = run/'tmp'
            parent.mkdir(exist_ok=True)
            path = parent/('case_' + uuid.uuid4().hex)
            path.mkdir()
            return path

        @pytest.hookimpl(tryfirst=True)
        def pytest_load_initial_conftests(self, early_config, parser, args):
            boundary.validate_selection(early_config.known_args_namespace.file_or_dir, source)
            if not early_config.known_args_namespace.noconftest:
                raise pytest.UsageError('AOO_CONFTEST_FORBIDDEN')

        def pytest_ignore_collect(self, collection_path, config):
            if collection_path.suffix == '.py' and collection_path.resolve() not in tests:
                return True

        def pytest_collect_file(self, file_path, parent):
            if file_path.suffix == '.py' and file_path.resolve() not in tests:
                raise pytest.UsageError('AOO_PREIMPORT_FILE_DENIED')

        def pytest_collection_modifyitems(self, session, config, items):
            if any(Path(item.path).resolve() not in tests for item in items):
                raise pytest.UsageError('AOO_UNREVIEWED_TEST_SELECTION_DENIED')

        def pytest_collection_finish(self, session):
            collected.extend(item.nodeid for item in session.items)

    pytest_args = [str(p) for p in tests] + ['-q', '--tb=short', '-c', str(config_path),
        '--rootdir', str(source), '--noconftest', '--confcutdir', str(source/'tests/unit'),
        '--import-mode=importlib', '-p', 'no:cacheprovider', '-p', 'no:logging',
        '--basetemp', str(run/'tmp'), '--junitxml', str(run/'junit.xml')]
    with (run/'pytest.log').open('x', encoding='utf-8') as output:
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            code = pytest.main(pytest_args, plugins=[Collection()])
    unexpected = {k: guard.counts[k] - guard.expected[k] for k in guard.counts}
    final_code = int(code) if code else int(any(unexpected.values()))
    result = {'schema': 'aoo-v1-developer-tests-v2', 'exit_code': final_code, 'pytest_exit_code': int(code),
        'source_root': str(source), 'write_root': str(run), 'collected': len(collected), 'nodeids': collected,
        'boundary': guard.counts, 'expected_negative_probes': guard.expected, 'unexpected_denials': unexpected,
        'path_denials': guard.path_denials,
        'interpreter': sys.executable, 'python': sys.version, 'isolated': bool(sys.flags.isolated),
        'dont_write_bytecode': bool(sys.flags.dont_write_bytecode), 'cleared_environment_keys': cleared,
        'pytest_args': pytest_args, 'conftest_loading': False, 'plugin_autoload': False,
        'tmp_path_fixture': 'fresh_run_uuid_directory_no_symlink_no_cleanup',
        'real_codex_sessions': 0, 'real_model_calls': 0, 'af_imports_allowed': False,
        'owner_grant_run_solver_authorized': False}
    (run/'result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k not in ('nodeids', 'pytest_args', 'path_denials')}))
    return final_code


if __name__ == '__main__':
    raise SystemExit(main())
