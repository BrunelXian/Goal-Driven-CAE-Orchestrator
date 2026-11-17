"""Project-scoped GD-CAE stdio server for the displacement Fixture."""
import asyncio
import json
import logging
import os
import re
import sys
from typing import Annotated, Literal

from mcp.server.lowlevel import Server
from mcp.types import CallToolResult, ListToolsResult, TextContent, Tool, ToolAnnotations
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from aegiscae.contracts.research_contracts import ContractError, require
from aegiscae.interfaces.fixture_scope import OPERATIONS, Scope
from aegiscae.interfaces.mcp_proposal import serve
from aegiscae.research import scoped_fixture
from aegiscae.research.task_cards import record_scoped, view


class Empty(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")


class Project(Empty):
    project_id: Annotated[str, Field(pattern=r"^rp_[0-9a-f]{32}$")]


class Event(Project):
    key: Annotated[str, Field(pattern=r"^[A-Za-z0-9._-]{1,96}$")]
    expected_revision: Annotated[int, Field(ge=1, le=1024)]


class Status(Project):
    request_key: Annotated[str, Field(pattern=r"^[A-Za-z0-9._-]{1,96}$")] | None = None


TaskID = Annotated[str, Field(pattern=r"^T[0-9]{2,6}$")]
Description = Annotated[str, Field(min_length=1, max_length=1024)]


class Reference(Empty):
    reference: Description
    sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class TaskCreate(Empty):
    task_id: TaskID
    kind: Literal["model-qualification", "capability-discovery", "result-extraction",
                  "independent-review", "candidate-design", "research-review"]
    goal: Description
    criterion: Description
    deps: Annotated[list[TaskID], Field(max_length=32)]
    refs: Annotated[list[Reference], Field(max_length=32)]


class TaskUpdate(Empty):
    task_id: TaskID
    execution: Literal["IN_PROGRESS", "SUBMITTED", "BLOCKED"]
    evidence: Annotated[list[Reference], Field(max_length=32)]


class Create(Event):
    data: TaskCreate


class Update(Event):
    data: TaskUpdate


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
        meta = project.inspect()
        return {"project_id": project.research_project_id, "revision": meta["project_revision"],
                "storage_generation": meta["storage_generation"], "host_attestation": "UNATTESTED"}
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
    op = {"gdcae_task_create": "task-create", "gdcae_task_update": "task-update"}[name]
    request = {"project": args.project_id, "key": args.key, "expected_revision": args.expected_revision,
               "data": args.data.model_dump()}
    return record_scoped(project, scope_id, request, op)


def error_kind(code):
    if code in {"SCOPE_EXPIRED", "SCOPE_UNAUTHORIZED", "OPERATION_DENIED", "PROJECT_MISMATCH"}:
        return "UNAUTHORIZED"
    if code == "MISSING_PROJECT":
        return "NOT_DEPLOYED"
    if code == "UNKNOWN_TOOL":
        return "NOT_IMPLEMENTED"
    if code in {"SERVICE_FAILURE", "STORE_UNAVAILABLE", "STORE_BUSY", "BINDING_CHANGED",
                "DEPLOYMENT_CHANGED", "PACKAGE_INVENTORY_MISMATCH", "BACKEND_PIN_MISMATCH",
                "INTEGRITY_ERROR", "FILE_IDENTITY_UNSAFE", "REPARSE_REJECTED"}:
        return "SERVICE_FAILURE"
    return "INPUT_OR_STATE_REJECTED"


def response(data=None, error=None):
    payload = {"error": error, "data": data}
    if error:
        payload["category"] = error_kind(error)
    return CallToolResult(structuredContent=payload, isError=error is not None,
                          content=[TextContent(type="text", text=json.dumps(payload, ensure_ascii=True,
                                                                           separators=(",", ":")))])


def create_server(scope, *, verify_deployment=None):
    require(set(TOOLS) == OPERATIONS, "SERVICE_CONFIGURATION_ERROR")

    async def list_tools(context, params):
        return ListToolsResult(tools=[Tool(name=name, description=description,
            inputSchema=model.model_json_schema(), annotations=ToolAnnotations(
                readOnlyHint=read_only, destructiveHint=False, idempotentHint=True, openWorldHint=False))
            for name, (model, read_only, description) in TOOLS.items()])

    async def call_tool(context, params):
        try:
            require(params.name in TOOLS, "UNKNOWN_TOOL")
            args = TOOLS[params.name][0].model_validate(params.arguments or {})
            if verify_deployment is not None:
                verify_deployment()
            return response(dispatch(scope, params.name, args))
        except ValidationError:
            return response(error="INVALID_ARGUMENTS")
        except (ValueError, OSError) as exc:
            code = getattr(exc, "code", None)
            if code is None and exc.args and exc.args[0] in (
                "BINDING_CHANGED", "SCOPE_EXPIRED", "DEPLOYMENT_CHANGED", "PACKAGE_INVENTORY_MISMATCH",
            ):
                code = exc.args[0]
            return response(error=code if isinstance(code, str) and re.fullmatch(r"[A-Z0-9_]{1,80}", code)
                            else "SERVICE_FAILURE")

    server = Server("gdcae-core", version="0.0.3", on_list_tools=list_tools, on_call_tool=call_tool,
                    instructions="Use the operator-bound project and the returned next action. "
                    "All numerical evidence is synthetic. Never retry an unknown submission with a new key.")
    server.middleware = []
    return server


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
