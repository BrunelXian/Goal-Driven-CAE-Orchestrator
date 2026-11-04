"""Negative probes for the exact D7 developer-only test boundary."""
import importlib
import sqlite3
import subprocess
import sys
import pytest
import d7_recovery_guard as boundary


def denied(category, operation):
    guard = boundary.base.ACTIVE
    assert guard is not None, 'USE_D7_ISOLATED_RUNNER'
    before = guard.counts.copy()
    with pytest.raises((PermissionError, sqlite3.DatabaseError)):
        operation()
    assert guard.counts[category] == before[category] + 1
    guard.expected[category] += 1


def test_persistent_grant_schema_forbidden(tmp_path):
    with sqlite3.connect(tmp_path / 'synthetic.sqlite3') as conn:
        denied('sqlite_denied', lambda: conn.execute('CREATE TABLE grants(id TEXT)'))


def test_memory_fixture_cannot_attach_outside_database(tmp_path):
    with sqlite3.connect(':memory:') as conn:
        conn.execute('CREATE TABLE grants(id INTEGER)')
        conn.execute('INSERT INTO grants VALUES(1)')
        denied('sqlite_denied', lambda: conn.execute('ATTACH DATABASE ? AS outside',
               (str(tmp_path / 'attached.sqlite3'),)))
        denied('sqlite_denied', lambda: conn.set_authorizer(None))
    assert not (tmp_path / 'attached.sqlite3').exists()


def test_no_external_write_process_or_af_import():
    guard = boundary.base.ACTIVE
    path = guard.run.parent / 'forbidden-side-effect.txt'
    denied('outside_write_denied', lambda: path.write_text('forbidden'))
    denied('sqlite_denied', lambda: sqlite3.connect(path))
    denied('native_network_denied', lambda: subprocess.run([sys.executable, '-V']))
    denied('af_import_denied', lambda: __import__('abqjobpilot'))
    assert not path.exists()


def test_selection_must_be_exact():
    with pytest.raises(PermissionError, match='UNREVIEWED_TEST_SELECTION_DENIED'):
        boundary.validate_selection([], boundary.base.ACTIVE.run)
