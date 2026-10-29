"""Fixed Project-owned v1 proposal sidecar. Never migrates the Project database."""

import os
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path

from aegiscae.contracts.research_contracts import canonical_json, digest_bytes, require
from aegiscae.research import project as store


FILENAME = "proposal-ingress-v1.sqlite3"
SCHEMA = "CREATE TABLE events (sequence INTEGER PRIMARY KEY, body BLOB NOT NULL, digest TEXT NOT NULL)"


def _fault(stage):
    """Trusted failure injection only."""


def identity(root):
    path = store._path(root / FILENAME, directory=False, scope=False)
    return store._file_id(path)


def create_file(root):
    # Exclusive creation; failure leaves a closed/blocked file, never overwritten.
    root, _ = store._check_root(root)
    path = store._path(root / FILENAME, exists=False, directory=False, scope=False)
    require(not path.exists(), "INGRESS_ALREADY_EXISTS")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.close(descriptor)


@contextmanager
def connection_for(root, *, write=False, creating=False):
    connection = None
    try:
        store._check_root(root)
        path = store._path(root / FILENAME, directory=False, scope=False)
        require(path.stat().st_size <= 1024 * 1024, "INGRESS_INTEGRITY")
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
    except sqlite3.OperationalError as exc:
        raise store.ProjectError("STORE_BUSY" if exc.sqlite_errorcode in
            (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED) else "STORE_UNAVAILABLE") from None
    except sqlite3.Error:
        raise store.ProjectError("INGRESS_INTEGRITY") from None
    finally:
        if connection is not None:
            if connection.in_transaction:
                connection.rollback()
            connection.close()


def read_events(connection):
    schema = dict(connection.execute("SELECT name,sql FROM sqlite_master "
                                     "WHERE type IN ('table','view','trigger')"))
    require(schema == {"events": SCHEMA}, "UNSUPPORTED_INGRESS_SCHEMA")
    rows = connection.execute("SELECT sequence,body,digest FROM events ORDER BY sequence LIMIT 6").fetchall()
    require(1 <= len(rows) <= 4, "INGRESS_INTEGRITY")
    previous, at, result = None, "", []
    transactions = set()
    for index, (seq, body, digest) in enumerate(rows, 1):
        event = store._decode(body, digest)
        require(set(event) == {"schema", "sequence", "previous", "at_utc", "transaction_id", "kind", "data"}
                and event["schema"] == "proposal-event-v1"
                and seq == index == event["sequence"] and event["previous"] == previous,
                "INGRESS_INTEGRITY")
        store._validate_time(event["at_utc"])
        require(event["at_utc"] >= at and event["transaction_id"] not in transactions,
                "INGRESS_INTEGRITY")
        from aegiscae.contracts.research_contracts import identifier
        identifier(event["transaction_id"], "ingresstx")
        transactions.add(event["transaction_id"])
        previous, at = digest, event["at_utc"]
        result.append((event, digest))
    return result


def append(connection, events, kind, data, at):
    store._validate_time(at)
    require(not events or at >= events[-1][0]["at_utc"], "CLOCK_REGRESSION")
    event = {"schema": "proposal-event-v1", "sequence": len(events) + 1,
             "previous": events[-1][1] if events else None, "at_utc": at,
             "transaction_id": "ingresstx_" + uuid.uuid4().hex, "kind": kind, "data": data}
    body = canonical_json(event)
    require(len(body) <= 65536, "INGRESS_LIMIT")
    connection.execute("INSERT INTO events VALUES (?,?,?)", (event["sequence"], body, digest_bytes(body)))
    _fault(kind.lower() + "_before_commit")
    connection.commit()
    _fault(kind.lower() + "_after_commit")
