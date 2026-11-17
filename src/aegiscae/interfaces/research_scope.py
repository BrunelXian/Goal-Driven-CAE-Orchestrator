"""Trusted local binding for the research MCP. The operator supplies contract and scope out of band."""
import argparse
import hashlib
import json
import re
import time
import uuid
from pathlib import Path

from aegiscae.contracts.research_contracts import canonical_json, identifier, require, strict_json
from aegiscae.research.project import _path, create_research_project, open_agreement_project
from aegiscae.research.workflow import validate_agent_contract


OPERATIONS = frozenset({
    "gdcae_project_open", "gdcae_task_list", "gdcae_task_create", "gdcae_task_update",
    "gdcae_workflow_start", "gdcae_workflow_status", "gdcae_workflow_advance",
    "gdcae_diagnostics", "gdcae_candidate_propose", "gdcae_evidence_read",
})

BINDING_FIELDS = {"project_id", "project_root", "operations", "max_executions", "issued", "expires"}
FIXED = {"schema": "research-scope-v1", "channel": "local-stdio", "solver_budget": 0, "cpus": 1}


def validate_limits(record, operations):
    identifier(record["project_id"], "rp")
    ops = record["operations"]
    require(type(ops) is list and all(type(op) is str and op in operations for op in ops)
            and len(ops) == len(set(ops)) and len(ops) > 0, "INVALID_SCOPE")
    require(type(record["max_executions"]) is int and 0 <= record["max_executions"] <= 3,
            "INVALID_SCOPE")
    issued, expires = record["issued"], record["expires"]
    require(type(issued) is int and type(expires) is int and 0 < expires - issued <= 86400,
            "INVALID_SCOPE")
    require(issued <= time.time() < expires, "SCOPE_EXPIRED")
    require(type(record["project_root"]) is str, "INVALID_ROOT")
    _path(record["project_root"], exists=False)


def validate(record):
    require(type(record) is dict and set(record) == set(FIXED) | BINDING_FIELDS | {"contract"},
            "INVALID_SCOPE")
    require(all(type(record[k]) is type(v) and record[k] == v for k, v in FIXED.items()),
            "INVALID_SCOPE")
    validate_limits(record, OPERATIONS)
    validate_agent_contract(record["contract"])


def issue(binding_file, project_root, fields, max_executions, ttl_seconds, operations, validate):
    root = _path(project_root, exists=False)
    path = _path(binding_file, exists=False, directory=False)
    require(not root.exists() and root != path and not path.is_relative_to(root), "ROOT_EXISTS")
    require(type(ttl_seconds) is int, "INVALID_SCOPE")
    issued = int(time.time())
    record = dict(fields, project_id="rp_" + uuid.uuid4().hex, project_root=str(root),
                  operations=sorted(operations),
                  max_executions=max_executions, issued=issued, expires=issued + ttl_seconds)
    validate(record)
    raw = canonical_json(record)
    with path.open("xb") as stream:
        stream.write(raw)
    return {"project_id": record["project_id"], "binding_sha256": hashlib.sha256(raw).hexdigest()}


def authorize(binding_file, project_root, *, contract, max_executions=3, ttl_seconds=3600, operations=None):
    return issue(binding_file, project_root, dict(FIXED, contract=contract), max_executions, ttl_seconds,
                 OPERATIONS if operations is None else operations, validate)


class Scope:
    validate = staticmethod(validate)
    project_name = "Bound research project"

    def __init__(self, binding_file, pin):
        require(type(pin) is str and re.fullmatch("[0-9a-f]{64}", pin), "SCOPE_UNAUTHORIZED")
        self.path = Path(binding_file)
        self.pin = pin

    def read(self, operation, project_id=None):
        path = _path(self.path, directory=False)
        require(path.stat().st_size <= 8192, "INVALID_SCOPE")
        raw = path.read_bytes()
        require(hashlib.sha256(raw).hexdigest() == self.pin, "BINDING_CHANGED")
        record = strict_json(raw)
        self.validate(record)
        require(operation in record["operations"], "OPERATION_DENIED")
        require(project_id is None or project_id == record["project_id"], "PROJECT_MISMATCH")
        return record

    @classmethod
    def project(cls, record, *, create=False, write=False):
        root = Path(record["project_root"])
        if create and not root.exists():
            create_research_project(root, cls.project_name, research_agreements=True,
                                    reserved_project_id=record["project_id"])
        project = open_agreement_project(root, write=write)
        require(project.research_project_id == record["project_id"], "PROJECT_MISMATCH")
        return project


def main():
    parser = argparse.ArgumentParser(description="Bind one local project to a reviewed research contract")
    parser.add_argument("--binding-file", required=True, type=Path)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--contract-file", required=True, type=Path)
    parser.add_argument("--max-executions", type=int, choices=range(4), required=True)
    parser.add_argument("--ttl-seconds", type=int, default=3600)
    args = parser.parse_args()
    path = _path(args.contract_file, directory=False, scope=False)
    require(path.stat().st_size <= 8192, "INPUT_LIMIT")
    print(json.dumps(authorize(args.binding_file, args.project_root, contract=strict_json(path.read_bytes()),
                               max_executions=args.max_executions, ttl_seconds=args.ttl_seconds)))


if __name__ == "__main__":
    main()
