"""Replay rules for both versions of the scoped workflow in the Core project transaction log."""
import re
from decimal import Decimal

from aegiscae.contracts.research_contracts import require
from aegiscae.research import agent_contract, project_tasks
from aegiscae.research.scoped_fixture_port import BASELINE, GOAL, rehearsal_proposal, validate_candidate

digest = project_tasks.digest
SCHEMA = "scoped-fixture-workflow-v1"
ACTIONS = {"NEW": "START", "CONTRACT_FROZEN": "PROPOSE_CANDIDATE", "QUALIFIED": "PROPOSE_CANDIDATE", "NEXT_CANDIDATE": "PROPOSE_CANDIDATE",
           "CANDIDATE": "EXECUTE_FIXTURE_ONCE", "CLAIMED": "QUERY_ORIGINAL_KEY_ONLY",
           "OBSERVED": "VALIDATE", "GOAL_MET": "STOP", "BUDGET_EXHAUSTED": "STOP", "BACKEND_UNAVAILABLE": "STOP"}


def initial():
    return {"state": "NEW", "candidates": [], "runs_used": 0, "receipts": {}, "scope": None,
            "max_runs": None}


def inputs_for(project, scope, index, proposal, contract=None, prior=()):
    if contract is None:
        validate_candidate(proposal)
        key = digest([project, scope, index, proposal])
        binding = {}
    else:
        agent_contract.validate_proposal(proposal, contract, prior)
        binding = {"contract_digest": digest(contract)}
        key = digest([project, scope, index, proposal, binding])
    return {"project": project, "scope": scope, "candidate": index, "request_key": key,
            "proposal": proposal, **binding}


def check_reading(reading, candidate, contract=None):
    """Check selected quantity, exact original request and producer receipt, independently of response law."""
    expected = {"input_digest": candidate["input_digest"], "request_key": candidate["request_key"],
                "project": candidate["inputs"]["project"], "scope": candidate["inputs"]["scope"],
                "real_solver_executed": False}
    if contract is None:
        expected.update(baseline_digest=digest(BASELINE), backend_kind="FIXTURE", selector=GOAL["selector"],
                        direction=GOAL["direction"], unit=GOAL["unit"])
    else:
        goal = contract["goal"]
        expected.update(contract_digest=digest(contract), metric=goal["metric"],
                        backend_kind=contract["backend"]["kind"], backend_id=contract["backend"]["id"],
                        baseline_digest=contract["baseline_sha256"], selector=goal["selector"],
                        direction=goal["direction"], unit=goal["unit"])
    require(type(reading) is dict and set(reading) == set(expected) | {"value"}
            and all(type(reading[k]) is type(v) and reading[k] == v for k,v in expected.items()),
            "FIXTURE_EVIDENCE_BINDING")
    if contract is not None:
        agent_contract.quantity(reading["value"], contract["goal"]["unit"])
    else:
        require(type(reading["value"]) is str and re.fullmatch(r"[0-9]{1,8}(?:\.[0-9]{1,12})?", reading["value"]),
                "INVALID_OBSERVATION")


def decision_for(candidate, contract=None):
    reading = candidate["receipt"]
    check_reading(reading, candidate, contract)
    value_field = "observed_value" if contract is not None else "observed_mm"
    require(digest(reading) == candidate["evidence_digest"] and candidate[value_field] == reading["value"],
            "FIXTURE_EVIDENCE_BINDING")
    if contract is not None:
        return agent_contract.assess(reading, contract)
    error = abs(Decimal(reading["value"]) - Decimal(GOAL["target_mm"]))
    return {"decision": "WITHIN_TARGET" if error <= Decimal(GOAL["tolerance_mm"]) else "OUTSIDE_TARGET",
            "absolute_error_mm": str(error), "criterion": GOAL, "evidence_digest": digest(reading)}


def _tasks(flow, hub, project, revision, action, payload):
    """Project this transaction into the same native Task Card hub and transition checks."""
    def emit(op, data, suffix):
        event = dict(schema=project_tasks.SCHEMA, project=project, main=flow["scope"], op=op,
                     expected_revision=revision, key=f"fixture.{revision}.{suffix}", data=data)
        project_tasks.apply(hub, event, project, revision, None)
        task_id = data.get("task_id")
        for card in ([hub["cards"][task_id]] if task_id else hub["cards"].values()):
            card["role_contract"]["session_status"] = "LOGICAL_STEP"
            card["host_attestation"] = "UNATTESTED"

    def update(task_id, execution, refs):
        emit("task-update", {"task_id": task_id, "execution": execution, "evidence": refs},
             task_id + execution)

    if action == "START":
        contract = flow.get("contract")
        if contract is None:
            summary = "Enter logical Research Main for scoped displacement fixture"
            task_goals = (
                ("Qualify synthetic model and frozen selectors", "Exactly match the pinned fixture baseline",
                 "Synthetic baseline digest"),
                ("Identify the selected local test instrument", "Record source classification and execution limits",
                 "Fixture capability record"),
            )
            candidate_task = ("Propose bounded F and supply its exact input",
                              "One scalar in N from the authorized baseline")
            validation_task = ("Evaluate returned tip displacement",
                               "Recompute absolute error against the frozen inclusive tolerance")
        else:
            summary = "Enter logical Research Main under the frozen research contract"
            task_goals = (
                ("Bind the operator-declared baseline and model scope",
                 "Record declared identity and qualification limits", "Baseline identity and qualification status"),
                ("Record backend identity and capability status",
                 "Identify the selected service or record it unavailable", "Capability observation and limits"),
            )
            candidate_task = ("Propose " + contract["parameter"]["name"] + " with rationale and prior evidence",
                              "Parameter, bounds, unit and baseline match the frozen contract")
            validation_task = ("Evaluate " + contract["goal"]["metric"] + " at " + contract["goal"]["selector"],
                               "Compare the bound observation with the frozen goal and tolerance")
        drafts = {task: {"goal": goal, "criterion": criterion, "deliverable": deliverable, "refs": []}
                  for task, (goal, criterion, deliverable) in zip(("T01", "T02"), task_goals, strict=True)}
        emit("task-init", {"summary": summary,
                           "drafts": drafts}, "init")
        baseline = contract["baseline_sha256"] if contract else digest(BASELINE)
        for tid, ref, sha in [("T01", "declared-baseline" if contract else "fixture-baseline", baseline),
                              ("T02", "operator-scope", flow["scope"])]:
            update(tid, "IN_PROGRESS", [])
            update(tid, "SUBMITTED", [{"reference": ref, "sha256": sha}])
        for tid, kind, (goal, criterion) in (("T03", "candidate-design", candidate_task),
                                             ("T04", "independent-review", validation_task)):
            emit("task-create", dict(task_id=tid, kind=kind, goal=goal, criterion=criterion,
                                     deps=["T01","T02"], refs=[]), tid)
    elif action == "PROPOSE_CANDIDATE":
        update("T03", "IN_PROGRESS", [])
        update("T03", "SUBMITTED", [{"reference": "candidate-input", "sha256": digest(payload)}])
        if flow["state"] == "BACKEND_UNAVAILABLE":
            update("T04", "BLOCKED", [{"reference": "unconfigured-backend",
                                       "sha256": digest(flow["contract"]["backend"])}])
    elif action == "VALIDATE":
        update("T04", "IN_PROGRESS", [])
        update("T04", "SUBMITTED", [{"reference": "measurement" if flow.get("contract") else "fixture-measurement",
                                     "sha256": payload["evidence_digest"]},
                                    {"reference": "interval-decision", "sha256": digest(payload)}])


def apply(flow, hub, event, project, revision):
    require(set(event) == {"schema","project","scope","max_runs","key","expected_revision",
                           "operation","proposal","action","payload"}
            and event["schema"] in (SCHEMA, agent_contract.EVENT_SCHEMA) and event["project"] == project
            and project_tasks.token(event["key"], r"[A-Za-z0-9._-]{1,96}")
            and event["key"] not in flow["receipts"] and event["key"] not in hub["receipts"]
            and not event["key"].startswith("fixture.")
            and type(event["expected_revision"]) is int and event["expected_revision"] == revision
            and project_tasks.token(event["scope"], "[0-9a-f]{64}")
            and type(event["max_runs"]) is int and 0 <= event["max_runs"] <= 3,
            "FIXTURE_EVENT_CONFLICT")
    action, payload, supplied = event["action"], event["payload"], event["proposal"]
    require(action == ACTIONS[flow["state"]] and action != "STOP"
            and event["operation"] == ("start" if action == "START" else "advance")
            and (supplied is None or action == "PROPOSE_CANDIDATE"), "ILLEGAL_STEP")
    generic = event["schema"] == agent_contract.EVENT_SCHEMA
    if action == "START":
        if generic:
            require(type(payload) is dict and "contract" in payload, "FREEZE_CONFLICT")
            contract = agent_contract.validate_agent_contract(payload["contract"])
            require(payload == {"contract": contract, "stage": "RESEARCH_MAIN", "role_mode": "LOGICAL_STEP",
                                "host_attestation": "UNATTESTED"}, "FREEZE_CONFLICT")
            flow["contract"] = contract
        else:
            require(digest(payload) == digest({"baseline": BASELINE, "goal": GOAL, "host_attestation": "UNATTESTED",
                            "stage": "RESEARCH_MAIN", "role_mode": "LOGICAL_STEP"}), "FREEZE_CONFLICT")
        unavailable = generic and flow["contract"]["backend"]["kind"] == "UNCONFIGURED"
        next_state = "CONTRACT_FROZEN" if generic else "QUALIFIED"
        flow.update(scope=event["scope"], max_runs=event["max_runs"],
                    state=next_state if event["max_runs"] or unavailable else "BUDGET_EXHAUSTED")
    else:
        require(flow["scope"] == event["scope"] and flow["max_runs"] == event["max_runs"], "SCOPE_CONFLICT")
        contract = flow.get("contract")
        require(generic == (contract is not None), "WORKFLOW_VERSION_CONFLICT")
        unavailable = generic and contract["backend"]["kind"] == "UNCONFIGURED"
        if action == "PROPOSE_CANDIDATE":
            require(unavailable or flow["runs_used"] < flow["max_runs"], "BUDGET_EXHAUSTED")
            proposal = rehearsal_proposal(flow) if not generic and supplied is None else supplied
            expected = inputs_for(project, flow["scope"], len(flow["candidates"])+1, proposal,
                                  contract, flow["candidates"])
            require(digest(payload) == digest(expected), "CANDIDATE_MISMATCH")
            scalar = ({"parameter": proposal["parameter"], "value": proposal["value"], "unit": proposal["unit"]}
                      if generic else {"force_N": proposal["force_N"]})
            flow["candidates"].append({"inputs": expected, "input_digest": digest(expected),
                                       "request_key": expected["request_key"], **scalar})
            flow["state"] = "BACKEND_UNAVAILABLE" if unavailable else "CANDIDATE"
        else:
            candidate = flow["candidates"][-1]
            if action == "EXECUTE_FIXTURE_ONCE":
                require(flow["runs_used"] < flow["max_runs"], "BUDGET_EXHAUSTED")
                require(not unavailable, "BACKEND_UNAVAILABLE")
                check_reading(payload, candidate, contract)
                candidate["receipt"] = payload
                flow["runs_used"] += 1
                flow["state"] = "CLAIMED"
            elif action == "QUERY_ORIGINAL_KEY_ONLY":
                require(payload == {"request_key": candidate["request_key"],
                                    "receipt_digest": digest(candidate["receipt"])}, "RECEIPT_MISMATCH")
                candidate["observed_value" if generic else "observed_mm"] = candidate["receipt"]["value"]
                candidate["evidence_digest"] = payload["receipt_digest"]
                flow["state"] = "OBSERVED"
            else:
                require(payload == decision_for(candidate, contract), "DECISION_MISMATCH")
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
