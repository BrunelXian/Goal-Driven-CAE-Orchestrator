"""Project-scoped AgentHub task events in the v3 ResearchProject transaction log."""
import json
import os
import re
from pathlib import Path

from aegiscae.contracts.research_contracts import canonical_json, digest_bytes, require
from aegiscae.research.project import _commit_workflow_event
from aegiscae.research.task_roles import match

SCHEMA = "research-task-v1"
STARTERS = (
    ("T01", "model-qualification"),
    ("T02", "capability-discovery"),
)
TRANSITIONS = {"OPEN": {"IN_PROGRESS", "BLOCKED"}, "IN_PROGRESS": {"BLOCKED", "SUBMITTED"},
               "BLOCKED": {"IN_PROGRESS"}, "SUBMITTED": {"IN_PROGRESS"}}


def digest(value):
    return digest_bytes(canonical_json(value)).removeprefix("sha256:")


def token(value, pattern):
    return isinstance(value, str) and re.fullmatch(pattern, value) is not None


def description(value):
    return isinstance(value, str) and 0 < len(value.strip()) <= 1024 and "\x00" not in value


def main_identity(host, desktop):
    for item in (host, desktop):
        require(token(item, r"[a-zA-Z0-9._:-]{1,160}"), "INVALID_HOST_PROJECT")
    key = digest_bytes(("gdcae-main-handoff-v1\n" + host + "\n" + desktop).encode()).removeprefix("sha256:")
    thread = os.environ.get("CODEX_THREAD_ID")
    require(token(thread, r"[a-zA-Z0-9._:-]{1,160}"), "MAIN_THREAD_UNAVAILABLE")
    base = os.environ.get("LOCALAPPDATA")
    require(base and Path(base).is_absolute(), "MAIN_RECEIPT_UNAVAILABLE")
    path = Path(base) / "GDCAE/project-main-handoffs/v1" / (key + ".json")
    require(path.is_file() and path.stat().st_size <= 8192 and
            not any(p.is_symlink() or p.is_junction() for p in (path, *path.parents)), "MAIN_RECEIPT_UNAVAILABLE")
    receipt = json.loads(path.read_bytes())
    require(receipt.get("schema") == "gdcae-main-handoff-v1" and receipt.get("state") == "VERIFIED"
            and receipt.get("request_id") == key and receipt.get("host_id") == host
            and receipt.get("project_id") == desktop and receipt.get("thread_id") == thread,
            "MAIN_IDENTITY_MISMATCH")
    return digest([key, thread])


def empty():
    return {"main": None, "summary": None, "cards": {}, "receipts": {}}


def references(refs):
    require(isinstance(refs, list) and len(refs) <= 32, "INVALID_TASK_REFS")
    for ref in refs:
        require(isinstance(ref, dict) and set(ref) == {"reference", "sha256"}
                and description(ref["reference"]) and token(ref["sha256"], "[0-9a-f]{64}"), "INVALID_TASK_REFS")


def create_card(hub, project, task_id, kind, goal, criterion, deps, refs, bundle, deliverable=None):
    require(token(task_id, r"T[0-9]{2,6}") and task_id not in hub["cards"], "TASK_ID_CONFLICT")
    require(description(goal) and description(criterion), "INVALID_TASK_DESCRIPTION")
    require(isinstance(deps, list) and all(isinstance(d, str) and d in hub["cards"] for d in deps)
            and len(deps) == len(set(deps)), "INVALID_DEPENDENCY")
    references(refs)
    require(deliverable is None or description(deliverable), "INVALID_DELIVERABLE")
    role = match(kind)
    hub["cards"][task_id] = dict(project=project, task_id=task_id, task_type=kind, goal=goal,
        accountable="Main", responsible=role["role"], role_contract=role, dependencies=deps,
        inputs=refs, agreement_digest=bundle, deliverable=deliverable or role["deliverable"], criterion=criterion,
        permissions="READ_ONLY_PROPOSAL", authorization="NOT_GRANTED", execution="OPEN",
        evidence=[], verification="NOT_VERIFIED", scientific_decision="NOT_ASSESSED")


def apply(hub, event, project, revision, bundle):
    require(set(event) == {"schema", "project", "key", "op", "expected_revision", "main", "data"}
            and event["schema"] == SCHEMA and event["project"] == project
            and token(event["key"], r"[a-zA-Z0-9._-]{1,96}") and event["key"] not in hub["receipts"]
            and type(event["expected_revision"]) is int and event["expected_revision"] == revision
            and token(event["main"], "[0-9a-f]{64}"), "TASK_EVENT_CONFLICT")
    op, data = event["op"], event["data"]
    require(isinstance(data, dict), "INVALID_TASK_DATA")
    if op == "task-init":
        require(not hub["main"] and set(data) == {"summary", "drafts"} and description(data["summary"]),
                "INTAKE_ALREADY_BOUND_OR_INVALID")
        hub.update(main=event["main"], summary=data["summary"])
        drafts = data["drafts"]
        require(isinstance(drafts, dict) and set(drafts) == {"T01", "T02"}, "BOTH_INTAKE_CARDS_REQUIRED")
        for tid, kind in STARTERS:
            draft = drafts[tid]
            require(isinstance(draft, dict) and set(draft) == {"goal", "criterion", "deliverable", "refs"}
                    and description(draft["deliverable"]), "INVALID_INTAKE_CARD")
            create_card(hub, project, tid, kind, deps=[], bundle=bundle, **draft)
    else:
        require(hub["main"] == event["main"], "MAIN_IDENTITY_MISMATCH")
        if op == "task-create":
            require(set(data) == {"task_id", "kind", "goal", "criterion", "deps", "refs"}, "INVALID_TASK_DATA")
            create_card(hub, project, bundle=bundle, **data)
        elif op == "task-update":
            require(set(data) == {"task_id", "execution", "evidence"} and
                    token(data["task_id"], r"T[0-9]{2,6}") and data["task_id"] in hub["cards"]
                    and isinstance(data["execution"], str), "INVALID_TASK_DATA")
            card = hub["cards"][data["task_id"]]
            require(data["execution"] in TRANSITIONS[card["execution"]], "INVALID_TASK_TRANSITION")
            references(data["evidence"])
            if data["execution"] in ("IN_PROGRESS", "SUBMITTED"):
                require(all(hub["cards"][d]["execution"] == "SUBMITTED" for d in card["dependencies"]),
                        "UNMET_TASK_DEPENDENCY")
            if data["execution"] == "SUBMITTED":
                require(data["evidence"], "TASK_EVIDENCE_REQUIRED")
            card["execution"] = data["execution"]
            for ref in data["evidence"]:
                if ref not in card["evidence"]:
                    card["evidence"].append(ref)
        else:
            require(False, "INVALID_TASK_OPERATION")
    hub["receipts"][event["key"]] = {"digest": digest(event), "revision": revision + 1}


def view(project):
    state = {}
    with project._snapshot(agreement_state=state) as (_, meta, _, _):
        hub = state.get("task_hub", empty())
        return {"project": project.research_project_id, "revision": meta["project_revision"],
                "summary": hub["summary"], "tasks": list(hub["cards"].values()),
                "execution_authorized": False}


def record(project, request, op):
    require(isinstance(request, dict) and set(request) ==
            {"project", "expected_revision", "key", "desktop_project", "host", "data"}
            and request["project"] == project.research_project_id, "INVALID_TASK_REQUEST")
    owner = main_identity(request["host"], request["desktop_project"])
    event = {k: request[k] for k in ("project", "expected_revision", "key", "data")}
    event.update(schema=SCHEMA, op=op, main=owner)
    require(token(event["key"], r"[a-zA-Z0-9._-]{1,96}"), "INVALID_TASK_KEY")
    state = {}
    with project._snapshot(write=True, agreement_state=state) as (conn, meta, bundles, _):
        hub = state.get("task_hub", empty())
        receipt = hub["receipts"].get(event["key"])
        if receipt:
            require(receipt["digest"] == digest(event), "REQUEST_KEY_CONFLICT")
        else:
            bundle = bundles[-1][1] if bundles else None
            apply(hub, event, project.research_project_id, meta["project_revision"], bundle)
            _commit_workflow_event(conn, meta, bundle, event)
            conn.commit()
    reread = {}
    with project._snapshot(agreement_state=reread) as (_, meta, _, _):
        receipt = reread["task_hub"]["receipts"].get(event["key"])
        require(receipt and receipt["digest"] == digest(event), "TASK_READBACK_MISMATCH")
        return {"status": "REGISTERED_READ_BACK", "key": event["key"], **receipt,
                "project": project.research_project_id, "execution_authorized": False}


def apply_scoped(state, event, project_id, revision):
    flow = state.get("scoped_fixture")
    require(flow and event.get("main") == flow["scope"], "SCOPE_CONFLICT")
    require(event.get("schema") == "scoped-task-v1" and event.get("op") in {"task-create", "task-update"}
            and isinstance(event.get("data"), dict) and token(event["data"].get("task_id"), r"T[0-9]{2,6}")
            and event["data"]["task_id"] not in {"T01", "T02", "T03", "T04"}, "RESERVED_TASK_OR_OPERATION")
    require(token(event.get("key"), r"[A-Za-z0-9._-]{1,96}") and not event["key"].startswith("fixture.")
            and event["key"] not in flow["receipts"], "REQUEST_KEY_CONFLICT")
    hub = state["task_hub"]
    apply(hub, dict(event, schema=SCHEMA), project_id, revision, None)
    hub["receipts"][event["key"]]["digest"] = digest(event)
    card = hub["cards"][event["data"]["task_id"]]
    card["role_contract"]["session_status"] = "LOGICAL_STEP"
    card["host_attestation"] = "UNATTESTED"


def record_scoped(project, scope_id, request, op):
    """Write a task through the same ledger after transport scope validation."""
    require(isinstance(request, dict) and set(request) == {"project", "expected_revision", "key", "data"}
            and request["project"] == project.research_project_id, "INVALID_TASK_REQUEST")
    require(token(scope_id, "[0-9a-f]{64}") and token(request["key"], r"[A-Za-z0-9._-]{1,96}")
            and not request["key"].startswith("fixture."), "INVALID_TASK_KEY")
    event = dict(request, schema="scoped-task-v1", op=op, main=scope_id)
    state = {}
    with project._snapshot(write=True, agreement_state=state) as (conn, meta, bundles, _):
        flow = state.get("scoped_fixture")
        require(not bundles and flow and flow["scope"] == scope_id, "SCOPED_MAIN_REQUIRED")
        receipt = state["task_hub"]["receipts"].get(request["key"])
        if receipt:
            require(receipt["digest"] == digest(event), "REQUEST_KEY_CONFLICT")
        else:
            apply_scoped(state, event, project.research_project_id, meta["project_revision"])
            _commit_workflow_event(conn, meta, None, event)
            conn.commit()
    reread = {}
    with project._snapshot(agreement_state=reread) as (_, _, _, _):
        receipt = reread["task_hub"]["receipts"][request["key"]]
        require(receipt["digest"] == digest(event), "TASK_READBACK_MISMATCH")
        return dict(status="REGISTERED_READ_BACK", project=project.research_project_id,
                    key=request["key"], host_attestation="UNATTESTED", execution_authorized=False, **receipt)
