"""Installed Main-only project discovery, narrow read consent and evidence submission."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from aegiscae.contracts.research_contracts import require, strict_json
from aegiscae.research import task_cards
from aegiscae.research.capability_discovery import local, windows_installation
from abqjobpilot_readonly import binding_reference, save_observation, submit_observation


def deployment(plugin, host, desktop):
    scope = hashlib.sha256((host+"\n"+desktop).encode()).hexdigest()
    base = local(Path(os.environ["LOCALAPPDATA"]) / "GDCAE/engineering/v1" / scope)
    path = local(base / "deployment.json")
    require(path.is_file() and path.stat().st_size <= 8192, "SERVICE_DEPLOYMENT_MISSING")
    raw = path.read_bytes()
    profile = strict_json(raw)
    policy = strict_json((plugin / "runtime/abq-readonly.json").read_bytes())
    require(isinstance(profile, dict) and set(profile) == {"schema","provider","host","desktop","backend_id","backend_root"}
            and profile["schema"] == 1 and profile["provider"] == policy["provider"]
            and profile["host"] == host and profile["desktop"] == desktop, "DEPLOYMENT_SCOPE_MISMATCH")
    require(local(profile["backend_root"]).is_dir(), "BACKEND_PROJECT_UNAVAILABLE")
    archive = local(base / "server.zip")
    require(archive.is_file(), "SERVICE_SOURCE_MISSING")
    require(archive.stat().st_size == policy["source_bytes"]
            and hashlib.sha256(archive.read_bytes()).hexdigest() == policy["source_sha256"], "BACKEND_SOURCE_MISMATCH")
    return base, profile, policy, hashlib.sha256(raw).hexdigest()


def scope_for(plugin, project, host, desktop, queue):
    require(queue is None or (isinstance(queue,str) and 0 < len(queue) <= 256 and queue.isprintable()),
            "INVALID_QUEUE_ID")
    owner = task_cards.main_identity(host,desktop)
    state = {}
    with project._snapshot(agreement_state=state):
        hub = state.get("task_hub", {})
        require(hub.get("main") == owner, "MAIN_PROJECT_MISMATCH")
        card = hub.get("cards", {}).get("T02")
        require(card and card["task_type"] == "capability-discovery", "T02_REQUIRED")
    base, profile, policy, pin = deployment(plugin, host, desktop)
    research = project.research_project_id
    pair = binding_reference(research, profile["backend_id"])
    permit = {"reference":"abqjobpilot:T02-read-and-record", "sha256":task_cards.digest({
        "research":research, "task":"T02", "profile":pin, "source":policy["source_sha256"], "queue":queue})}
    return base, profile, policy, card, pair, permit


def authorized(card, pair, permit):
    refs = card["inputs"] + card["evidence"]
    require(permit in refs, "T02_READ_CONSENT_REQUIRED")
    require({r["sha256"] for r in refs if r["reference"] == pair["reference"]} == {pair["sha256"]},
            "BACKEND_PROJECT_NOT_BOUND")


def run(args, plugin, project, body):
    reading = args.operation == "t02-read"
    fields = {"queue_id","expected_revision","key"} if reading else {"queue_id"}
    require(isinstance(body,dict) and set(body) == fields, "INVALID_T02_REQUEST")
    host, desktop = args.host_id, args.desktop_project_id
    base, profile, policy, card, pair, permit = scope_for(plugin,project,host,desktop,body["queue_id"])
    if not reading:
        return {"status":"READ_PROPOSAL","task":"T02","installed_product":windows_installation(),
                "source_version":"0.2.2","source_commit":policy["source_commit"],"service":"NOT_QUERIED",
                "expected_backend_id":profile["backend_id"],"consent_refs":[pair,permit],"execution_authorized":False}
    require(task_cards.token(body["key"], r"[a-zA-Z0-9._-]{1,96}") and type(body["expected_revision"]) is int,
            "INVALID_T02_REQUEST")
    authorized(card,pair,permit)
    storage = local(base / "observations" / task_cards.digest(project.research_project_id))
    if card["execution"] == "SUBMITTED":
        # Only reuse an observation tied to this operation, not another submitter's file reference.
        for ref in reversed(card["evidence"]):
            if ref["reference"] != ref["sha256"]+".json":
                continue
            path = local(storage / ref["reference"])
            require(path.is_file() and path.stat().st_size <= 65536, "EVIDENCE_UNAVAILABLE")
            data = path.read_bytes()
            require(hashlib.sha256(data).hexdigest() == ref["sha256"], "EVIDENCE_DIGEST_MISMATCH")
            old = strict_json(data)
            if old.get("request_key") == body["key"] and old.get("consent") == permit["sha256"]:
                receipt = submit_observation(project,host,desktop,profile["backend_id"],storage,ref["sha256"],
                                             body["expected_revision"],body["key"])
                return {"status":"REPLAYED","artifact":ref,"observation":old,"receipt":receipt,"execution_authorized":False}
        raise ValueError("T02_ALREADY_SUBMITTED")
    require(card["execution"] == "IN_PROGRESS", "T02_NOT_IN_PROGRESS")
    require(task_cards.view(project)["revision"] == body["expected_revision"], "TASK_REVISION_CONFLICT")
    call = {"root":str(project._root),"host":host,"desktop":desktop,"queue":body["queue_id"],
            "binding":args.binding_sha256,"consent":permit["sha256"]}
    try:
        child = subprocess.run([sys.executable,"-I","-B","-S",str(plugin/"scripts/t02_worker.py")],
                               input=json.dumps(call).encode(),capture_output=True,timeout=75)
    except (OSError,subprocess.TimeoutExpired):
        raise ValueError("MCP_WORKER_UNAVAILABLE") from None
    require(0 < len(child.stdout) <= 65536, "MCP_WORKER_NO_RECEIPT")
    response = strict_json(child.stdout)
    if child.returncode or response.get("status") != "OBSERVED":
        reason = response.get("reason")
        raise ValueError(reason if task_cards.token(reason,r"[A-Z_]{3,64}") else "MCP_SESSION_FAILED")
    report = response["observation"]
    require(report["research_project"] == project.research_project_id and report["task_id"] == "T02"
            and report["backend_project"] == profile["backend_id"] and report["execution_authorized"] is False
            and response["consent"] == permit["sha256"], "EVIDENCE_SCOPE_MISMATCH")
    report.update(consent=permit["sha256"],request_key=body["key"],source_commit=policy["source_commit"])
    _, _, _, latest, current_pair, current_permit = scope_for(plugin,project,host,desktop,body["queue_id"])
    require((pair, permit) == (current_pair, current_permit), "EVIDENCE_SCOPE_MISMATCH")
    authorized(latest, current_pair, current_permit)
    require(latest["execution"] == "IN_PROGRESS" and task_cards.view(project)["revision"] == body["expected_revision"], "TASK_REVISION_CONFLICT")
    storage.mkdir(parents=True,exist_ok=True)
    ref = save_observation(report,storage)
    receipt = submit_observation(project,host,desktop,profile["backend_id"],storage,ref["sha256"],
                                 body["expected_revision"],body["key"])
    return {"status":"REGISTERED_READ_BACK","observation":report,"artifact":ref,"receipt":receipt,"execution_authorized":False}
