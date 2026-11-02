"""Negative probes: deny effects before changing frozen inputs or history."""
import os
from pathlib import Path
import sqlite3

import pytest
import aoo_v1_guard as boundary


@pytest.fixture
def guard():
    assert boundary.ACTIVE is not None, 'USE_ISOLATED_AOO_RUNNER'
    return boundary.ACTIVE


def denied(guard, category, operation):
    before = guard.counts.copy()
    with pytest.raises((PermissionError, sqlite3.DatabaseError)):
        operation()
    assert guard.counts[category] == before[category] + 1
    assert all(guard.counts[k] == before[k] for k in before if k != category)
    guard.expected[category] += 1


@pytest.mark.parametrize('name', ['MANIFEST.json', 'AOO-V1-01-source-candidate01.zip', 'dev05/result.json'])
@pytest.mark.parametrize('operation', ['overwrite', 'delete', 'rename_out', 'replace_in'])
def test_frozen_and_historical_files_cannot_change(guard, tmp_path, name, operation):
    protected = guard.run.parent/name
    before = protected.read_bytes()
    new = tmp_path/'new.txt'
    new.write_text('new run only')
    actions = {'overwrite': lambda: protected.write_bytes(b'forbidden'),
               'delete': lambda: protected.unlink(),
               'rename_out': lambda: protected.rename(tmp_path/'stolen'),
               'replace_in': lambda: os.replace(new, protected)}
    denied(guard, 'outside_write_denied', actions[operation])
    assert protected.read_bytes() == before and new.read_text() == 'new run only'


def test_other_run_and_external_files_cannot_be_created(guard):
    paths = [guard.run.parent/'dev05/forbidden-new-file',
             guard.run.parent.parent/'AOO-guard-forbidden-external-file']
    for path in paths:
        assert not path.exists()
        denied(guard, 'outside_write_denied', lambda: path.write_bytes(b'forbidden'))
        assert not path.exists()


@pytest.mark.parametrize('kind', ['external', 'historical', 'frozen', 'relative', 'encoded_uri'])
def test_sqlite_external_and_history_connections_denied(guard, kind):
    paths = {'external': guard.run.parent.parent/'AOO-forbidden-external.sqlite3',
             'historical': guard.run.parent/'dev05/forbidden-db.sqlite3',
             'frozen': guard.run.parent/'MANIFEST.json',
             'relative': Path('forbidden-relative.sqlite3'),
             'encoded_uri': guard.run.parent/'dev05/forbidden-encoded.sqlite3'}
    path = paths[kind]
    before = path.read_bytes() if path.is_file() else None
    value = path.as_uri().replace('dev05', '%64ev05')+'?mode=rwc' if kind == 'encoded_uri' else path
    denied(guard, 'sqlite_denied', lambda: sqlite3.connect(value, uri=kind=='encoded_uri'))
    assert (path.read_bytes() if path.is_file() else None) == before


@pytest.mark.parametrize('query', ['mode=rw&mode=rwc', 'mode=rwc&vfs=unix-none', 'mode=memory',
                                  'mode=rw&immutable=1', 'mode=rw#fragment'])
def test_sqlite_uri_options_not_allowlisted(guard, tmp_path, query):
    path = tmp_path/'uri.sqlite3'
    denied(guard, 'sqlite_denied', lambda: sqlite3.connect(path.as_uri()+'?'+query, uri=True))
    assert not path.exists()


@pytest.mark.parametrize('constructor', [boundary.ORIGINAL_CONNECT, boundary.ORIGINAL_CONNECTION])
def test_raw_sqlite_alias_or_constructor_cannot_bypass_wrapper(guard, tmp_path, constructor):
    path = tmp_path/'unguarded.sqlite3'
    denied(guard, 'sqlite_denied', lambda: constructor(path))
    assert not path.exists()


def test_caller_factory_denied_before_callback(guard, tmp_path):
    called = []
    def factory(*args, **kwargs): called.append(True)
    denied(guard, 'sqlite_denied', lambda: sqlite3.connect(tmp_path/'factory.sqlite3', factory=factory))
    assert not called


@pytest.mark.parametrize('sql', ['ATTACH DATABASE ? AS outside', 'VACUUM INTO ?'])
def test_attach_and_vacuum_into_cannot_write_external_db(guard, tmp_path, sql):
    target = guard.run.parent/'dev05/forbidden-attached.sqlite3'
    assert not target.exists()
    conn = sqlite3.connect(tmp_path/'local.sqlite3')
    try: denied(guard, 'sqlite_denied', lambda: conn.execute(sql, (str(target),)))
    finally: conn.close()
    assert not target.exists()


@pytest.mark.parametrize('sql', ['PRAGMA writable_schema=ON', 'PRAGMA journal_mode=WAL',
    "PRAGMA temp_store_directory='C:/Windows/Temp'", "PRAGMA data_store_directory='C:/Windows/Temp'",
    'CREATE TABLE grants(id TEXT)'])
def test_sqlite_authorizer_denies_unsafe_controls(guard, tmp_path, sql):
    conn = sqlite3.connect(tmp_path/'controls.sqlite3')
    try: denied(guard, 'sqlite_denied', lambda: conn.execute(sql))
    finally: conn.close()


def test_authorizer_cannot_be_accidentally_removed_and_extensions_denied(guard):
    conn = sqlite3.connect(':memory:')
    try:
        denied(guard, 'sqlite_denied', lambda: conn.set_authorizer(None))
        denied(guard, 'sqlite_denied', lambda: conn.enable_load_extension(True))
        denied(guard, 'sqlite_denied', lambda: conn.load_extension('nonexistent'))
    finally: conn.close()


def test_new_run_database_read_write_and_readonly_uri_work(guard, tmp_path):
    path = tmp_path/'normal.sqlite3'
    conn = sqlite3.connect(path)
    conn.execute('CREATE TABLE value(n INTEGER)'); conn.execute('INSERT INTO value VALUES(7)')
    conn.commit(); conn.close()
    conn = sqlite3.connect(path.as_uri()+'?mode=ro', uri=True)
    assert conn.execute('SELECT n FROM value').fetchone()[0] == 7
    conn.close()


@pytest.mark.parametrize('mode', ['path', 'ro', 'rw'])
def test_existing_historical_database_bytes_are_unchanged(guard, mode):
    candidates = sorted((guard.run.parent/'dev05/tmp').rglob('research.sqlite3'))
    assert candidates, 'ORIGINAL_DEV05_HISTORY_REQUIRED'
    path = candidates[0]
    before = path.read_bytes()
    value = path if mode == 'path' else path.as_uri()+'?mode='+mode
    denied(guard, 'sqlite_denied', lambda: sqlite3.connect(value, uri=mode!='path'))
    assert path.read_bytes() == before


def test_frozen_source_file_is_outside_run_write_scope(guard):
    path = Path(__file__).resolve()
    before = path.read_bytes()
    denied(guard, 'outside_write_denied', lambda: path.write_bytes(b'forbidden'))
    assert path.read_bytes() == before


def test_link_creation_cannot_escape_through_new_run(guard, tmp_path):
    link = tmp_path/'history-link'
    denied(guard, 'outside_write_denied', lambda: link.symlink_to(guard.run.parent/'dev05', target_is_directory=True))
    assert not link.exists()


def test_preimport_selection_rejects_extra_or_replaced_test_file():
    root = Path(__file__).resolve().parents[2]
    allowed = [root/'tests/unit'/name for name in boundary.TEST_NAMES]
    assert boundary.validate_selection(allowed, root) == allowed
    for selected in (allowed+[root/'tests/unit/test_research_project.py'], allowed[:1], list(reversed(allowed))):
        with pytest.raises(PermissionError, match='AOO_UNREVIEWED_TEST_SELECTION_DENIED'):
            boundary.validate_selection(selected, root)


def test_injection_environment_cleaned_and_source_isolated():
    import sys
    assert sys.flags.isolated and sys.flags.ignore_environment and sys.flags.dont_write_bytecode
    assert not any(k in os.environ for k in boundary.INJECTED_ENV)
    assert os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] == '1'


def test_pytest_configuration_cannot_load_unreviewed_config_or_conftest(pytestconfig, guard):
    root = Path(__file__).resolve().parents[2]
    assert Path(pytestconfig.inipath) == guard.run/'pytest-empty.ini'
    assert pytestconfig.getoption('noconftest') is True
    assert pytestconfig.getoption('importmode') == 'importlib'
    assert not pytestconfig.pluginmanager._conftest_plugins
    boundary.validate_selection(pytestconfig.args, root)
