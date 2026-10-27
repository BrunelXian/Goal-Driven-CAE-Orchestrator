"""Bounded recorded AF evidence via one lazy, explicit, attach-only seam.

The injected discovery callable is trusted test infrastructure, not a plugin API.
The facade is not an OS sandbox or a read-only AF credential.
"""

import json
import re
import time
from pathlib import PureWindowsPath

from aegiscae.contracts.af_evidence import (
    ProjectBinding,
    ReadCursor,
    ReadEnvelope,
    ReadError,
    SourceIdentity,
)

_READS = {
    "capabilities": "health", "list_runs": "project_view", "get_run": "run",
    "get_receipt": "receipt", "list_events": "events",
    "get_validations": "validations", "get_diagnostic": "diagnose",
}
_CODES = frozenset({
    "LEGACY_PROJECT", "NOT_AN_AGENT_FIRST_PROJECT", "PROJECT_INCOMPLETE",
    "UNSUPPORTED_FORMAT", "PROJECT_IDENTITY_MISMATCH", "DISCOVERY_LAYOUT_UNSUPPORTED",
    "DISCOVERY_UNAVAILABLE", "LOCAL_CREDENTIAL_UNAVAILABLE", "AUTHENTICATION_FAILED",
    "PROTOCOL_MISMATCH", "ENDPOINT_IDENTITY_MISMATCH", "OWNER_NOT_RUNNING",
    "PROCESS_IDENTITY_UNKNOWN", "PROCESS_IDENTITY_MISMATCH", "CAPABILITY_UNAVAILABLE",
    "COMMUNICATION_UNKNOWN", "NOT_FOUND", "LIMIT_EXCEEDED", "MESSAGE_TOO_LARGE",
    "STORE_UNAVAILABLE", "STORE_REQUIRES_MAINTENANCE", "INVALID_REQUEST",
    "MALFORMED_RESPONSE", "INVALID_BINDING", "INVALID_CURSOR",
})
_STAGES = frozenset({"DISCOVERY", "TRANSPORT", "QUERY", "VALIDATE", "PROTOCOL"})
_STATUS = {
    "queue_state": {"PENDING", "DISPATCHED", "BLOCKED"},
    "execution": {"PLANNED", "RUNNING", "FINISHED", "UNKNOWN", "START_INTENT",
                  "BLOCKED", "VALIDATING"},
    "solver_conclusion": {"NOT_RUN", "EVIDENCE_INSUFFICIENT", "COMPLETED_TEXT_EVIDENCE",
                          "FAILED_TEXT_EVIDENCE"},
    "artifact_validation": {"NOT_RUN", "UNKNOWN", "VALID", "INVALID"},
    "reconciliation": {"NONE", "REQUIRED", "RECONCILIATION_REQUIRED"},
}
_EVENTS = frozenset({
    "REQUEST_ACCEPTED", "START_INTENT", "DISPATCH_BLOCKED", "FAKE_COMPLETED",
    "VALIDATION_RECORDED", "RECONCILIATION_REQUIRED", "RECONCILIATION_APPLIED",
    "PROCESS_IDENTITIES", "PROCESS_EXIT_OBSERVED", "PROCESS_COMPLETED",
    "PROCESS_RECONCILIATION_APPLIED", "MANAGED_SCOPE_PREPARED", "MANAGED_ROOT_CREATED",
    "MANAGED_SCOPE_OBSERVED", "MANAGED_SCOPE_COMPLETED", "STANDARD_STARTING",
    "STANDARD_LAUNCH_INTENT", "STANDARD_CREATE_ENTERING", "STANDARD_CREATED",
    "STANDARD_PROCESS_OBSERVATION", "STANDARD_OBSERVATION_ENDED",
    "STANDARD_RESULT_RECORDED", "STANDARD_DISPOSITION_RECORDED",
    "STANDARD_MANAGED_COMPLETED",
})


def _discover(explicit_project_root):
    from abqjobpilot.service_discovery import discover
    return discover(explicit_project_root)


class _Failure(Exception):
    def __init__(self, code):
        self.code = code


def _require(condition, code="MALFORMED_RESPONSE"):
    if not condition:
        raise _Failure(code)


def _integer(value):
    return type(value) is int and 0 <= value < 2**63


def _identifier(value, prefix):
    return type(value) is str and re.fullmatch(prefix + r"_[0-9a-f]{32}", value) is not None


def _digest(value):
    return type(value) is str and re.fullmatch(r"sha256:[0-9a-f]{64}", value) is not None


def _bounded(value):
    """Reject non-JSON, cyclic, deep or oversized inputs before projecting fields."""
    nodes, characters = 0, 0

    def visit(item, depth):
        nonlocal nodes, characters
        nodes += 1
        _require(depth <= 12 and nodes <= 8192, "LIMIT_EXCEEDED")
        if type(item) is dict:
            _require(len(item) <= 8192, "LIMIT_EXCEEDED")
            for key, child in item.items():
                _require(type(key) is str)
                characters += len(key)
                _require(characters <= 262144, "LIMIT_EXCEEDED")
                visit(child, depth + 1)
        elif type(item) is list:
            _require(len(item) <= 8192, "LIMIT_EXCEEDED")
            for child in item:
                visit(child, depth + 1)
        elif type(item) is str:
            characters += len(item)
            _require(characters <= 262144, "LIMIT_EXCEEDED")
        else:
            _require(item is None or type(item) is bool or _integer(item))

    visit(value, 0)
    _require(len(json.dumps(value, ensure_ascii=True).encode("utf-8")) <= 262144,
             "LIMIT_EXCEEDED")
    return value


def _mapping(value):
    _require(type(value) is dict)
    return value


def _identity(binding):
    _require(type(binding) is ProjectBinding, "INVALID_BINDING")
    _require(type(binding.root) is str and 0 < len(binding.root) <= 1024,
             "INVALID_BINDING")
    root = PureWindowsPath(binding.root)
    _require(root.is_absolute() and len(root.drive) == 2
             and ".." not in root.parts and "\x00" not in binding.root,
             "INVALID_BINDING")
    _require(_identifier(binding.project_id, "p")
             and _identifier(binding.project_instance_id, "pi")
             and _digest(binding.context_digest) and _identifier(binding.owner_id, "owner"),
             "INVALID_BINDING")
    return SourceIdentity(binding.project_id, binding.project_instance_id,
                          binding.context_digest, binding.owner_id)


def _scope(value, source, *, required=False):
    for name in ("project_id", "project_instance_id", "context_digest"):
        if required or name in value:
            _require(value.get(name) == vars(source)[name], "PROJECT_IDENTITY_MISMATCH")


def _run(value, source, run_id=None):
    value = _mapping(value)
    _scope(value, source)
    _require(_identifier(value.get("run_id"), "r"))
    if run_id is not None:
        _require(value["run_id"] == run_id, "PROJECT_IDENTITY_MISMATCH")
    result = {"run_id": value["run_id"]}
    complete = True
    for name, options in _STATUS.items():
        item = value.get(name)
        result[name] = item if type(item) is str and item in options else None
        complete &= result[name] is not None
    for name in ("revision", "created_at"):
        item = value.get(name)
        result[name] = item if _integer(item) else None
        complete &= result[name] is not None
    backend = value.get("backend_id")
    result["backend_id"] = backend if backend in (
        "fake-v1", "python-process-fixture-v1", "abaqus-standard-axial-2024-v1") else None
    plan = value.get("plan_id")
    result["plan_id"] = plan if _identifier(plan, "plan") else None
    complete &= result["backend_id"] is not None and result["plan_id"] is not None
    optional = {
        "simulation": type(value.get("simulation")) is bool,
        "validation_scope": value.get("validation_scope") in (
            "simulation", "fixed_standard_dat_only"),
        "plan_digest": _digest(value.get("plan_digest")),
    }
    for name, valid in optional.items():
        result[name] = value.get(name) if valid else None
        if name in value and value[name] is not None and not valid:
            complete = False
    return result, complete


def _validations(value, run_id):
    _require(type(value) is list)
    _require(len(value) <= 64, "LIMIT_EXCEEDED")
    result, complete = [], True
    for item in value:
        item = _mapping(item)
        _require(item.get("run_id") == run_id, "PROJECT_IDENTITY_MISMATCH")
        _require(_identifier(item.get("validation_id"), "val"))
        verdict = item.get("verdict")
        verdict = verdict if type(verdict) is str and verdict in {"PASS", "FAIL", "UNKNOWN"} else None
        recorded = item.get("recorded_at")
        recorded = recorded if _integer(recorded) else None
        scope = item.get("scope")
        scope = scope if scope in ("simulation", "fixed_standard_dat_only") else None
        complete &= verdict is not None and recorded is not None and scope is not None
        record = {"validation_id": item["validation_id"], "run_id": run_id,
                  "recorded_verdict": verdict, "recorded_at": recorded, "scope": scope}
        enums = {
            "policy_id": ("fake-result-v1", "process-fixture-result-v1", "fixed-2024-axial-dat-v1"),
            "validator_id": ("fake-json-validator", "process-fixture-validator",
                             "standard-dat-validator"),
        }
        for name, choices in enums.items():
            record[name] = item.get(name) if item.get(name) in choices else None
            complete &= record[name] is not None
        for name in ("policy_version", "validator_version"):
            record[name] = item.get(name) if _integer(item.get(name)) else None
            complete &= record[name] is not None
        result.append(record)
    return tuple(result), complete


class EvidenceBridge:
    """Seven explicit reads; constructing/importing this class performs no discovery."""

    def __init__(self, discovery=None):
        self._discovery = discovery if discovery is not None else _discover

    def _read(self, binding, operation, reader):
        source, stage = None, "VALIDATE"
        try:
            expected = _identity(binding)
            stage = "DISCOVERY"
            client, context, health = self._discovery(binding.root)
            endpoint = _mapping(client.endpoint)
            _require(endpoint.get("protocol") == "af-local-json-v1", "PROTOCOL_MISMATCH")
            _require(context.project_id == expected.project_id
                     and context.project_instance_id == expected.project_instance_id
                     and context.context_digest == expected.context_digest,
                     "PROJECT_IDENTITY_MISMATCH")
            _scope(endpoint, expected, required=True)
            _require(endpoint.get("owner_id") == expected.owner_id, "ENDPOINT_IDENTITY_MISMATCH")
            health = _mapping(_bounded(health))
            operations = health.get("operations")
            _require(type(operations) is list)
            _require(_READS[operation] in operations, "CAPABILITY_UNAVAILABLE")
            source, stage = expected, "QUERY"
            data, complete, source_time, cursor, more = reader(client, health, source)
            return ReadEnvelope(operation, source, time.time_ns() // 1_000_000,
                                "COMPLETE" if complete else "INCOMPLETE",
                                "recorded_read; successive_calls_not_atomic", data,
                                source_time, cursor, more)
        except Exception as exc:
            metadata = vars(exc)
            code = metadata.get("code")
            if not (type(code) is str and code in _CODES):
                code = ("MALFORMED_RESPONSE" if stage == "QUERY"
                        and isinstance(exc, (ValueError, TypeError, KeyError))
                        else "UPSTREAM_UNAVAILABLE")
            upstream_stage = metadata.get("stage")
            if type(upstream_stage) is str and upstream_stage in _STAGES:
                stage = upstream_stage
            return ReadEnvelope(operation, source, time.time_ns() // 1_000_000,
                                "UNAVAILABLE", "no_successful_read",
                                error=ReadError(code, stage))

    def capabilities(self, binding):
        def project(client, health, source):
            reads = tuple(name for name, rpc in _READS.items() if rpc in health["operations"])
            simulation = health.get("simulation")
            simulation = simulation if type(simulation) is bool else None
            return ({"read_operations": reads, "simulation": simulation,
                     "execution_authorized": False}, simulation is not None, None, None, None)
        return self._read(binding, "capabilities", project)

    def _cursor(self, cursor, source, operation):
        if cursor is None:
            return 0
        _require(type(cursor) is ReadCursor and cursor.source == source
                 and cursor.operation == operation and _integer(cursor.position)
                 and cursor.position > 0, "INVALID_CURSOR")
        return cursor.position

    def list_runs(self, binding, cursor=None, limit=32):
        def project(client, health, source):
            _require(type(limit) is int and 1 <= limit <= 32, "INVALID_REQUEST")
            before = self._cursor(cursor, source, "list_runs")
            raw = _mapping(_bounded(client.project_view(before_row=before, limit=limit)))
            _scope(raw, source, required=True)
            _require(raw.get("view_version") == "af-project-view-v1")
            rows = raw.get("runs")
            _require(type(rows) is list and len(rows) <= limit)
            _require(_integer(raw.get("read_at")))
            _require("next_before_row" in raw)
            position = raw["next_before_row"]
            _require(position is None or (_integer(position) and position > 0
                     and (before == 0 or position < before) and len(rows) > 0))
            values = [_run(item, source) for item in rows]
            _require(len({item[0]["run_id"] for item in values}) == len(values))
            next_cursor = ReadCursor(source, "list_runs", position) if position else None
            return (tuple(item[0] for item in values), all(item[1] for item in values),
                    raw["read_at"], next_cursor, position is not None)
        return self._read(binding, "list_runs", project)

    def get_run(self, binding, run_id):
        def project(client, health, source):
            _require(_identifier(run_id, "r"), "INVALID_REQUEST")
            raw = _mapping(_bounded(client.run(run_id)))
            _require(raw.get("project_id") == source.project_id
                     and raw.get("project_instance_id") == source.project_instance_id,
                     "PROJECT_IDENTITY_MISMATCH")
            value, complete = _run(raw, source, run_id)
            return value, complete, None, None, None
        return self._read(binding, "get_run", project)

    def get_receipt(self, binding, key):
        def project(client, health, source):
            _require(type(key) is str and 0 < len(key) <= 256, "INVALID_REQUEST")
            raw = _mapping(_bounded(client.receipt(key)))
            _require(raw.get("idempotency_key") == key, "PROJECT_IDENTITY_MISMATCH")
            namespace = raw.get("namespace")
            _require(type(namespace) is str)
            namespace = json.loads(namespace)
            _require(type(namespace) is list and len(namespace) == 3
                     and namespace[0] == source.project_instance_id
                     and type(namespace[1]) is str and namespace[2] == "submit",
                     "PROJECT_IDENTITY_MISMATCH")
            _require(_identifier(raw.get("request_id"), "req")
                     and _identifier(raw.get("run_id"), "r"))
            _require(raw.get("request_status") == "ACCEPTED" and _integer(raw.get("accepted_at")))
            return ({"request_id": raw["request_id"], "run_id": raw["run_id"],
                     "request_status": raw["request_status"], "accepted_at": raw["accepted_at"]},
                    True, None, None, None)
        return self._read(binding, "get_receipt", project)

    def list_events(self, binding, cursor=None, limit=64, run_id=None):
        def project(client, health, source):
            _require(type(limit) is int and 1 <= limit <= 64, "INVALID_REQUEST")
            _require(run_id is None or _identifier(run_id, "r"), "INVALID_REQUEST")
            after = self._cursor(cursor, source, "list_events")
            raw = _bounded(client.events(after_sequence=after, limit=limit))
            _require(type(raw) is list and len(raw) <= limit)
            result, complete, position = [], True, after
            for item in raw:
                item = _mapping(item)
                _scope(item, source)
                sequence = item.get("project_sequence")
                _require(_integer(sequence) and sequence > position)
                position = sequence
                kind = item.get("type")
                if type(kind) is not str or kind not in _EVENTS:
                    complete = False
                    continue
                _require(_identifier(item.get("event_id"), "ev")
                         and _identifier(item.get("run_id"), "r"))
                if run_id is not None and item["run_id"] != run_id:
                    continue
                recorded = item.get("recorded_at")
                recorded = recorded if _integer(recorded) else None
                complete &= recorded is not None
                result.append({"event_id": item["event_id"], "run_id": item["run_id"],
                               "project_sequence": sequence, "type": kind,
                               "recorded_at": recorded})
            next_cursor = ReadCursor(source, "list_events", position) if position else None
            return tuple(result), complete, None, next_cursor, len(raw) == limit
        return self._read(binding, "list_events", project)

    def get_validations(self, binding, run_id):
        def project(client, health, source):
            _require(_identifier(run_id, "r"), "INVALID_REQUEST")
            result, complete = _validations(_bounded(client.validations(run_id)), run_id)
            return result, complete, None, None, None
        return self._read(binding, "get_validations", project)

    def get_diagnostic(self, binding, run_id):
        def project(client, health, source):
            _require(_identifier(run_id, "r"), "INVALID_REQUEST")
            raw = _mapping(_bounded(client.diagnose(run_id)))
            body = _mapping(raw.get("body"))
            identity = _mapping(body.get("identity"))
            _scope(identity, source, required=True)
            _require(identity.get("run_id") == run_id, "PROJECT_IDENTITY_MISMATCH")
            _require(body.get("report_version") in
                     ("af-run-diagnostic-v1", "af-run-diagnostic-v2", "af-run-diagnostic-v3"))
            view = _mapping(body.get("view"))
            _require(_integer(view.get("read_at")))
            facts = _mapping(body.get("facts"))
            run, complete = _run(facts.get("run"), source, run_id)
            validations, valid_complete = _validations(facts.get("validations"), run_id)
            digest = raw.get("content_digest")
            digest = digest if _digest(digest) else None
            complete &= valid_complete and digest is not None
            complete &= view.get("all_run_records_within_limits") is True
            return ({"run": run, "validations": validations,
                     "source_recorded_digest": digest, "digest_verified": False,
                     "artifacts_revalidated": False, "current_os_liveness_verified": False},
                    complete, view["read_at"], None, None)
        return self._read(binding, "get_diagnostic", project)
