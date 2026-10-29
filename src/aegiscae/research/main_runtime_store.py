"""Explicit F1 sidecar. Short SQLite transactions; a separate OS sender lock."""

import os
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path

from aegiscae.contracts.research_contracts import canonical_json, digest_bytes, require
from aegiscae.research import project


FILENAME = "main-runtime-v1.sqlite3"
LOCKFILE = "main-runtime-v1.owner"
SCHEMA = "CREATE TABLE events (sequence INTEGER PRIMARY KEY, body BLOB NOT NULL, digest TEXT NOT NULL)"


def _fault(stage):
    """Trusted offline fault seam; never a client-supplied callback."""


def create_files(root):
    root, _ = project._check_root(root)
    for name in (FILENAME, LOCKFILE):
        path = project._path(root / name, exists=False, directory=False, scope=False)
        require(not path.exists(), "RUNTIME_ALREADY_EXISTS")
    for name in (FILENAME, LOCKFILE):
        path = root / name
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.close(descriptor)


def identities(root):
    return [project._file_id(project._path(root / name, directory=False, scope=False))
            for name in (FILENAME, LOCKFILE)]


@contextmanager
def sender(root):
    # Windows-only finite runtime. Closing the retained handle releases the lock;
    # its file is never deleted/recreated to take over an owner.
    require(os.name == "nt", "UNSUPPORTED_OWNER_PLATFORM")
    import msvcrt
    project._check_root(root)
    path = project._path(root / LOCKFILE, directory=False, scope=False)
    require(path.stat().st_size == 0, "OWNER_INTEGRITY")
    with path.open("rb") as stream:
        try:
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            raise project.ProjectError("OWNER_BUSY") from None
        try:
            yield
        finally:
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)


@contextmanager
def connection_for(root, *, write=False, creating=False):
    connection = None
    try:
        project._check_root(root)
        path = project._path(root / FILENAME, directory=False, scope=False)
        require(path.stat().st_size <= 4 * 1024 * 1024, "RUNTIME_LIMIT")
        for suffix in ("-journal", "-wal", "-shm"):
            require(not Path(str(path) + suffix).exists(), "STORE_BUSY")
        connection = sqlite3.connect(path.as_uri() + ("?mode=rw" if write else "?mode=ro"),
                                     uri=True, isolation_level=None, timeout=2)
        connection.execute("PRAGMA trusted_schema=OFF")
        connection.execute("PRAGMA busy_timeout=2000")
        if not write:
            connection.execute("PRAGMA query_only=ON")
        connection.execute("BEGIN IMMEDIATE" if write else "BEGIN")
        if creating:
            connection.execute(SCHEMA)
        yield connection
    except sqlite3.OperationalError as error:
        raise project.ProjectError("STORE_BUSY" if error.sqlite_errorcode in
            (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED) else "STORE_UNAVAILABLE") from None
    except sqlite3.Error:
        raise project.ProjectError("RUNTIME_INTEGRITY") from None
    finally:
        if connection is not None:
            if connection.in_transaction:
                connection.rollback()
            connection.close()


def read_events(connection):
    schema = dict(connection.execute("SELECT name,sql FROM sqlite_master "
                                     "WHERE type IN ('table','view','trigger')"))
    require(schema == {"events": SCHEMA}, "UNSUPPORTED_RUNTIME_SCHEMA")
    rows = connection.execute("SELECT sequence,body,digest FROM events ORDER BY sequence LIMIT 66").fetchall()
    require(1 <= len(rows) <= 64, "RUNTIME_LIMIT")
    previous, last_time, transactions, result = None, "", set(), []
    for index, (sequence, body, digest) in enumerate(rows, 1):
        event = project._decode(body, digest)
        require(set(event) == {"schema", "sequence", "previous", "transaction_id", "at_utc", "kind", "data"}
                and event["schema"] == "main-runtime-journal-v1"
                and type(event["sequence"]) is int
                and sequence == index == event["sequence"] and event["previous"] == previous,
                "RUNTIME_INTEGRITY")
        from aegiscae.contracts.research_contracts import identifier
        identifier(event["transaction_id"], "runtimetx")
        project._validate_time(event["at_utc"])
        require(event["at_utc"] >= last_time and event["transaction_id"] not in transactions,
                "RUNTIME_INTEGRITY")
        transactions.add(event["transaction_id"])
        previous, last_time = digest, event["at_utc"]
        result.append((event, digest))
    return result


def append(connection, events, kind, data):
    at = project._utc()
    require(len(events) < 64, "RUNTIME_LIMIT")
    require(not events or at >= events[-1][0]["at_utc"], "CLOCK_REGRESSION")
    event = {"schema": "main-runtime-journal-v1", "sequence": len(events) + 1,
             "previous": events[-1][1] if events else None, "transaction_id": "runtimetx_" + uuid.uuid4().hex,
             "at_utc": at, "kind": kind, "data": data}
    body = canonical_json(event)
    require(len(body) <= 65536, "RUNTIME_LIMIT")
    connection.execute("INSERT INTO events VALUES (?,?,?)", (event["sequence"], body, digest_bytes(body)))
    _fault(kind.lower() + "_before_commit")
    connection.commit()
    _fault(kind.lower() + "_after_commit")
