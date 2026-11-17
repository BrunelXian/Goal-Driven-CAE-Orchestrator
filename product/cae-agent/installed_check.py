"""Exercise an installed Codex adapter with an external caller's exact proposal.

Each invocation opens a fresh local Host. Inspect the contract/evidence first.
To propose, pass a JSON object with expected_revision, key and proposal. Values,
units, rationale and observation references come from the caller.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from host_probe import InstalledHost, digest


def execute(args):
    profile = json.loads((args.home / "cae-agent/deployment.json").read_bytes())
    out = {"surface": "Desktop-bundled app-server; external tool caller; no native Desktop model turn",
           "product": "CAE Agent", "version": "0.3.1", "requests": [], "classic": {},
           "proposal_origin": "EXTERNAL_CLIENT_INPUT" if args.proposal_file else None}
    host = InstalledHost(args.codex, args.home, args.market, plugin_name="cae-agent",
                         plugin_id="cae-agent@cae-agent-local",
                         required_services=("gdcae-core", "abqjobpilot") if profile["classic"] else ("gdcae-core",))
    project_id = storage = None
    observations = []

    def call(tool, data):
        result = host.call(tool, data)
        out["requests"].append({"tool": tool, "arguments": data, "result": result})
        if result.get("error"):
            raise ValueError(result["error"])
        return result["data"]

    try:
        with host:
            out["plugin"] = host.plugin
            out["host"] = host.host_version
            out["servers"] = host.servers
            if host.servers["gdcae-core"]["info"]["version"] != "0.3.1":
                raise ValueError("WRONG_CORE_VERSION")
            if args.classic_check:
                classic = profile["classic"]
                if not classic or host.servers["abqjobpilot"]["tools"] != ["abq_job_status", "abq_list_jobs"]:
                    raise ValueError("CLASSIC_UNAVAILABLE")
                for scope in ("queue", "history"):
                    jobs = host.call("abq_list_jobs", {"scope": scope, "limit": 50})
                    if jobs["project_id"] != classic["backend_id"] or jobs["errors"]:
                        raise ValueError("CLASSIC_IDENTITY_MISMATCH")
                    out["classic"][scope] = len(jobs["data"]["jobs"])
                if classic["queue_id"]:
                    result = host.call("abq_job_status", {"scope": "queue", "identifier": classic["queue_id"]})
                    if result["project_id"] != classic["backend_id"] or result["errors"]:
                        raise ValueError("CLASSIC_STATUS_UNAVAILABLE")
                    out["classic"].update(status=result["status"],
                                          active_execution_confirmed=result["data"]["active_execution_confirmed"])
            project = call("gdcae_project_open", {})
            project_id, storage = project["project_id"], project["storage_generation"]
            pid = {"project_id": project_id}
            out["diagnostics"] = call("gdcae_diagnostics", pid)
            call("gdcae_task_list", pid)
            state = call("gdcae_workflow_status", pid)
            if state["state"] == "NEW":
                call("gdcae_workflow_start", dict(pid, key="main-enter", expected_revision=project["revision"]))
                state = call("gdcae_workflow_status", pid)
            if state["contract"]["backend"]["kind"] != "FIXTURE":
                raise ValueError("TEST_ONLY_BACKEND_REQUIRED")
            for index, c in enumerate(state["candidates"], start=1):
                if "receipt" in c:
                    call("gdcae_evidence_read", dict(pid, candidate=index))
            if args.query_key:
                out["reconciliation"] = call("gdcae_workflow_status", dict(pid, request_key=args.query_key))
            if args.proposal_file:
                proposal = json.loads(args.proposal_file.read_bytes())
                if set(proposal) != {"expected_revision", "key", "proposal"}:
                    raise ValueError("EXACT_PROPOSAL_REQUEST_REQUIRED")
                result = host.call("gdcae_candidate_propose", dict(pid, **proposal))
                out["requests"].append({"tool": "gdcae_candidate_propose", "arguments": dict(pid, **proposal),
                                        "result": result})
                out["proposal_result"] = result
                current = call("gdcae_workflow_status", pid)
                if result["error"]:
                    if current != state:
                        raise ValueError("REFUSAL_CHANGED_STATE")
                else:
                    state = current
                    for _ in range(8):
                        if state["next_action"] in {"STOP", "PROPOSE_CANDIDATE"}:
                            break
                        call("gdcae_workflow_advance", dict(pid, key="step-" + str(state["revision"]),
                             expected_revision=state["revision"]))
                        state = call("gdcae_workflow_status", pid)
                    else:
                        raise ValueError("UNRESOLVED_NEXT_ACTION")
            for index, row in enumerate(state["candidates"], start=1):
                if "receipt" in row:
                    candidate = call("gdcae_evidence_read", dict(pid, candidate=index))["candidate"]
                    observations.append({"index": index, "value": candidate["value"],
                                         "observation": candidate["observed_value"],
                                         "decision": candidate["decision"], "evidence_sha256": candidate["evidence_digest"]})
            out.update(contract=state["contract"], state=state["state"], next_action=state["next_action"],
                       runs_used=state["runs_used"], revision=state["revision"], observations=observations)
            out["snapshot_sha256"] = digest({"project": call("gdcae_project_open", {}),
                                              "tasks": call("gdcae_task_list", pid), "workflow": state})
            out["status"] = "COMPLETE"
    except Exception as exc:
        out.update(status="PARTIAL", failure=str(exc)[:300])
    out.update(calls=host.calls, host_exit=host.exit_code, process_cleanup=host.cleanup)
    if host.exit_code != 0 or not host.cleanup or host.cleanup["forced"] or host.cleanup["surviving_descendants"]:
        out["status"] = "PARTIAL"
    data = json.dumps(out, ensure_ascii=True, indent=2)
    for key, label in ((project_id, "<project>"), (storage, "<storage>")):
        if key:
            data = data.replace(key, label)
    return json.loads(data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("codex", "home", "market", "output"):
        parser.add_argument("--" + key, type=Path, required=True)
    parser.add_argument("--classic-check", action="store_true")
    selector = parser.add_mutually_exclusive_group()
    selector.add_argument("--proposal-file", type=Path)
    selector.add_argument("--query-key")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("use a fresh receipt path")
    report = execute(args)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, ensure_ascii=True)
    print(json.dumps({k: v for k, v in report.items() if k in {
        "status", "failure", "state", "contract", "revision", "runs_used", "observations", "next_action",
        "process_cleanup", "classic", "proposal_result", "snapshot_sha256"}}, ensure_ascii=True))
    sys.exit(0 if report["status"] == "COMPLETE" else 2)
