"""Operator provisioning for the single-user, stdio-only synthetic displacement case.

The trusted launcher supplies a binding file AND its independently stored digest.
No MCP tool can mint a binding, choose a root, enable a solver or change the budget.
"""
import argparse
import hashlib
import json
import re
import time
import uuid
from pathlib import Path

from aegiscae.contracts.research_contracts import canonical_json, identifier, require, strict_json
from aegiscae.research.project import _path, create_research_project, open_agreement_project
from aegiscae.research.scoped_fixture_port import BASELINE


OPERATIONS = frozenset({
    "gdcae_project_open", "gdcae_task_list", "gdcae_task_create", "gdcae_task_update",
    "gdcae_workflow_start", "gdcae_workflow_status", "gdcae_workflow_advance",
    "gdcae_diagnostics",
})
SCENARIO = "downward-displacement-fixture-v1"
FIXED = {
    "schema": "gdcae-local-scope-v1", "channel": "local-stdio", "case": SCENARIO,
    "backend_kind": "FIXTURE", "solver_budget": 0, "cpus": 1,
    "baseline_sha256": hashlib.sha256(canonical_json(BASELINE)).hexdigest(),
    "allowed_parameter": BASELINE["allowed_parameter"], "force_unit": BASELINE["force_unit"],
    "load_min": BASELINE["load_min_N"], "load_max": BASELINE["load_max_N"],
    "target_mm": "1.0", "tolerance_mm": "0.1",
    "output": "bound ResearchProject", "host_identity": "UNATTESTED",
}


def validate(record):
    fields = {"project_id", "project_root", "operations", "max_executions", "issued", "expires"}
    require(type(record) is dict and set(record) == set(FIXED) | fields, "INVALID_SCOPE")
    require(all(type(record[k]) is type(v) and record[k] == v for k, v in FIXED.items()),
            "INVALID_SCOPE")
    identifier(record["project_id"], "rp")
    ops = record["operations"]
    require(type(ops) is list and all(type(op) is str and op in OPERATIONS for op in ops)
            and len(ops) == len(set(ops)) and len(ops) > 0, "INVALID_SCOPE")
    require(type(record["max_executions"]) is int and 0 <= record["max_executions"] <= 3,
            "INVALID_SCOPE")
    issued, expires = record["issued"], record["expires"]
    require(type(issued) is int and type(expires) is int and 0 < expires - issued <= 86400,
            "INVALID_SCOPE")
    require(issued <= time.time() < expires, "SCOPE_EXPIRED")
    require(type(record["project_root"]) is str, "INVALID_ROOT")
    _path(record["project_root"], exists=False)


def authorize(binding_file, project_root, *, max_executions=3, ttl_seconds=3600, operations=None):
    """Trusted operator entry point. Requires a fresh project path and a fresh binding file."""
    root = _path(project_root, exists=False)
    path = _path(binding_file, exists=False, directory=False)
    require(not root.exists() and root != path and not path.is_relative_to(root), "ROOT_EXISTS")
    require(type(ttl_seconds) is int, "INVALID_SCOPE")
    issued = int(time.time())
    record = dict(FIXED, project_id="rp_" + uuid.uuid4().hex, project_root=str(root),
                  operations=sorted(OPERATIONS if operations is None else operations),
                  max_executions=max_executions, issued=issued, expires=issued + ttl_seconds)
    validate(record)
    raw = canonical_json(record)
    with path.open("xb") as stream:
        stream.write(raw)
    return {"project_id": record["project_id"], "binding_sha256": hashlib.sha256(raw).hexdigest()}


class Scope:
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
        validate(record)
        require(operation in record["operations"], "OPERATION_DENIED")
        require(project_id is None or project_id == record["project_id"], "PROJECT_MISMATCH")
        return record

    @staticmethod
    def project(record, *, create=False, write=False):
        root = Path(record["project_root"])
        if create and not root.exists():
            create_research_project(root, "Scoped displacement fixture", research_agreements=True,
                                    reserved_project_id=record["project_id"])
        project = open_agreement_project(root, write=write)
        require(project.research_project_id == record["project_id"], "PROJECT_MISMATCH")
        return project


def main():
    parser = argparse.ArgumentParser(description="Authorize one fresh isolated displacement fixture")
    parser.add_argument("--binding-file", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--max-executions", type=int, choices=range(4), default=3)
    parser.add_argument("--ttl-seconds", type=int, default=3600)
    args = parser.parse_args()
    print(json.dumps(authorize(args.binding_file, args.project_root, max_executions=args.max_executions,
                               ttl_seconds=args.ttl_seconds)))


if __name__ == "__main__":
    main()
