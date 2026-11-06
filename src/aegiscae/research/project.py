"""One local SQLite ResearchProject. All writes require explicit write APIs.

Filesystem checks detect ordinary copies, moves and reparse points, not hostile
same-user races or administrator tampering. No AF, Solver, MCP or agent imports.
"""

import os
import re
import sqlite3
import stat
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from aegiscae.contracts.research_contracts import (
    ContractBundle, ContractError, canonical_json, digest_bytes, identifier, strict_json,
)


class ProjectError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _require(condition, code):
    if not condition:
        raise ProjectError(code)


_DATABASE = "research.sqlite3"
_MARKERS = (".git", "agent_project.json", "experiment.json", "project.json", _DATABASE)
_SCHEMA = {
    "project": "CREATE TABLE project (singleton INTEGER PRIMARY KEY CHECK(singleton=1), "
               "body BLOB NOT NULL, digest TEXT NOT NULL)",
    "parts": "CREATE TABLE parts (kind TEXT NOT NULL, contract_id TEXT NOT NULL, "
             "version INTEGER NOT NULL, digest TEXT NOT NULL, body BLOB NOT NULL, "
             "PRIMARY KEY(kind,contract_id,version))",
    "bundles": "CREATE TABLE bundles (bundle_id TEXT NOT NULL, version INTEGER NOT NULL, "
               "digest TEXT NOT NULL UNIQUE, body BLOB NOT NULL, revision INTEGER NOT NULL UNIQUE, "
               "idempotency_key TEXT NOT NULL UNIQUE, created_at_utc TEXT NOT NULL, "
               "transaction_id TEXT NOT NULL UNIQUE, metadata_digest TEXT NOT NULL, "
               "PRIMARY KEY(bundle_id,version))",
    "audit": "CREATE TABLE audit (sequence INTEGER PRIMARY KEY, body BLOB NOT NULL, "
             "digest TEXT NOT NULL)",
}
_FAILURES = {"INVALID_ROOT", "REPARSE_REJECTED", "PROJECT_IDENTITY_MISMATCH", "UNSUPPORTED_SCHEMA",
             "INTEGRITY_ERROR", "STORE_UNAVAILABLE", "MISSING_PROJECT", "STORE_BUSY"}


def _utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _validate_time(value):
    _require(type(value) is str and re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z", value) is not None, "INTEGRITY_ERROR")
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        raise ProjectError("INTEGRITY_ERROR") from None


def _freeze_metadata(project_id, bundle_digest, revision, key, created, transaction_id):
    return digest_bytes(canonical_json({"research_project_id": project_id,
        "bundle_digest": bundle_digest, "project_revision": revision, "idempotency_key": key,
        "at_utc": created, "transaction_id": transaction_id}))


def _path(explicit, *, exists=True, directory=True, scope=True):
    _require(type(explicit) in (str, Path) or isinstance(explicit, Path), "INVALID_ROOT")
    path = Path(explicit)
    _require(path.is_absolute() and len(str(path)) <= 1024 and ".." not in path.parts,
             "INVALID_ROOT")
    if os.name == "nt":
        _require(len(path.drive) == 2 and path.drive[1] == ":", "INVALID_ROOT")
    for part in path.parts[1:]:
        _require(part and not part.endswith((" ", ".")) and ":" not in part
                 and not re.fullmatch(r"(?i:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", part),
                 "INVALID_ROOT")
    for candidate in (*reversed(path.parents), path):
        try:
            info = candidate.lstat()
        except FileNotFoundError:
            _require(candidate == path and not exists, "MISSING_PROJECT")
            continue
        _require(not stat.S_ISLNK(info.st_mode)
                 and not (os.name == "nt" and info.st_file_attributes & 0x400), "REPARSE_REJECTED")
        if candidate != path:
            _require(stat.S_ISDIR(info.st_mode), "INVALID_ROOT")
            if scope:
                _require(not any((candidate / name).exists() for name in _MARKERS), "INVALID_ROOT")
    if exists:
        info = path.stat()
        _require(stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode),
                 "INVALID_ROOT")
        if not directory:
            _require(info.st_nlink == 1, "FILE_IDENTITY_UNSAFE")
    return path


def _file_id(path):
    info = path.stat()
    return [str(info.st_dev), str(info.st_ino)]


def _identity(root):
    return {"canonical_root_digest": digest_bytes(os.path.normcase(str(root.resolve())).encode()),
            "root_file_identity": _file_id(root), "database_file_identity": _file_id(root / _DATABASE)}


def _check_root(root):
    root = _path(root)
    _require(not any((root / name).exists() for name in _MARKERS[:-1]), "INVALID_ROOT")
    db = _path(root / _DATABASE, directory=False, scope=False)
    _require(0 < db.stat().st_size <= 64 * 1024 * 1024, "INTEGRITY_ERROR")
    for suffix in ("-journal", "-wal", "-shm"):
        # Conservative: no automatic recovery/migration through either open API.
        _require(not Path(str(db) + suffix).exists(), "STORE_BUSY")
    return root, db


def _fault(stage):
    """No-op seam for trusted failure/crash injection tests, not a public hook."""


@contextmanager
def _connection(root, *, write=False, creating=False):
    connection = None
    try:
        if creating:
            db = root / _DATABASE
        else:
            root, db = _check_root(root)
        mode = "rw" if write else "ro"
        connection = sqlite3.connect(db.as_uri() + "?mode=" + mode, uri=True,
                                     isolation_level=None, timeout=2)
        connection.execute("PRAGMA trusted_schema=OFF")
        connection.execute("PRAGMA busy_timeout=2000")
        if not write:
            connection.execute("PRAGMA query_only=ON")
        connection.execute("BEGIN IMMEDIATE" if write else "BEGIN")
        yield connection
        if connection.in_transaction:
            connection.rollback()
    except sqlite3.OperationalError as exc:
        code = "STORE_BUSY" if exc.sqlite_errorcode in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED) \
            else "STORE_UNAVAILABLE"
        raise ProjectError(code) from None
    except sqlite3.Error:
        raise ProjectError("INTEGRITY_ERROR") from None
    except OSError:
        raise ProjectError("STORE_UNAVAILABLE") from None
    finally:
        if connection is not None:
            connection.close()


def _decode(body, expected_digest):
    _require(type(body) is bytes and len(body) <= 65536
             and digest_bytes(body) == expected_digest, "INTEGRITY_ERROR")
    try:
        value = strict_json(body)
        _require(canonical_json(value) == body, "INTEGRITY_ERROR")
        return value
    except ContractError:
        raise ProjectError("INTEGRITY_ERROR") from None


def _read_state(connection, root, agreement_state=None):
    schema = dict(connection.execute("SELECT name,sql FROM sqlite_master "
                                     "WHERE type IN ('table','view','trigger')"))
    _require(schema == _SCHEMA, "UNSUPPORTED_SCHEMA")
    rows = connection.execute("SELECT body,digest FROM project").fetchall()
    _require(len(rows) == 1, "INTEGRITY_ERROR")
    meta = _decode(*rows[0])
    expected_keys = {"schema_version", "research_project_id", "project_revision", "created_at_utc",
                     "storage_generation", "name", "phase", "binding", "binding_status",
                     "canonical_root_digest", "root_file_identity", "database_file_identity",
                     "created_transaction_id", "revision_transaction_id", "revision_at_utc"}
    _require(type(meta) is dict and set(meta) == expected_keys
             and type(meta["schema_version"]) is int and meta["schema_version"] in (1, 2, 3),
             "UNSUPPORTED_SCHEMA")
    _require(agreement_state is None or meta["schema_version"] == 3, "RESEARCH_AGREEMENT_OPT_IN_REQUIRED")
    if meta["schema_version"] == 3:
        _require(meta["binding"] is None, "INTEGRITY_ERROR")
        from aegiscae.research.research_agreement import apply_agreement, empty_state
        agreement_state = {} if agreement_state is None else agreement_state
        agreement_state.update(empty_state())
    _require(type(meta["project_revision"]) is int, "INTEGRITY_ERROR")
    _require(all(meta[key] == value for key, value in _identity(root).items()),
             "PROJECT_IDENTITY_MISMATCH")
    try:
        identifier(meta["research_project_id"], "rp")
        identifier(meta["storage_generation"], "sg")
        _validate_name(meta["name"])
        _binding(meta["binding"])
        _require(meta["binding_status"] == ("BOUND_DECLARED" if meta["binding"] else "UNBOUND"),
                 "INTEGRITY_ERROR")
        _validate_time(meta["created_at_utc"])
        _validate_time(meta["revision_at_utc"])
        identifier(meta["created_transaction_id"], "tx")
        identifier(meta["revision_transaction_id"], "tx")
    except (ContractError, TypeError, KeyError):
        raise ProjectError("INTEGRITY_ERROR") from None
    bundles = connection.execute("SELECT bundle_id,version,digest,body,revision,idempotency_key,"
                                 "created_at_utc,transaction_id,metadata_digest "
                                 "FROM bundles ORDER BY revision LIMIT 130").fetchall()
    _require(len(bundles) <= 128, "INPUT_LIMIT")
    parts = connection.execute("SELECT kind,contract_id,version,digest,body FROM parts LIMIT 385").fetchall()
    _require(len(parts) <= 384, "INPUT_LIMIT")
    _require(meta["schema_version"] != 2 or (not bundles and not parts), "INTEGRITY_ERROR")
    expected_parts, decoded = {}, []
    for row in bundles:
        bundle_id, version, digest, body, revision, key, created, transaction_id, metadata_digest = row
        try:
            bundle = ContractBundle.from_dict(_decode(body, digest))
            identifier(transaction_id, "tx")
        except ContractError:
            raise ProjectError("INTEGRITY_ERROR") from None
        _require(bundle.bundle_id == bundle_id and bundle.version == version
                 and type(revision) is int and 2 <= revision <= 1024
                 and bundle.research_project_id == meta["research_project_id"], "INTEGRITY_ERROR")
        _validate_key(key)
        _validate_time(created)
        _require(metadata_digest == _freeze_metadata(meta["research_project_id"], digest,
                 revision, key, created, transaction_id), "INTEGRITY_ERROR")
        for kind, item, contract_id in (("goal", bundle.goal, bundle.goal.goal_id),
                                         ("model", bundle.model, bundle.model.baseline_id),
                                         ("verification", bundle.verification,
                                          bundle.verification.verification_id)):
            part_body = canonical_json(asdict(item))
            part = (digest_bytes(part_body), part_body)
            identity = (kind, contract_id, item.version)
            _require(identity not in expected_parts or expected_parts[identity] == part,
                     "INTEGRITY_ERROR")
            expected_parts[identity] = part
        decoded.append((bundle, digest, revision, key, created, transaction_id, metadata_digest))
    _require({tuple(p[:3]): tuple(p[3:]) for p in parts} == expected_parts, "INTEGRITY_ERROR")
    expected_phase = "CONTRACT_FROZEN_PENDING_APPROVAL" if bundles else "CREATED"
    if meta["schema_version"] == 2 and meta["project_revision"] > 1:
        expected_phase = "REAL_PREVIEW_FROZEN_PENDING_APPROVAL"
    _require(meta["phase"] == expected_phase, "INTEGRITY_ERROR")
    audit = connection.execute("SELECT sequence,body,digest FROM audit ORDER BY sequence LIMIT 1025").fetchall()
    _require(1 <= len(audit) <= 1024, "INPUT_LIMIT")
    previous, freeze_records, events, transactions = None, [], [], set()
    current_revision = 1
    latest_frozen_digest = None
    candidate_records = {}
    if meta["schema_version"] != 3:
        from aegiscae.research.budget_rules import empty_ledger
        ledger = empty_ledger()
    workflow_state = None
    candidate_ids, candidate_keys, candidate_outputs = set(), set(), set()
    revision_stamp = (meta["created_at_utc"], meta["created_transaction_id"])
    for sequence, body, digest in audit:
        event = _decode(body, digest)
        _require(type(event) is dict, "INTEGRITY_ERROR")
        candidate_event = event.get("kind") == "CANDIDATE_PUBLICATION_OBSERVED"
        budget_event = event.get("kind") == "BUDGET_RECORDED"
        workflow_event = event.get("kind") == "WORKFLOW_RECORDED"
        _require(sequence == len(events) + 1 and set(event) == {
            "kind", "project_revision", "bundle_digest", "code", "provenance", "at_utc",
            "previous_digest", "transaction_id", "metadata_digest"}.union(
                {"candidate"} if candidate_event else {"budget"} if budget_event
                else {"workflow"} if workflow_event else set()).union(
                {"creation_schema"} if sequence == 1 and meta["schema_version"] in (2, 3) else set())
            and event["previous_digest"] == previous, "INTEGRITY_ERROR")
        if sequence == 1 and meta["schema_version"] in (2, 3):
            _require(type(event.get("creation_schema")) is int
                     and event["creation_schema"] == meta["schema_version"], "INTEGRITY_ERROR")
        _validate_time(event["at_utc"])
        try:
            identifier(event["transaction_id"], "tx")
        except ContractError:
            raise ProjectError("INTEGRITY_ERROR") from None
        _require(event["transaction_id"] not in transactions
                 and type(event["project_revision"]) is int, "INTEGRITY_ERROR")
        transactions.add(event["transaction_id"])
        kind = event["kind"]
        _require(meta["schema_version"] != 3 or kind in {
            "CREATED", "BUNDLE_FROZEN", "WORKFLOW_RECORDED", "REOPEN_FAILURE_OBSERVED"}, "INTEGRITY_ERROR")
        _require(meta["schema_version"] != 2 or kind in {
            "CREATED", "WORKFLOW_RECORDED", "REOPEN_FAILURE_OBSERVED"}, "INTEGRITY_ERROR")
        _require(type(kind) is str and kind in {"CREATED", "BUNDLE_FROZEN", "REOPEN_FAILURE_OBSERVED",
                                               "CANDIDATE_PUBLICATION_OBSERVED", "BUDGET_RECORDED",
                                               "WORKFLOW_RECORDED"}
                 and (sequence != 1 or kind == "CREATED"), "INTEGRITY_ERROR")
        if kind == "BUNDLE_FROZEN":
            current_revision += 1
            latest_frozen_digest = event["bundle_digest"]
            revision_stamp = (event["at_utc"], event["transaction_id"])
            freeze_records.append((event["bundle_digest"], event["project_revision"],
                                   *revision_stamp, event["metadata_digest"]))
        elif candidate_event:
            parent = next((b for b in decoded if b[1] == event["bundle_digest"]
                           and b[1] == latest_frozen_digest and b[2] <= current_revision), None)
            _require(parent is not None, "INTEGRITY_ERROR")
            try:
                from aegiscae.research.mutation_rules import validate_record
                request = validate_record(event["candidate"], parent[0])
                output = (request.workspace_id, request.output_identity)
                _require(request.project_revision == current_revision
                         and event["metadata_digest"] == digest_bytes(canonical_json(event["candidate"]))
                         and request.candidate_id not in candidate_ids
                         and request.idempotency_key not in candidate_keys
                         and output not in candidate_outputs, "INTEGRITY_ERROR")
                candidate_ids.add(request.candidate_id)
                candidate_keys.add(request.idempotency_key)
                candidate_outputs.add(output)
                candidate_records[request.candidate_id] = event["candidate"]
            except ContractError:
                raise ProjectError("INTEGRITY_ERROR") from None
        elif budget_event:
            parent = next((b for b in decoded if b[1] == event["bundle_digest"]
                           and b[2] <= current_revision), None)
            _require(parent is not None, "INTEGRITY_ERROR")
            try:
                from aegiscae.research.budget_rules import apply_event
                apply_event(ledger, event["budget"], parent[0], candidate_records,
                            current_revision, latest_frozen_digest)
                _require(event["budget"]["request"]["scope"]["research_project_id"]
                         == meta["research_project_id"] and event["metadata_digest"]
                         == digest_bytes(canonical_json(event["budget"])), "INTEGRITY_ERROR")
            except ContractError:
                raise ProjectError("INTEGRITY_ERROR") from None
            current_revision += 1
            revision_stamp = (event["at_utc"], event["transaction_id"])
        elif workflow_event:
            try:
                if meta["schema_version"] == 3:
                    parent = next((b for b in decoded if b[1] == latest_frozen_digest
                                   and b[2] <= current_revision), None)
                    _require(parent is not None and event["bundle_digest"] == parent[1], "INTEGRITY_ERROR")
                    apply_agreement(agreement_state, event["workflow"], parent[0], current_revision)
                elif meta["schema_version"] == 2:
                    from aegiscae.research.rod_preview_rules import apply_preview
                    workflow_state = apply_preview(workflow_state, event["workflow"],
                        meta["research_project_id"], current_revision, event["at_utc"])
                    _require(event["bundle_digest"] == workflow_state["contract_digest"],
                             "INTEGRITY_ERROR")
                else:
                    parent = next((b for b in decoded if b[1] == event["bundle_digest"]
                                   and b[2] <= current_revision), None)
                    _require(parent is not None, "INTEGRITY_ERROR")
                    if event["workflow"].get("schema_version") == "rod-local-workflow-v2":
                        from aegiscae.research.rod_local_project import apply_local
                        workflow_state = apply_local(workflow_state, event["workflow"],
                            parent[0], current_revision, latest_frozen_digest)
                    elif event["workflow"].get("schema_version") == "rod-real-workflow-v1":
                        from aegiscae.research.rod_real_project import apply_real_workflow
                        workflow_state = apply_real_workflow(workflow_state, event["workflow"],
                            parent[0], current_revision, latest_frozen_digest)
                    else:
                        from aegiscae.research.workflow_rules import apply_workflow
                        workflow_state = apply_workflow(workflow_state, event["workflow"], parent[0],
                            candidate_records, ledger, current_revision, latest_frozen_digest)
                _require(event["metadata_digest"] == digest_bytes(canonical_json(event["workflow"])),
                         "INTEGRITY_ERROR")
            except (ContractError, TypeError, KeyError):
                raise ProjectError("INTEGRITY_ERROR") from None
            current_revision += 1
            revision_stamp = (event["at_utc"], event["transaction_id"])
        elif kind == "CREATED":
            _require(sequence == 1 and (event["at_utc"], event["transaction_id"])
                     == revision_stamp, "INTEGRITY_ERROR")
        else:
            _require(type(event["code"]) is str and event["code"] in _FAILURES
                     and event["provenance"] == "CALLER_REPORTED",
                     "INTEGRITY_ERROR")
        _require(event["project_revision"] == current_revision, "INTEGRITY_ERROR")
        if kind != "BUNDLE_FROZEN" and not candidate_event and not budget_event and not workflow_event:
            _require(event["bundle_digest"] is None and event["metadata_digest"] is None,
                     "INTEGRITY_ERROR")
        if kind != "REOPEN_FAILURE_OBSERVED":
            _require(event["code"] is None and event["provenance"] == "LOCAL_TRANSACTION",
                     "INTEGRITY_ERROR")
        events.append({"sequence": sequence, **event, "event_digest": digest})
        previous = digest
    _require(freeze_records == [(b[1], b[2], b[4], b[5], b[6]) for b in decoded]
             and current_revision == meta["project_revision"]
             and revision_stamp == (meta["revision_at_utc"], meta["revision_transaction_id"]),
             "INTEGRITY_ERROR")
    # Re-stat after reads; no claim that Python closes adversarial replacement races.
    _path(root / _DATABASE, directory=False, scope=False)
    _require(all(meta[key] == value for key, value in _identity(root).items()),
             "PROJECT_IDENTITY_MISMATCH")
    return meta, decoded, events


def _validate_name(name):
    _require(type(name) is str and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 _.-]{0,79}", name)
             is not None and not re.search(r"(?i:secret|credential|password|token|dpapi)", name),
             "INVALID_NAME")


def _validate_key(key):
    _require(type(key) is str and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", key) is not None,
             "INVALID_KEY")


def _binding(value):
    if value is None:
        return None
    _require(type(value) is dict and set(value) == {"project_id", "project_instance_id",
             "context_digest", "protocol", "capability_version"}, "INVALID_BINDING")
    identifier(value["project_id"], "p")
    identifier(value["project_instance_id"], "pi")
    _require(type(value["context_digest"]) is str and re.fullmatch(
        r"sha256:[0-9a-f]{64}", value["context_digest"]) is not None, "INVALID_BINDING")
    _require(value["protocol"] == "af-local-json-v1"
             and value["capability_version"] == "gd-af-read-v1", "INVALID_BINDING")
    return strict_json(canonical_json(value))


def _append_audit(connection, kind, revision, bundle_digest=None, code=None, *,
                  at_utc=None, transaction_id=None, metadata_digest=None, candidate=None, budget=None,
                  workflow=None, creation_schema=None):
    last = connection.execute("SELECT sequence,digest FROM audit ORDER BY sequence DESC LIMIT 1").fetchone()
    sequence, previous = (last[0] + 1, last[1]) if last else (1, None)
    _require(sequence <= 1024, "INPUT_LIMIT")
    event = {"kind": kind, "project_revision": revision, "bundle_digest": bundle_digest,
             "code": code, "provenance": "CALLER_REPORTED" if code else "LOCAL_TRANSACTION",
             "at_utc": at_utc if at_utc is not None else _utc(), "previous_digest": previous,
             "transaction_id": transaction_id or "tx_" + uuid.uuid4().hex,
             "metadata_digest": metadata_digest}
    _validate_time(event["at_utc"])
    if creation_schema is not None:
        _require(kind == "CREATED" and sequence == 1
                 and type(creation_schema) is int and creation_schema in (2, 3), "INTEGRITY_ERROR")
        event["creation_schema"] = creation_schema
    if candidate is not None:
        _require(kind == "CANDIDATE_PUBLICATION_OBSERVED", "INTEGRITY_ERROR")
        event["candidate"] = candidate
    if budget is not None:
        _require(kind == "BUDGET_RECORDED", "INTEGRITY_ERROR")
        event["budget"] = budget
    if workflow is not None:
        _require(kind == "WORKFLOW_RECORDED", "INTEGRITY_ERROR")
        event["workflow"] = workflow
    body = canonical_json(event)
    connection.execute("INSERT INTO audit VALUES (?,?,?)", (sequence, body, digest_bytes(body)))
    return {"sequence": sequence, **event, "event_digest": digest_bytes(body)}


def _commit_budget_event(connection, meta, payload):
    """One owned transaction: budget event, counter replay metadata and Project revision."""
    meta["project_revision"] += 1
    meta["revision_at_utc"] = _utc()
    meta["revision_transaction_id"] = "tx_" + uuid.uuid4().hex
    body = canonical_json(meta)
    connection.execute("UPDATE project SET body=?,digest=? WHERE singleton=1", (body, digest_bytes(body)))
    return _append_audit(connection, "BUDGET_RECORDED", meta["project_revision"],
        payload["request"]["scope"]["refs"]["bundle"], at_utc=meta["revision_at_utc"],
        transaction_id=meta["revision_transaction_id"],
        metadata_digest=digest_bytes(canonical_json(payload)), budget=payload)


def _commit_workflow_event(connection, meta, bundle_digest, payload, *, at_utc=None):
    """Versioned workflow observation and revision; no new table or schema migration."""
    meta["project_revision"] += 1
    if meta["schema_version"] == 2:
        meta["phase"] = "REAL_PREVIEW_FROZEN_PENDING_APPROVAL"
    meta["revision_at_utc"] = at_utc or _utc()
    meta["revision_transaction_id"] = "tx_" + uuid.uuid4().hex
    body = canonical_json(meta)
    connection.execute("UPDATE project SET body=?,digest=? WHERE singleton=1", (body, digest_bytes(body)))
    return _append_audit(connection, "WORKFLOW_RECORDED", meta["project_revision"], bundle_digest,
        at_utc=meta["revision_at_utc"], transaction_id=meta["revision_transaction_id"],
        metadata_digest=digest_bytes(canonical_json(payload)), workflow=payload)


def create_research_project(explicit_new_root, descriptive_name, *, declared_af_binding=None,
                            rod_preview=False, research_agreements=False):
    _require(type(rod_preview) is bool, "INVALID_SCHEMA_SELECTION")
    _require(type(research_agreements) is bool and not (research_agreements and rod_preview),
             "INVALID_SCHEMA_SELECTION")
    _require(not research_agreements or declared_af_binding is None, "INVALID_BINDING")
    _require(not rod_preview or declared_af_binding is None, "INVALID_BINDING")
    _validate_name(descriptive_name)
    declared = _binding(declared_af_binding)
    root = _path(explicit_new_root, exists=False)
    _require(not root.exists(), "ROOT_EXISTS")
    try:
        root.mkdir()  # Exclusive creation; never parents=True or exist_ok=True.
        descriptor = os.open(root / _DATABASE, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.close(descriptor)
        created, transaction_id = _utc(), "tx_" + uuid.uuid4().hex
        _validate_time(created)
        meta = {"schema_version": 3 if research_agreements else 2 if rod_preview else 1,
                "research_project_id": "rp_" + uuid.uuid4().hex,
                "project_revision": 1, "created_at_utc": created,
                "created_transaction_id": transaction_id,
                "revision_transaction_id": transaction_id, "revision_at_utc": created,
                "storage_generation": "sg_" + uuid.uuid4().hex, "name": descriptive_name,
                "phase": "CREATED", "binding": declared,
                "binding_status": "BOUND_DECLARED" if declared else "UNBOUND", **_identity(root)}
        with _connection(root, write=True, creating=True) as connection:
            for statement in _SCHEMA.values():
                connection.execute(statement)
            body = canonical_json(meta)
            connection.execute("INSERT INTO project VALUES (1,?,?)", (body, digest_bytes(body)))
            _append_audit(connection, "CREATED", 1, at_utc=created, transaction_id=transaction_id,
                          creation_schema=meta["schema_version"] if rod_preview or research_agreements else None)
            _fault("create_before_commit")
            connection.commit()
        return open_existing_readonly(root)
    except OSError:
        # A newly created incomplete root is quarantined; never repaired or reused.
        raise ProjectError("CREATE_FAILED") from None


@dataclass(frozen=True)
class ResearchProject:
    _root: Path = field(repr=False)
    research_project_id: str
    storage_generation: str
    _write_enabled: bool = field(default=False, repr=False)

    @contextmanager
    def _snapshot(self, *, write=False, agreement_state=None, freezing_bundle=False):
        _require(not write or self._write_enabled, "READ_ONLY")
        with _connection(self._root, write=write) as connection:
            meta, bundles, events = _read_state(connection, self._root, agreement_state)
            _require(not write or meta["schema_version"] != 3 or agreement_state is not None
                     or freezing_bundle, "AGREEMENT_PROJECT_WRITE_SCOPE")
            _require(meta["research_project_id"] == self.research_project_id
                     and meta["storage_generation"] == self.storage_generation,
                     "PROJECT_IDENTITY_MISMATCH")
            yield connection, meta, bundles, events

    def inspect(self):
        with self._snapshot() as (_, meta, bundles, events):
            return {key: meta[key] for key in ("schema_version", "research_project_id",
                    "storage_generation", "project_revision", "created_at_utc", "phase",
                    "canonical_root_digest", "binding_status")} | {
                "declared_af_binding": meta["binding"], "bundle_count": len(bundles),
                "latest_bundle_digest": bundles[-1][1] if bundles else None,
                "audit_count": len(events), "human_approval": "NOT_ESTABLISHED",
                "numerical_verification": "NOT_RUN", "physical_verification": "NOT_ASSESSED",
                "execution_authorized": False, "budget_enforcement": (
                    "LOCAL_SYNTHETIC_ALLOCATION_ONLY" if any(e["kind"] == "BUDGET_RECORDED" for e in events)
                    else "NOT_IMPLEMENTED"), "budget_real_execution_enforced": False}

    def read_frozen_bundle(self, bundle_digest):
        with self._snapshot() as (_, meta, bundles, _events):
            for bundle, digest, revision, _key, created, transaction_id, metadata_digest in bundles:
                if digest == bundle_digest:
                    return {"bundle": bundle, "digests": bundle.digests(), "project_revision": revision,
                            "frozen_at_utc": created, "phase": "CONTRACT_FROZEN_PENDING_APPROVAL",
                            "transaction_id": transaction_id, "metadata_digest": metadata_digest,
                            "hard_constraint_coverage": "COMPLETE_DECLARED",
                            "declarations_trust": "UNTRUSTED_DECLARATIONS",
                            "human_approval": "NOT_ESTABLISHED", "V4": "NOT_ASSESSED",
                            "execution_authorized": False}
        raise ProjectError("NOT_FOUND")

    def audit_events(self, after_sequence=0, limit=64):
        _require(type(after_sequence) is int and 0 <= after_sequence <= 1024
                 and type(limit) is int and 1 <= limit <= 64, "INVALID_PAGE")
        with self._snapshot() as (_, _meta, _bundles, events):
            return tuple(events[after_sequence:after_sequence + limit])

    def freeze_contract_bundle(self, bundle, expected_revision, idempotency_key):
        _require(self._write_enabled, "READ_ONLY")
        _require(type(expected_revision) is int and expected_revision >= 1, "INVALID_REVISION")
        _validate_key(idempotency_key)
        _require(type(bundle) is ContractBundle, "INVALID_CONTRACT")
        body = bundle.canonical_bytes()
        bundle = ContractBundle.from_dict(strict_json(body))
        digest = digest_bytes(body)
        _require(bundle.research_project_id == self.research_project_id, "PROJECT_IDENTITY_MISMATCH")
        _fault("before_begin")
        with self._snapshot(write=True, freezing_bundle=True) as (connection, meta, bundles, _events):
            _require(meta["schema_version"] in (1, 3), "CONTRACT_SCHEMA_MISMATCH")
            for previous, previous_digest, revision, key, _created, _transaction, _metadata in bundles:
                if key == idempotency_key:
                    _require(previous_digest == digest, "IDEMPOTENCY_CONFLICT")
                    return {"bundle_digest": digest, "project_revision": revision,
                            "phase": "CONTRACT_FROZEN_PENDING_APPROVAL", "replayed": True}
            _require(meta["project_revision"] == expected_revision, "REVISION_CONFLICT")
            _require(len(bundles) < 128, "INPUT_LIMIT")
            for previous, *_ in bundles:
                _require(previous.bundle_id != bundle.bundle_id or previous.version < bundle.version,
                         "VERSION_CONFLICT")
            new_revision = expected_revision + 1
            created, transaction_id = _utc(), "tx_" + uuid.uuid4().hex
            _validate_time(created)
            metadata_digest = _freeze_metadata(self.research_project_id, digest, new_revision,
                                               idempotency_key, created, transaction_id)
            connection.execute("INSERT INTO bundles VALUES (?,?,?,?,?,?,?,?,?)",
                               (bundle.bundle_id, bundle.version, digest, body, new_revision,
                                idempotency_key, created, transaction_id, metadata_digest))
            _fault("after_bundle")
            for kind, item, contract_id in (("goal", bundle.goal, bundle.goal.goal_id),
                                             ("model", bundle.model, bundle.model.baseline_id),
                                             ("verification", bundle.verification,
                                              bundle.verification.verification_id)):
                part_body = canonical_json(asdict(item))
                part_digest = digest_bytes(part_body)
                existing = connection.execute("SELECT version,digest FROM parts WHERE kind=? "
                                              "AND contract_id=? ORDER BY version DESC",
                                              (kind, contract_id)).fetchall()
                exact = next((row for row in existing if row[0] == item.version), None)
                if exact:
                    _require(exact[1] == part_digest, "CONTRACT_VERSION_CONFLICT")
                else:
                    _require(not existing or item.version > existing[0][0], "VERSION_CONFLICT")
                    connection.execute("INSERT INTO parts VALUES (?,?,?,?,?)",
                                       (kind, contract_id, item.version, part_digest, part_body))
            _fault("after_parts")
            meta["project_revision"] = new_revision
            meta["phase"] = "CONTRACT_FROZEN_PENDING_APPROVAL"
            meta["revision_transaction_id"] = transaction_id
            meta["revision_at_utc"] = created
            encoded = canonical_json(meta)
            connection.execute("UPDATE project SET body=?,digest=? WHERE singleton=1",
                               (encoded, digest_bytes(encoded)))
            _append_audit(connection, "BUNDLE_FROZEN", new_revision, digest, at_utc=created,
                          transaction_id=transaction_id, metadata_digest=metadata_digest)
            _fault("before_commit")
            connection.commit()
            _fault("after_commit")  # Lost acknowledgement: replay by key, never assume rollback.
            return {"bundle_digest": digest, "project_revision": new_revision,
                    "phase": "CONTRACT_FROZEN_PENDING_APPROVAL", "replayed": False}

    def record_reopen_failure_observation(self, error_code):
        _require(type(error_code) is str and error_code in _FAILURES, "INVALID_OBSERVATION")
        with self._snapshot(write=True) as (connection, meta, _bundles, _events):
            _append_audit(connection, "REOPEN_FAILURE_OBSERVED", meta["project_revision"], code=error_code)
            connection.commit()


def _open(explicit_root, write, agreement_state=None):
    root = _path(explicit_root)
    with _connection(root, write=write) as connection:
        meta, _, _ = _read_state(connection, root, agreement_state)
        _require(not write or meta["schema_version"] != 3 or agreement_state is not None,
                 "AGREEMENT_PROJECT_WRITE_SCOPE")
    return ResearchProject(root, meta["research_project_id"], meta["storage_generation"], write)


def open_existing_readonly(explicit_root):
    return _open(explicit_root, False)


def open_agreement_project(explicit_root, *, write=False):
    """Only admit a project originally created with the research-agreements option."""
    return _open(explicit_root, write, {})


def open_existing_for_explicit_write(explicit_root):
    return _open(explicit_root, True)


def freeze_contract_bundle(explicit_root, bundle, expected_revision, idempotency_key):
    return open_existing_for_explicit_write(explicit_root).freeze_contract_bundle(
        bundle, expected_revision, idempotency_key)


def check_pinned_artifact_identity(bundle, explicit_synthetic_files):
    """Only explicitly declared synthetic artifacts. Never parse INP/CAE or follow includes."""
    _require(type(bundle) is ContractBundle, "INVALID_CONTRACT")
    bundle.canonical_bytes()
    artifacts = bundle.model.artifacts
    _require(type(explicit_synthetic_files) is dict, "INVALID_ARTIFACT_MAPPING")
    _require(all(a.source_kind == "SYNTHETIC_TEST_ONLY" for a in artifacts), "SYNTHETIC_ONLY")
    known = {a.artifact_id for a in artifacts}
    if set(explicit_synthetic_files) - known:
        return {"status": "INCOMPLETE", "reason": "UNDECLARED_DEPENDENCY",
                "physical_verification": "NOT_ASSESSED"}
    missing = any(dep not in known for artifact in artifacts for dep in artifact.dependencies)
    for artifact in artifacts:
        if artifact.artifact_id not in explicit_synthetic_files:
            missing = True
            continue
        try:
            path = _path(explicit_synthetic_files[artifact.artifact_id], directory=False)
            _require(path.suffix.lower() == ".txt", "SYNTHETIC_TEXT_REQUIRED")
            before = path.stat()
            if before.st_size != artifact.size_bytes:
                return {"status": "STALE", "reason": "SIZE_CHANGED",
                        "physical_verification": "NOT_ASSESSED"}
            with path.open("rb") as stream:
                body = stream.read(64 * 1024 * 1024 + 1)
            after = path.stat()
            if (before.st_ino, before.st_size, before.st_mtime_ns) != (
                    after.st_ino, after.st_size, after.st_mtime_ns) or digest_bytes(body) != artifact.sha256:
                return {"status": "STALE", "reason": "BYTES_CHANGED",
                        "physical_verification": "NOT_ASSESSED"}
        except FileNotFoundError:
            missing = True
        except ProjectError as exc:
            if exc.code == "MISSING_PROJECT":
                missing = True
            else:
                raise
    return {"status": "INCOMPLETE" if missing else "BYTES_MATCH_DECLARED",
            "dependency_closure": "INCOMPLETE" if missing else bundle.model.dependency_closure,
            "semantic_status": "DECLARED_ONLY", "physical_verification": "NOT_ASSESSED"}
