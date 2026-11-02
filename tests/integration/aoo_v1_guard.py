"""Narrow AOO test guard, installed before pytest or test-module collection.

Accidental-side-effect defense for an exact reviewed selection, not a sandbox
against hostile Python that rewrites this module or calls native APIs directly.
"""
import os
from pathlib import Path
import sqlite3
import sys
import threading
from urllib.parse import parse_qsl, unquote, urlsplit

ORIGINAL_CONNECT = sqlite3.connect
ORIGINAL_CONNECTION = sqlite3.Connection
ACTIVE = None
TEST_NAMES = ('test_scoped_sessions.py', 'test_aoo_v1_guard.py')
INJECTED_ENV = ('PYTEST_ADDOPTS', 'PYTEST_PLUGINS', 'PYTHONPATH', 'PYTHONHOME',
                'PYTHONSTARTUP', 'PYTHONINSPECT', 'PYTHONPYCACHEPREFIX')


def clean_environment():
    removed = sorted(name for name in os.environ if name in INJECTED_ENV or name.startswith('PYTEST_'))
    for name in removed:
        os.environ.pop(name, None)
    os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
    return removed  # Do not expose environment values.


def validate_selection(paths, source_root):
    expected = [source_root / 'tests/unit' / name for name in TEST_NAMES]
    if [Path(p).resolve() for p in paths] != expected:
        raise PermissionError('AOO_UNREVIEWED_TEST_SELECTION_DENIED')
    return expected


class Guard:
    def __init__(self, run):
        self.run = Path(run).resolve()
        self.local = threading.local()
        self.path_denials = []
        self.counts = dict.fromkeys(('native_network_denied', 'af_import_denied',
                                   'outside_write_denied', 'sqlite_denied'), 0)

    def deny(self, category, code):
        self.counts[category] += 1
        raise PermissionError(code)

    def scoped_path(self, value, category='outside_write_denied'):
        if not isinstance(value, (str, os.PathLike)):
            self.path_denials.append({'event': getattr(self.local, 'event', None), 'type': type(value).__name__})
            self.deny(category, 'AOO_PATH_INVALID')
        path = Path(value)
        if (not path.is_absolute() or '..' in path.parts
                or any(p.is_symlink() or p.is_junction() for p in (path, *path.parents))
                or not path.resolve().is_relative_to(self.run)):
            self.path_denials.append({'event': getattr(self.local, 'event', None), 'path': str(path)})
            self.deny(category, 'AOO_NEW_RUN_SCOPE_REQUIRED')
        return path.resolve()

    def database_path(self, value):
        if value == ':memory:':
            return
        if isinstance(value, str) and value.startswith('file:'):
            uri = urlsplit(value)
            pairs = parse_qsl(uri.query, keep_blank_values=True)
            if uri.netloc or uri.fragment or pairs not in ([('mode', 'ro')], [('mode', 'rw')], [('mode', 'rwc')]):
                self.deny('sqlite_denied', 'AOO_SQLITE_URI_DENIED')
            raw = unquote(uri.path, errors='strict')
            if len(raw) > 2 and raw[0] == '/' and raw[2] == ':': raw = raw[1:]
            value = raw
        self.scoped_path(value, 'sqlite_denied')

    def audit(self, event, values):
        self.local.event = event
        if event == 'import' and str(values[0]).split('.')[0] == 'abqjobpilot':
            self.deny('af_import_denied', 'AOO_AF_IMPORT_ISSUER_DENIED')
        if event in {'subprocess.Popen', 'os.system', 'os.exec', 'os.spawn', 'os.startfile',
                     'os.startfile/2', 'socket.connect', 'socket.bind'}:
            self.deny('native_network_denied', 'AOO_NATIVE_NETWORK_DENIED')
        if event == 'sqlite3.connect':
            if not getattr(self.local, 'opening', False):
                self.deny('sqlite_denied', 'AOO_UNGUARDED_SQLITE_CONNECT_DENIED')
            self.local.opening = False
            self.local.pending_handle = True
            self.database_path(values[0])
        elif event == 'sqlite3.connect/handle':
            if not getattr(self.local, 'busy', False) or not getattr(self.local, 'pending_handle', False):
                self.deny('sqlite_denied', 'AOO_UNGUARDED_SQLITE_HANDLE_DENIED')
            self.local.pending_handle = False
        targets = []
        if event == 'open' and not isinstance(values[0], int):
            mode, flags = values[1:3]
            if (isinstance(mode, str) and any(c in mode for c in 'wax+')) or (
                    isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)):
                targets = [values[0]]
        elif event in ('os.mkdir', 'os.remove', 'os.rmdir', 'os.chmod', 'os.utime', 'os.truncate'):
            targets = [values[0]]
        elif event in ('os.rename', 'os.replace'):
            targets = list(values[:2])
        elif event in ('os.link', 'os.symlink'):
            self.deny('outside_write_denied', 'AOO_LINK_CREATION_DENIED')
        for target in targets:
            self.scoped_path(target)

    def authorizer(self, action, first, second, database, source):
        forbidden = action in (sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH)
        if action == sqlite3.SQLITE_PRAGMA:
            pragma = (first or '').lower()
            forbidden |= pragma in ('writable_schema', 'temp_store_directory', 'data_store_directory')
            forbidden |= pragma == 'journal_mode' and second is not None and second.lower() != 'delete'
        if action == sqlite3.SQLITE_FUNCTION:
            forbidden |= (second or '').lower() in ('load_extension', 'writefile', 'readfile')
        if action in (sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE,
                      sqlite3.SQLITE_CREATE_TABLE, sqlite3.SQLITE_DROP_TABLE):
            forbidden |= (first or '').lower() in ('grants', 'management_grants')
        if forbidden:
            self.counts['sqlite_denied'] += 1
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    def connect(self, database, *args, **kwargs):
        if args or set(kwargs) - {'timeout', 'detect_types', 'isolation_level', 'check_same_thread',
                                 'cached_statements', 'uri', 'autocommit'}:
            self.deny('sqlite_denied', 'AOO_SQLITE_FACTORY_OR_ARGUMENTS_DENIED')
        if getattr(self.local, 'busy', False):
            self.deny('sqlite_denied', 'AOO_REENTRANT_SQLITE_DENIED')
        self.database_path(database)
        # All URIs must be explicitly enabled, never interpreted as path strings.
        if isinstance(database, str) and database.startswith('file:') and kwargs.get('uri') is not True:
            self.deny('sqlite_denied', 'AOO_SQLITE_URI_DENIED')
        self.local.busy = self.local.opening = True
        conn = None
        try:
            conn = ORIGINAL_CONNECT(database, factory=GuardedConnection, **kwargs)
            ORIGINAL_CONNECTION.set_authorizer(conn, self.authorizer)
            conn.execute('PRAGMA temp_store=MEMORY')
            conn.execute('PRAGMA trusted_schema=OFF')
            return conn
        except BaseException:
            if conn is not None:
                conn.close()
            raise
        finally:
            self.local.busy = self.local.opening = self.local.pending_handle = False

    def install(self):
        global ACTIVE
        if ACTIVE is not None or any(n.split('.')[0] in ('abqjobpilot', 'pytest', '_pytest') for n in sys.modules):
            raise RuntimeError('AOO_GUARD_ALREADY_ACTIVE_OR_AF_PYTEST_PRELOADED')
        ACTIVE = self
        sys.addaudithook(self.audit)
        sqlite3.connect = sqlite3.dbapi2.connect = self.connect


class GuardedConnection(ORIGINAL_CONNECTION):
    def set_authorizer(self, callback):
        ACTIVE.deny('sqlite_denied', 'AOO_AUTHORIZER_REPLACEMENT_DENIED')

    def enable_load_extension(self, enabled):
        ACTIVE.deny('sqlite_denied', 'AOO_SQLITE_EXTENSION_DENIED')

    def load_extension(self, *args, **kwargs):
        ACTIVE.deny('sqlite_denied', 'AOO_SQLITE_EXTENSION_DENIED')
