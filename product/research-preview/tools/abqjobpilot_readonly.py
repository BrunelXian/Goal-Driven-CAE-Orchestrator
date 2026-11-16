"""Read-only T02 adapter for an operator-trusted AbqJobPilot 0.2.2 MCP connection."""
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from aegiscae.contracts.research_contracts import canonical_json, require
from aegiscae.research import task_cards
from aegiscae.research.capability_discovery import local

TOOLS = {"abq_list_jobs", "abq_job_status", "abq_locate_outputs", "abq_preflight", "abq_prepare_enqueue"}
STATUS = {"QUEUED", "DATACHECK", "RUNNING", "COMPLETED", "FAILED", "CANCELLED", "SKIPPED",
          "LOCKED", "ODB_MISSING", "UNKNOWN"}


def binding_reference(research_id, backend_id):
    """Main approves this pair independently of the server response."""
    uuid_pattern = r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}"
    require(isinstance(backend_id, str) and re.fullmatch(uuid_pattern, backend_id), "INVALID_BACKEND_PROJECT")
    return {"reference": "abqjobpilot:project",
            "sha256": task_cards.digest({"research_project": research_id, "backend_project": backend_id})}


def check_task(project, host, desktop, backend_id, *, retry=False):
    owner = task_cards.main_identity(host, desktop)
    state = {}
    with project._snapshot(agreement_state=state):
        hub = state.get("task_hub") or {}
        require(hub.get("main") == owner, "MAIN_PROJECT_MISMATCH")
        card = hub["cards"].get("T02")
        allowed_states = ("IN_PROGRESS", "SUBMITTED") if retry else ("IN_PROGRESS",)
        require(card and card["task_type"] == "capability-discovery" and card["execution"] in allowed_states,
                "T02_NOT_IN_PROGRESS")
        expected = binding_reference(project.research_project_id, backend_id)
        pins = {r["sha256"] for r in card["inputs"] + card["evidence"] if r["reference"] == expected["reference"]}
        require(pins == {expected["sha256"]}, "BACKEND_PROJECT_NOT_BOUND")


async def _read(client, name, args, backend_id):
    result = await client.call_tool(name, args)
    body = result.structured_content
    require(not result.is_error and isinstance(body, dict), "MCP_CALL_FAILED")
    require(body.get("project_id") == backend_id, "BACKEND_PROJECT_MISMATCH")
    require(body.get("schema_version") == "1.0" and body.get("errors") == []
            and body.get("error_details") == [] and isinstance(body.get("data"), dict), "BACKEND_RESPONSE_REJECTED")
    # Keep the response digest; paths, user job names and log tails stay out of the retained receipt.
    data = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False).encode("ascii")
    return body, hashlib.sha256(data).hexdigest()


async def observe(client, project, host, desktop, backend_id, *, queue_id=None):
    """Only a trusted caller supplies the connected client. No backend writes or task transitions."""
    check_task(project, host, desktop, backend_id)
    server = client.server_info
    require(server and server.name == "AbqJobPilot" and server.version == "0.2.2"
            and client.protocol_version == "2025-11-25", "MCP_SERVER_INCOMPATIBLE")
    listing = await client.list_tools()
    names = [t.name for t in listing.tools]
    require(not listing.next_cursor and len(names) == len(TOOLS) and set(names) == TOOLS
            and all(t.annotations and t.annotations.read_only_hint is True
                    and t.annotations.destructive_hint is False for t in listing.tools), "MCP_TOOLSET_INCOMPATIBLE")
    for tool in listing.tools:
        if tool.name in ("abq_list_jobs", "abq_job_status"):
            schema = tool.input_schema
            fields = schema.get("properties", {})
            expected = {"scope", "limit"} if tool.name == "abq_list_jobs" else {"scope", "identifier"}
            require(schema.get("type") == "object" and expected <= fields.keys()
                    and set(schema.get("required", [])) <= expected, "MCP_INPUT_SCHEMA_INCOMPATIBLE")
    checksums = {}
    counts = {}
    for scope in ("queue", "history"):
        reply, checksums[scope] = await _read(client, "abq_list_jobs", {"scope": scope, "limit": 50}, backend_id)
        data = reply["data"]
        require(reply.get("status") == "OK" and data.get("scope") == scope and data.get("limit") == 50
                and isinstance(data.get("jobs"), list) and len(data["jobs"]) <= 50, "INVALID_JOB_LIST")
        counts[scope] = len(data["jobs"])
    detail = None
    if queue_id is not None:
        require(isinstance(queue_id, str) and 0 < len(queue_id) <= 256, "INVALID_QUEUE_ID")
        reply, checksums["status"] = await _read(client, "abq_job_status",
                                                 {"scope": "queue", "identifier": queue_id}, backend_id)
        data = reply["data"]
        observed = data.get("observed_status")
        require(data.get("scope") == "queue" and data.get("queue_id") == queue_id
                and data.get("active_execution_confirmed") is False and observed in STATUS
                and reply.get("status") == ("STATUS_UNCONFIRMED" if observed == "RUNNING" else observed),
                "INVALID_JOB_STATUS")
        # The public API may echo an unknown queue identifier even when it cannot locate a job.
        require(observed != "UNKNOWN", "JOB_STATUS_UNVERIFIED")
        detail = {"identifier_sha256": hashlib.sha256(queue_id.encode()).hexdigest(),
                  "status": reply["status"], "active_execution_confirmed": False}
    return {"schema": "gdcae-t02-abq-read-v1", "task_id": "T02", "research_project": project.research_project_id,
            "backend_project": backend_id, "server": server.name, "version": server.version,
            "protocol": str(client.protocol_version), "tools": sorted(names), "sample_limit": 50,
            "rows_returned": counts, "queue_status": detail, "response_sha256": checksums,
            "observed_utc": datetime.now(timezone.utc).isoformat(), "execution_authorized": False}


def save_observation(report, evidence_dir):
    """Publish complete canonical bytes under their digest in an explicitly selected existing directory."""
    directory = local(evidence_dir)
    require(directory.is_dir(), "EVIDENCE_DIRECTORY_REQUIRED")
    body = canonical_json(report)
    pin = hashlib.sha256(body).hexdigest()
    path = local(directory / (pin + ".json"))
    with tempfile.TemporaryDirectory(dir=directory) as tmp:
        temp = Path(tmp) / "receipt"
        with temp.open("xb") as stream:
            stream.write(body)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temp, path)
        except FileExistsError:
            pass
        require(local(path).is_file() and path.stat().st_size == len(body)
                and path.read_bytes() == body, "EVIDENCE_READBACK_FAILED")
    return {"reference": path.name, "sha256": pin}



def submit_observation(project, host, desktop, backend_id, evidence_dir, pin, revision, key):
    """Use only a pin independently delivered by the reviewed capture, never one derived from the input file."""
    from aegiscae.contracts.research_contracts import strict_json

    check_task(project, host, desktop, backend_id, retry=True)
    require(isinstance(pin, str) and re.fullmatch("[0-9a-f]{64}", pin), "INVALID_EVIDENCE_PIN")
    path = local(local(evidence_dir) / (pin + ".json"))
    require(path.is_file() and path.stat().st_size <= 65536, "EVIDENCE_UNAVAILABLE")
    body = path.read_bytes()
    require(hashlib.sha256(body).hexdigest() == pin, "EVIDENCE_DIGEST_MISMATCH")
    report = strict_json(body)
    require(report.get("schema") == "gdcae-t02-abq-read-v1" and report.get("task_id") == "T02"
            and report.get("backend_project") == backend_id and report.get("research_project") == project.research_project_id
            and report.get("execution_authorized") is False, "EVIDENCE_SCOPE_MISMATCH")
    return task_cards.record(project, {
        "host": host, "desktop_project": desktop, "project": project.research_project_id,
        "key": key, "expected_revision": revision,
        "data": {"task_id": "T02", "execution": "SUBMITTED",
                 "evidence": [{"reference": path.name, "sha256": pin}]},
    }, "task-update")
