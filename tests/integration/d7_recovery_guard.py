"""Reuse the offline audit boundary; allow AF-table fixtures only in :memory:.

No AF package import, persistent Grant table, process or network is permitted.
This is accidental-side-effect protection for reviewed tests, not an OS sandbox.
"""
from pathlib import Path
import sqlite3
import aoo_v1_guard as base

TEST_NAMES = ('test_d7_expired_recovery.py', 'test_research_project.py',
              'test_d6_a_only.py', 'test_d7r2f_plugin.py', 'test_d7_recovery_guard.py')
clean_environment = base.clean_environment


def validate_selection(paths, source_root):
    expected = [source_root / 'tests/unit' / name for name in TEST_NAMES]
    if [Path(p).resolve() for p in paths] != expected:
        raise PermissionError('D7_UNREVIEWED_TEST_SELECTION_DENIED')
    return expected


class Guard(base.Guard):
    def connect(self, database, *args, **kwargs):
        conn = super().connect(database, *args, **kwargs)
        if database == ':memory:':
            # Only ephemeral rows used to prove rejection of nonzero evidence.
            # All other restrictions (ATTACH, extensions, etc.) still apply.
            def memory_authorizer(action, first, second, db, source):
                if action in (sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE,
                              sqlite3.SQLITE_CREATE_TABLE, sqlite3.SQLITE_DROP_TABLE):
                    if (first or '').lower() in ('grants', 'management_grants'):
                        first = ''
                return self.authorizer(action, first, second, db, source)
            base.ORIGINAL_CONNECTION.set_authorizer(conn, memory_authorizer)
        return conn
