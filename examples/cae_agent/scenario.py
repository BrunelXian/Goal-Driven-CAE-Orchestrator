"""Standard MCP stdio replay for the separately provisioned research example.

The proposal tape is test data. The live MCP responses determine legal steps,
evidence references, revision, independent checks and the stopping point.
"""

import argparse
import asyncio
import hashlib
import json
import os
from decimal import Decimal
from pathlib import Path

from call import stdio_connect


HERE = Path(__file__).resolve().parent


def digest(value):
    blob = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return hashlib.sha256(blob.encode("ascii")).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


async def call_recorded(call, log, name, args, *, rejected=None):
    reply = await call(name, args)
    log.append({"tool": name, "arguments": args, "result": reply,
                "request_sha256": digest(args), "response_sha256": digest(reply)})
    if rejected is not None:
        require(reply.get("error") == rejected, f"{name} expected {rejected}, got {reply.get('error')}")
        return None
    require(reply.get("error") is None and isinstance(reply.get("data"), dict),
            f"{name} failed: {reply.get('error')}")
    return reply["data"]


def event(project_id, state, key):
    return {"project_id": project_id, "expected_revision": state["revision"], "key": key}


def proposal(contract, row, evidence_refs):
    return {"parameter": contract["parameter"]["name"], "unit": contract["parameter"]["unit"],
            "baseline_digest": contract["baseline_sha256"], "value": row["value"],
            "reason": row["reason"], "evidence_refs": list(evidence_refs)}


async def snapshot(call, log, pid):
    project = await call_recorded(call, log, "gdcae_project_open", {})
    tasks = await call_recorded(call, log, "gdcae_task_list", pid)
    workflow = await call_recorded(call, log, "gdcae_workflow_status", pid)
    require(project["project_id"] == pid["project_id"]
            and project["revision"] == tasks["revision"] == workflow["revision"],
            "Inconsistent project, task or workflow identity")
    return {"project": project, "tasks": tasks, "workflow": workflow}


async def submit_row(call, log, pid, state, contract, row, refs, key, *, rejected=None):
    request = dict(event(pid["project_id"], state, key), proposal=proposal(contract, row, refs))
    await call_recorded(call, log, "gdcae_candidate_propose", request, rejected=rejected)
    observed = await call_recorded(call, log, "gdcae_workflow_status", pid)
    require(observed["runs_used"] == state["runs_used"], "Proposal spent execution budget")
    if rejected is not None:
        require(observed == state, "Rejected proposal mutated the workflow")
    else:
        require(observed["revision"] > state["revision"], "Missing candidate revision")
    return observed


async def evaluate(call, log, pid, state):
    """Advance this single accepted candidate, never propose a replacement."""
    for _ in range(8):
        if state["next_action"] in {"STOP", "PROPOSE_CANDIDATE"}:
            return state
        request = event(pid["project_id"], state, f"advance-{state['revision']}")
        await call_recorded(call, log, "gdcae_workflow_advance", request)
        state = await call_recorded(call, log, "gdcae_workflow_status", pid)
    raise RuntimeError("No candidate decision within the bounded protocol replay")


def verify_candidate(candidate, contract):
    reading = candidate["receipt"]
    decision = candidate["validation"]
    goal = contract["goal"]
    for field in ("metric", "unit", "direction", "selector"):
        require(reading[field] == goal[field], f"Measurement selector mismatch: {field}")
    require(reading["value"] == candidate["observed_value"] and reading["real_solver_executed"] is False
            and reading["backend_kind"] == contract["backend"]["kind"]
            and reading["backend_id"] == contract["backend"]["id"], "Incorrect evidence source")
    require(reading["input_digest"] == digest(candidate["inputs"])
            and reading["request_key"] == candidate["request_key"]
            and reading["contract_digest"] == digest(contract)
            and reading["project"] == candidate["inputs"]["project"]
            and reading["scope"] == candidate["inputs"]["scope"]
            and reading["baseline_digest"] == contract["baseline_sha256"], "Evidence linkage mismatch")
    actual = Decimal(reading["value"])
    error = abs(actual - Decimal(goal["target"]))
    expected = "WITHIN_TARGET" if error <= Decimal(goal["tolerance"]) else "OUTSIDE_TARGET"
    require(candidate["decision"] == expected == decision["decision"]
            and candidate["evidence_digest"] == digest(reading) == decision["evidence_digest"],
            "Independent contract decision differs")
    return {"candidate": candidate["value"], "observation": reading["value"], "unit": reading["unit"],
            "evidence_sha256": digest(reading), "decision": expected, "absolute_error": str(error)}


def public_log(log, project):
    serialized = json.dumps(log, ensure_ascii=True)
    for key, alias in (("project_id", "<project>"), ("storage_generation", "<storage>")):
        value = project.get(key)
        if isinstance(value, str) and value:
            serialized = serialized.replace(value, alias)
    return json.loads(serialized)


async def run_case(connect, case_path=None):
    """Use the exact records supplied by a test case, with causal references read from MCP."""
    path = Path(case_path) if case_path else HERE / "test-proposals.json"
    tape = json.loads(path.read_text(encoding="utf-8"))
    require(tape["source"] == "SCRIPTED_PROTOCOL_TEST_DATA" and len(tape["proposals"]) == 2,
            "This regression requires a two-row scripted proposal tape")
    log = []
    async with connect() as call:
        project = await call_recorded(call, log, "gdcae_project_open", {})
        pid = {"project_id": project["project_id"]}
        initial = await call_recorded(call, log, "gdcae_workflow_status", pid)
        require(initial["state"] == "NEW", "Replay requires a fresh operator-provisioned project")
        await call_recorded(call, log, "gdcae_workflow_start",
                            event(pid["project_id"], initial, "enter-main"))
        active = await call_recorded(call, log, "gdcae_workflow_status", pid)
        contract = active["contract"]
        require(contract["backend"]["kind"] == "FIXTURE" and active["runs_used"] == 0,
                "An isolated Fixture scope is required")
        await submit_row(call, log, pid, active, contract, tape["out_of_bounds"], [], "invalid",
                         rejected="PARAMETER_OUT_OF_BOUNDS")
        first = await submit_row(call, log, pid, active, contract, tape["proposals"][0], [], "sample-a")
        first = await evaluate(call, log, pid, first)
        require(first["runs_used"] == 1 and len(first["candidates"]) == 1,
                "First candidate was not evaluated exactly once")
        first_check = verify_candidate(first["candidates"][0], contract)
        require(first_check["decision"] == "OUTSIDE_TARGET", "Missing first target miss")
        checkpoint = await snapshot(call, log, pid)

    async with connect() as call:
        recovered = await snapshot(call, log, pid)
        require(recovered == checkpoint, "Reopened task/plan/candidate/evidence snapshot differs")
        first_evidence = await call_recorded(call, log, "gdcae_evidence_read", {**pid, "candidate": 1})
        require(first_evidence["candidate"]["evidence_digest"] == first_check["evidence_sha256"],
                "Reopened evidence identity differs")
        refs = [first_evidence["candidate"]["evidence_digest"]]
        require(first_evidence["candidate"]["receipt"] == first["candidates"][0]["receipt"],
                "Reopened original reading differs")
        second = await submit_row(call, log, pid, recovered["workflow"], contract,
                                  tape["proposals"][1], refs, "sample-b")
        second = await evaluate(call, log, pid, second)
        require(second["state"] == "GOAL_MET" and second["runs_used"] == 2
                and len(second["candidates"]) == 2, "Unexpected terminal state or count")
        final_candidate = second["candidates"][1]
        second_check = verify_candidate(final_candidate, contract)
        require(final_candidate["inputs"]["proposal"]["evidence_refs"] == refs
                and first_check["evidence_sha256"] != second_check["evidence_sha256"],
                "Causal candidate/evidence chain differs")
        evidence = await call_recorded(call, log, "gdcae_evidence_read", {**pid, "candidate": 2})
        require(evidence["candidate"] == final_candidate
                and evidence["candidate"]["evidence_digest"] == second_check["evidence_sha256"],
                "Final returned evidence differs")
        terminal = await snapshot(call, log, pid)

    async with connect() as call:
        reopened = await snapshot(call, log, pid)
        require(reopened == terminal, "Terminal project, task or workflow differs after reconnect")

    return {"proposal_source": tape["source"], "model_turns": 0, "backend_kind": "FIXTURE",
            "real_solver_executed": False, "contract": contract, "decisions": [first_check, second_check],
            "recovery": {"after_miss_sha256": digest(checkpoint), "terminal_sha256": digest(terminal),
                         "restored_state": recovered["workflow"]["state"],
                         "restored_next_action": recovered["workflow"]["next_action"],
                         "restored_revision": recovered["workflow"]["revision"],
                         "terminal_revision": reopened["workflow"]["revision"]},
            "terminal_state": second["state"],
            "counts": {"tool_calls": len(log), "fresh_sessions": 3,
                       "fixture_executions": second["runs_used"], "real_solver_calls": 0,
                       "in_scope_human_interventions": 0},
            "receipts": public_log(log, project)}


def main():
    parser = argparse.ArgumentParser(description="Run the explicitly scripted research MCP regression")
    parser.add_argument("--binding-file", required=True, type=Path)
    parser.add_argument("--source", type=Path, help="Source package root for a development installation")
    parser.add_argument("--case", type=Path, default=HERE / "test-proposals.json")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output must be a new file")
    pin = os.environ.get("GDCAE_BINDING_SHA256")
    if not pin:
        parser.error("supply the operator-provided GDCAE_BINDING_SHA256")
    connect = stdio_connect(args.binding_file.resolve(), pin,
                            source=args.source.resolve() if args.source else None)
    report = asyncio.run(run_case(connect, args.case))
    report["surface"] = "STANDARD_MCP_SDK_STDIO"
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    print(json.dumps(report["counts"]))


if __name__ == "__main__":
    main()
