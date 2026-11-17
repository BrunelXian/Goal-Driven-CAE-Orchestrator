"""TEST_ONLY operator entry for historical scoped displacement fixture bindings."""
import argparse
import hashlib
import json
import time
from pathlib import Path

from aegiscae.contracts.research_contracts import canonical_json, require
from aegiscae.interfaces import research_scope
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
    research_scope.validate_limits(record, OPERATIONS)


def authorize(binding_file, project_root, *, max_executions=3, ttl_seconds=3600, operations=None):
    return research_scope.issue(binding_file, project_root, FIXED, max_executions, ttl_seconds,
                                OPERATIONS if operations is None else operations, validate)


class Scope(research_scope.Scope):
    validate = staticmethod(validate)
    project_name = "Scoped displacement fixture"


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
