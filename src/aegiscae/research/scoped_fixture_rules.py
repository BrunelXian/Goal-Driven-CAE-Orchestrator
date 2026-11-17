"""Pure replay and independent interval validation for the scoped fixture event."""
import re
from decimal import Decimal, ROUND_HALF_UP

from aegiscae.contracts.research_contracts import require
from aegiscae.research import task_cards
from aegiscae.research.scoped_fixture_port import BASELINE, validate_candidate

digest = task_cards.digest
SCHEMA = "scoped-fixture-workflow-v1"
GOAL = {"target_mm": "1.0", "tolerance_mm": "0.1", "selector": "fixture-tip",
        "direction": "downward-positive", "unit": "mm"}
ACTIONS = {"NEW": "START", "QUALIFIED": "PROPOSE_CANDIDATE", "NEXT_CANDIDATE": "PROPOSE_CANDIDATE",
           "CANDIDATE": "EXECUTE_FIXTURE_ONCE", "CLAIMED": "QUERY_ORIGINAL_KEY_ONLY",
           "OBSERVED": "VALIDATE", "GOAL_MET": "STOP", "BUDGET_EXHAUSTED": "STOP"}


def initial():
    return {"state": "NEW", "candidates": [], "runs_used": 0, "receipts": {}, "scope": None,
            "max_runs": None}


def proposal_for(flow):
    force = 50
    if flow["candidates"]:
        previous = flow["candidates"][-1]
        mm = Decimal(previous["observed_mm"])
        require(mm > 0, "INVERSE_UNDEFINED")
        force = int((Decimal(previous["force_N"]) * Decimal(GOAL["target_mm"]) / mm)
                    .to_integral_value(rounding=ROUND_HALF_UP))
    proposal = {"force_N": force, "unit": "N", "baseline_digest": digest(BASELINE)}
    validate_candidate(proposal)
    return proposal


def inputs_for(project, scope, index, proposal):
    validate_candidate(proposal)
    key = digest([project, scope, index, proposal])
    return {"project": project, "scope": scope, "candidate": index, "request_key": key,
            "proposal": proposal}


def check_reading(reading, candidate):
    """Check selected quantity, exact original request and producer receipt, independently of response law."""
    expected = {"input_digest": candidate["input_digest"], "request_key": candidate["request_key"],
                "project": candidate["inputs"]["project"], "scope": candidate["inputs"]["scope"],
                "baseline_digest": digest(BASELINE), "backend_kind": "FIXTURE",
                "real_solver_executed": False, "selector": GOAL["selector"],
                "direction": GOAL["direction"], "unit": GOAL["unit"]}
    require(type(reading) is dict and set(reading) == set(expected) | {"value"}
            and all(type(reading[k]) is type(v) and reading[k] == v for k,v in expected.items()),
            "FIXTURE_EVIDENCE_BINDING")
    require(type(reading["value"]) is str and re.fullmatch(r"[0-9]{1,8}(?:\.[0-9]{1,12})?", reading["value"]),
            "INVALID_OBSERVATION")


def decision_for(candidate):
    reading = candidate["receipt"]
    check_reading(reading, candidate)
    require(digest(reading) == candidate["evidence_digest"] and candidate["observed_mm"] == reading["value"],
            "FIXTURE_EVIDENCE_BINDING")
    error = abs(Decimal(reading["value"]) - Decimal(GOAL["target_mm"]))
    return {"decision": "WITHIN_TARGET" if error <= Decimal(GOAL["tolerance_mm"]) else "OUTSIDE_TARGET",
            "absolute_error_mm": str(error), "criterion": GOAL, "evidence_digest": digest(reading)}


def _tasks(flow, hub, project, revision, action, payload):
    """Project this transaction into the same native Task Card hub and transition checks."""
    def emit(op, data, suffix):
        event = dict(schema=task_cards.SCHEMA, project=project, main=flow["scope"], op=op,
                     expected_revision=revision, key=f"fixture.{revision}.{suffix}", data=data)
        task_cards.apply(hub, event, project, revision, None)
        task_id = data.get("task_id")
        for card in ([hub["cards"][task_id]] if task_id else hub["cards"].values()):
            card["role_contract"]["session_status"] = "LOGICAL_STEP"
            card["host_attestation"] = "UNATTESTED"

    def update(task_id, execution, refs):
        emit("task-update", {"task_id": task_id, "execution": execution, "evidence": refs},
             task_id + execution)

    if action == "START":
        drafts = {"T01": {"goal": "Qualify synthetic model and frozen selectors",
                          "criterion": "Exactly match the pinned fixture baseline",
                          "deliverable": "Synthetic baseline digest", "refs": []},
                  "T02": {"goal": "Identify the selected local test instrument",
                          "criterion": "Record source classification and execution limits",
                          "deliverable": "Fixture capability record", "refs": []}}
        emit("task-init", {"summary": "Enter logical Research Main for scoped displacement fixture",
                           "drafts": drafts}, "init")
        for tid, ref, sha in [("T01", "fixture-baseline", digest(BASELINE)),
                              ("T02", "operator-scope", flow["scope"])]:
            update(tid, "IN_PROGRESS", [])
            update(tid, "SUBMITTED", [{"reference": ref, "sha256": sha}])
        for tid, kind, goal, criterion in [
                ("T03", "candidate-design", "Propose bounded F and supply its exact input",
                 "One scalar in N from the authorized baseline"),
                ("T04", "independent-review", "Evaluate returned tip displacement",
                 "Recompute absolute error against the frozen inclusive tolerance")]:
            emit("task-create", dict(task_id=tid, kind=kind, goal=goal, criterion=criterion,
                                     deps=["T01","T02"], refs=[]), tid)
    elif action == "PROPOSE_CANDIDATE":
        update("T03", "IN_PROGRESS", [])
        update("T03", "SUBMITTED", [{"reference": "candidate-input", "sha256": digest(payload)}])
    elif action == "VALIDATE":
        update("T04", "IN_PROGRESS", [])
        update("T04", "SUBMITTED", [{"reference": "fixture-measurement",
                                     "sha256": payload["evidence_digest"]},
                                    {"reference": "interval-decision", "sha256": digest(payload)}])


def apply(flow, hub, event, project, revision):
    require(set(event) == {"schema","project","scope","max_runs","key","expected_revision",
                           "operation","proposal","action","payload"}
            and event["schema"] == SCHEMA and event["project"] == project
            and task_cards.token(event["key"], r"[A-Za-z0-9._-]{1,96}")
            and event["key"] not in flow["receipts"] and event["key"] not in hub["receipts"]
            and not event["key"].startswith("fixture.")
            and type(event["expected_revision"]) is int and event["expected_revision"] == revision
            and task_cards.token(event["scope"], "[0-9a-f]{64}")
            and type(event["max_runs"]) is int and 0 <= event["max_runs"] <= 3,
            "FIXTURE_EVENT_CONFLICT")
    action, payload, supplied = event["action"], event["payload"], event["proposal"]
    require(action == ACTIONS[flow["state"]] and action != "STOP"
            and event["operation"] == ("start" if action == "START" else "advance")
            and (supplied is None or action == "PROPOSE_CANDIDATE"), "ILLEGAL_STEP")
    if action == "START":
        require(digest(payload) == digest({"baseline": BASELINE, "goal": GOAL, "host_attestation": "UNATTESTED",
                            "stage": "RESEARCH_MAIN", "role_mode": "LOGICAL_STEP"}), "FREEZE_CONFLICT")
        flow.update(scope=event["scope"], max_runs=event["max_runs"],
                    state="QUALIFIED" if event["max_runs"] else "BUDGET_EXHAUSTED")
    else:
        require(flow["scope"] == event["scope"] and flow["max_runs"] == event["max_runs"], "SCOPE_CONFLICT")
        if action == "PROPOSE_CANDIDATE":
            require(flow["runs_used"] < flow["max_runs"], "BUDGET_EXHAUSTED")
            proposal = proposal_for(flow) if supplied is None else supplied
            expected = inputs_for(project, flow["scope"], len(flow["candidates"])+1, proposal)
            require(digest(payload) == digest(expected), "CANDIDATE_MISMATCH")
            flow["candidates"].append({"inputs": expected, "input_digest": digest(expected),
                                       "force_N": proposal["force_N"], "request_key": expected["request_key"]})
            flow["state"] = "CANDIDATE"
        else:
            candidate = flow["candidates"][-1]
            if action == "EXECUTE_FIXTURE_ONCE":
                require(flow["runs_used"] < flow["max_runs"], "BUDGET_EXHAUSTED")
                check_reading(payload, candidate)
                candidate["receipt"] = payload
                flow["runs_used"] += 1
                flow["state"] = "CLAIMED"
            elif action == "QUERY_ORIGINAL_KEY_ONLY":
                require(payload == {"request_key": candidate["request_key"],
                                    "receipt_digest": digest(candidate["receipt"])}, "RECEIPT_MISMATCH")
                candidate.update(observed_mm=candidate["receipt"]["value"],
                                 evidence_digest=payload["receipt_digest"])
                flow["state"] = "OBSERVED"
            else:
                require(payload == decision_for(candidate), "DECISION_MISMATCH")
                candidate.update(decision=payload["decision"], validation=payload)
                if payload["decision"] == "WITHIN_TARGET":
                    flow["state"] = "GOAL_MET"
                elif flow["runs_used"] == flow["max_runs"]:
                    flow["state"] = "BUDGET_EXHAUSTED"
                else:
                    flow["state"] = "NEXT_CANDIDATE"
    _tasks(flow, hub, project, revision, action, payload)
    flow["receipts"][event["key"]] = {"operation": event["operation"], "proposal": supplied,
                                      "expected_revision": revision, "revision": revision+1}
