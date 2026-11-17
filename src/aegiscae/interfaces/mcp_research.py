"""Harness-neutral stdio MCP for the operator-bound research project."""
import asyncio
import json
import logging
import os
import re
import sys
from typing import Annotated, Literal

from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from mcp.types import CallToolResult, ListToolsResult, TextContent, Tool, ToolAnnotations
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from aegiscae import __version__
from aegiscae.contracts.research_contracts import ContractError, require
from aegiscae.interfaces.research_scope import OPERATIONS, Scope
from aegiscae.research.workflow import agent_start, agent_advance, agent_status
from aegiscae.research.project_tasks import record_scoped, view


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
    parameter: Description
    value: Annotated[str, Field(min_length=1, max_length=64)]
    unit: Description
    baseline_digest: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    reason: Description
    evidence_refs: Annotated[list[Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]], Field(max_length=32)]


class Propose(Event):
    proposal: Candidate


class Evidence(Project):
    candidate: Annotated[int, Field(ge=1, le=1024)]


TOOLS = {
    "gdcae_project_open": (Empty, False, "Create or reopen the operator-bound ResearchProject."),
    "gdcae_task_list": (Project, True, "Read project Task Cards, deliverables and revision."),
    "gdcae_task_create": (Create, False, "Register a scoped specialist task with dependencies."),
    "gdcae_task_update": (Update, False, "Update an auxiliary card with evidence references."),
    "gdcae_workflow_start": (Event, False, "Enter logical Research Main and freeze the bound operator contract."),
    "gdcae_workflow_advance": (Event, False, "Advance an admitted candidate, reconcile a receipt or check evidence. "
                               "At PROPOSE_CANDIDATE use gdcae_candidate_propose."),
    "gdcae_candidate_propose": (Propose, False, "Submit your own single-parameter candidate with units, "
                                "reason, baseline and references to prior observations."),
    "gdcae_evidence_read": (Evidence, True, "Read one candidate's actual recorded receipt, observation and decision."),
    "gdcae_workflow_status": (Status, True, "Recover workflow, budget, decisions and next step. "
                              "Query an uncertain write using its original request key."),
    "gdcae_diagnostics": (Project, True, "Read core deployment identity and scoped operation capabilities."),
}


def dispatch(scope, name, args):
    record = scope.read(name, args.project_id if isinstance(args, Project) else None)
    contract = record["contract"]
    if name == "gdcae_diagnostics":
        return {"project_id": record["project_id"], "service": "gdcae-core", "version": __version__,
                "channel": "local-stdio", "operations": record["operations"], "scope_sha256": scope.pin,
                "backend": contract["backend"], "max_executions": record["max_executions"],
                "solver_budget": record["solver_budget"], "real_submit": "NOT_IMPLEMENTED",
                "project_store": "PRESENT" if os.path.isdir(record["project_root"]) else "NOT_DEPLOYED"}
    project = scope.project(record, create=name == "gdcae_project_open", write=not TOOLS[name][1])
    if name == "gdcae_project_open":
        return project_view(project)
    if name == "gdcae_task_list":
        return view(project)
    if name in {"gdcae_task_create", "gdcae_task_update"}:
        return task_write(project, scope.pin, name, args)
    limit = record["max_executions"]
    if name == "gdcae_workflow_status":
        return agent_status(project, scope.pin, limit, request_key=args.request_key, contract=contract)
    if name == "gdcae_evidence_read":
        state = agent_status(project, scope.pin, limit, contract=contract)
        require(args.candidate <= len(state["candidates"]), "CANDIDATE_NOT_FOUND")
        candidate = state["candidates"][args.candidate - 1]
        require("receipt" in candidate, "EVIDENCE_NOT_AVAILABLE")
        return {"project_id": args.project_id, "revision": state["revision"],
                "candidate_index": args.candidate, "candidate": candidate,
                "goal": contract["goal"], "backend": contract["backend"]}
    if name == "gdcae_workflow_start":
        return agent_start(project, scope.pin, limit, args.expected_revision, args.key, contract=contract)
    proposal = args.proposal.model_dump() if name == "gdcae_candidate_propose" else None
    return agent_advance(project, scope.pin, limit, args.expected_revision, args.key,
                         proposal=proposal, contract=contract)


def project_view(project):
    meta = project.inspect()
    return {"project_id": project.research_project_id, "revision": meta["project_revision"],
            "storage_generation": meta["storage_generation"], "host_attestation": "UNATTESTED"}


def task_write(project, pin, name, args):
    op = {"gdcae_task_create": "task-create", "gdcae_task_update": "task-update"}[name]
    request = {"project": args.project_id, "key": args.key, "expected_revision": args.expected_revision,
               "data": args.data.model_dump()}
    return record_scoped(project, pin, request, op)


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


def stdio_tools(scope, schemas, operations, handler, version, instructions, verify_deployment):
    require(set(schemas) == operations, "SERVICE_CONFIGURATION_ERROR")

    async def list_tools(context, params):
        return ListToolsResult(tools=[Tool(name=name, description=description,
            inputSchema=model.model_json_schema(), annotations=ToolAnnotations(
                readOnlyHint=read_only, destructiveHint=False, idempotentHint=True, openWorldHint=False))
            for name, (model, read_only, description) in schemas.items()])

    async def call_tool(context, params):
        try:
            require(params.name in schemas, "UNKNOWN_TOOL")
            args = schemas[params.name][0].model_validate(params.arguments or {})
            if verify_deployment is not None:
                verify_deployment()
            return response(handler(scope, params.name, args))
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

    server = Server("gdcae-core", version=version, on_list_tools=list_tools, on_call_tool=call_tool,
                    instructions=instructions)
    server.middleware = []
    return server


def create_server(scope, *, verify_deployment=None):
    return stdio_tools(scope, TOOLS, OPERATIONS, dispatch, __version__,
                       "Inspect the frozen contract and actual observations. Submit your own proposals. "
                       "If acceptance is unknown, query the original request key.",
                       verify_deployment)


async def serve(server):
    async with stdio_server() as (reader, writer):
        await server.run(reader, writer, server.create_initialization_options())


def main():
    logging.disable(logging.CRITICAL)
    try:
        require(len(sys.argv) == 3 and sys.argv[1] == "--binding-file", "EXPLICIT_BINDING_REQUIRED")
        scope = Scope(sys.argv[2], os.environ.get("GDCAE_BINDING_SHA256"))
        asyncio.run(serve(create_server(scope)))
        return 0
    except (ContractError, OSError):
        print("GDCAE_RESEARCH_SERVICE_UNAVAILABLE", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
