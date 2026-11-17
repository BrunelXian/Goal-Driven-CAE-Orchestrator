"""TEST_ONLY v1 stdio interface for historical displacement fixture replay."""
import asyncio
import logging
import os
import sys
from typing import Annotated, Literal

from pydantic import Field

from aegiscae.contracts.research_contracts import ContractError, require
from aegiscae.interfaces.fixture_scope import OPERATIONS, Scope
from aegiscae.interfaces.mcp_research import (
    Empty, Project, Event, Status, Create, Update, project_view, task_write, stdio_tools, serve,
)
from aegiscae.research import scoped_fixture
from aegiscae.research.task_cards import view


class Candidate(Empty):
    force_N: Annotated[int, Field(ge=1, le=200)]
    unit: Literal["N"]
    baseline_digest: Annotated[str, Field(min_length=64, max_length=71)]


class Advance(Event):
    proposal: Candidate | None = None


TOOLS = {
    "gdcae_project_open": (Empty, False, "Create or reopen the operator-bound ResearchProject."),
    "gdcae_task_list": (Project, True, "Read project Task Cards, deliverables and revision."),
    "gdcae_task_create": (Create, False, "Register a scoped specialist task with dependencies."),
    "gdcae_task_update": (Update, False, "Update an auxiliary card with evidence references."),
    "gdcae_workflow_start": (Event, False, "Enter logical Main and freeze the scoped fixture case."),
    "gdcae_workflow_advance": (Advance, False, "Advance one legal fixture step. At PROPOSE_CANDIDATE, "
                               "optionally supply a bounded load against the frozen baseline."),
    "gdcae_workflow_status": (Status, True, "Recover workflow, budget, decisions and next step. "
                              "Query an uncertain write using its original request key."),
    "gdcae_diagnostics": (Project, True, "Read core deployment identity and scoped operation capabilities."),
}


def dispatch(scope, name, args):
    record = scope.read(name, args.project_id if isinstance(args, Project) else None)
    if name == "gdcae_diagnostics":
        return {
            "project_id": record["project_id"], "backend_kind": "FIXTURE",
            "service": "gdcae-core", "version": "0.0.3", "channel": "local-stdio",
            "scope_sha256": scope.pin, "operations": record["operations"],
            "host_attestation": "UNATTESTED", "real_solver_executed": False,
            "solver_budget": record["solver_budget"], "max_executions": record["max_executions"],
            "real_submit": "NOT_IMPLEMENTED", "classic_status": "QUERY_SEPARATE_SERVICE",
            "project_store": "PRESENT" if os.path.isdir(record["project_root"]) else "NOT_DEPLOYED",
        }
    project = scope.project(record, create=name == "gdcae_project_open", write=not TOOLS[name][1])
    if name == "gdcae_project_open":
        return project_view(project)
    if name == "gdcae_task_list":
        return view(project)
    return workflow_operation(name, project, scope.pin, record["max_executions"], args)


def workflow_operation(name, project, scope_id, max_runs, args):
    if name == "gdcae_workflow_status":
        return scoped_fixture.status(project, scope_id, max_runs, request_key=args.request_key)
    if name == "gdcae_workflow_start":
        return scoped_fixture.start(project, scope_id, max_runs, args.expected_revision, args.key)
    if name == "gdcae_workflow_advance":
        proposal = args.proposal.model_dump() if args.proposal is not None else None
        return scoped_fixture.advance(project, scope_id, max_runs, args.expected_revision, args.key,
                                      proposal=proposal)
    return task_write(project, scope_id, name, args)


def create_server(scope, *, verify_deployment=None):
    return stdio_tools(scope, TOOLS, OPERATIONS, dispatch, "0.0.3",
                       "Historical TEST_ONLY displacement fixture. Use the returned next action.",
                       verify_deployment)


def main():
    logging.disable(logging.CRITICAL)
    try:
        require(len(sys.argv) == 3 and sys.argv[1] == "--binding-file", "EXPLICIT_BINDING_REQUIRED")
        scope = Scope(sys.argv[2], os.environ.get("GDCAE_FIXTURE_BINDING_SHA256"))
        asyncio.run(serve(create_server(scope)))
        return 0
    except (ContractError, OSError):
        print("GDCAE_SCOPED_SERVICE_UNAVAILABLE", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
