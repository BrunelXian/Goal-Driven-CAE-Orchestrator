"""Legacy Host-attested task writer and compatibility exports for the common task ledger."""
import json
import os
from pathlib import Path

from aegiscae.contracts.research_contracts import digest_bytes, require
from aegiscae.research.project import _commit_workflow_event
from aegiscae.research.project_tasks import (
    SCHEMA, STARTERS, TRANSITIONS, apply, apply_scoped, create_card, description,
    digest, empty, record_scoped, references, token, view,
)


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
