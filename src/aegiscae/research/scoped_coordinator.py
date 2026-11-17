"""Authoritative, transactional coordination of scoped Research Main workflow steps."""
from copy import deepcopy

from aegiscae.contracts.research_contracts import require
from aegiscae.research import scoped_fixture_port as instrument
from aegiscae.research import scoped_fixture_rules as rules
from aegiscae.research import agent_contract, project_tasks
from aegiscae.research.project import _commit_workflow_event


def _view(flow, project, max_runs, revision, contract=None):
    contract = flow.get("contract", contract)
    result = {"project": project, "revision": revision, "state": flow["state"],
            "next_action": rules.ACTIONS[flow["state"]], "candidates": deepcopy(flow["candidates"]),
            "runs_used": flow["runs_used"], "max_runs": max_runs,
            "real_solver_executed": False, "host_attestation": "UNATTESTED",
            "role_mode": "LOGICAL_STEP", "stage": "SETUP" if flow["state"] == "NEW" else "RESEARCH_MAIN"}
    if contract is None:
        result.update(backend_kind="FIXTURE", goal=dict(instrument.GOAL),
                      baseline_digest=rules.digest(instrument.BASELINE))
    else:
        result.update(contract=deepcopy(contract), contract_digest=rules.digest(contract),
                      backend_kind=contract["backend"]["kind"], backend_id=contract["backend"]["id"],
                      goal=dict(contract["goal"]), baseline_digest=contract["baseline_sha256"],
                      proposal_policy="EXPLICIT_AGENT_PROPOSAL",
                      model_qualification=("SYNTHETIC_TEST_ONLY" if contract["backend"]["kind"] == "FIXTURE"
                                           else "DECLARED_IDENTITY_ONLY"))
    return result


def _check(scope, max_runs, flow, contract=None):
    if contract is not None:
        agent_contract.validate_agent_contract(contract)
    require(flow["state"] == "NEW" or contract == flow.get("contract"), "CONTRACT_MISMATCH")
    require(project_tasks.token(scope, "[0-9a-f]{64}") and type(max_runs) is int
            and 0 <= max_runs <= 3, "INVALID_SCOPE")
    require(flow["scope"] is None or (flow["scope"] == scope and flow["max_runs"] == max_runs),
            "SCOPE_CONFLICT")


def status(project, scope_id, max_runs, request_key=None, *, contract=None):
    state = {}
    with project._snapshot(agreement_state=state) as (_, meta, _, _):
        flow = state.get("scoped_fixture", rules.initial())
        _check(scope_id, max_runs, flow, contract)
        view = _view(flow, project.research_project_id, max_runs, meta["project_revision"], contract)
        if request_key is not None:
            require(project_tasks.token(request_key, r"[A-Za-z0-9._-]{1,96}"), "INVALID_KEY")
            receipt = flow["receipts"].get(request_key)
            view["request_receipt"] = None if receipt is None else {
                "key": request_key, "proposal_digest": rules.digest(receipt["proposal"]), **receipt}
        return view


def _payload(flow, project, scope, action, proposal, contract=None):
    if action == "START":
        if contract is not None:
            return {"contract": contract, "stage": "RESEARCH_MAIN", "role_mode": "LOGICAL_STEP",
                    "host_attestation": "UNATTESTED"}
        return {"baseline": instrument.BASELINE, "goal": instrument.GOAL, "stage": "RESEARCH_MAIN",
                "role_mode": "LOGICAL_STEP", "host_attestation": "UNATTESTED"}
    if action == "PROPOSE_CANDIDATE":
        if contract is None and proposal is None:
            proposal = instrument.rehearsal_proposal(flow)
        return rules.inputs_for(project, scope, len(flow["candidates"])+1, proposal, contract,
                                flow["candidates"])
    candidate = flow["candidates"][-1]
    if action == "EXECUTE_FIXTURE_ONCE":
        return instrument.measure(candidate["inputs"], contract)
    if action == "QUERY_ORIGINAL_KEY_ONLY":
        return {"request_key": candidate["request_key"], "receipt_digest": rules.digest(candidate["receipt"])}
    return rules.decision_for(candidate, contract)


def _prior_view(events, revision, project_id, max_runs):
    # Rebuild the exact response at the original committed revision, even after later writes.
    flow, hub = rules.initial(), project_tasks.empty()
    for entry in events:
        if entry["project_revision"] > revision:
            break
        event = entry.get("workflow", {})
        if event.get("schema") in (rules.SCHEMA, agent_contract.EVENT_SCHEMA):
            rules.apply(flow, hub, event, project_id, entry["project_revision"] - 1)
    return _view(flow, project_id, max_runs, revision)


def _record(project, scope, max_runs, revision, key, operation, proposal, contract=None):
    require(project_tasks.token(key, r"[A-Za-z0-9._-]{1,96}") and not key.startswith("fixture."),
            "INVALID_KEY")
    require(type(revision) is int and 1 <= revision <= 1024, "INVALID_REVISION")
    state = {}
    project_id = project.research_project_id
    with project._snapshot(write=True, agreement_state=state) as (conn, meta, bundles, events):
        require(not bundles, "SCOPED_CONTRACT_CONFLICT" if contract is not None else "FIXTURE_REQUIRES_ISOLATED_PROJECT")
        flow = state.setdefault("scoped_fixture", rules.initial())
        hub = state.setdefault("task_hub", project_tasks.empty())
        _check(scope, max_runs, flow, contract)
        existing = flow["receipts"].get(key)
        if existing is not None:
            requested = {"operation": operation, "proposal": proposal, "expected_revision": revision,
                         "revision": revision + 1}
            require(rules.digest(existing) == rules.digest(requested), "REQUEST_KEY_CONFLICT")
            return _prior_view(events, existing["revision"], project_id, max_runs)
        require(key not in hub["receipts"], "REQUEST_KEY_CONFLICT")
        require(meta["project_revision"] == revision, "REVISION_CONFLICT")
        action = rules.ACTIONS[flow["state"]]
        require(action != "STOP" and operation == ("start" if action == "START" else "advance")
                and (proposal is None or action == "PROPOSE_CANDIDATE"), "ILLEGAL_STEP")
        if action == "EXECUTE_FIXTURE_ONCE":
            require(flow["runs_used"] < max_runs, "BUDGET_EXHAUSTED")
        schema = rules.SCHEMA if contract is None else agent_contract.EVENT_SCHEMA
        event = dict(schema=schema, project=project_id, scope=scope, max_runs=max_runs,
                     key=key, expected_revision=revision, operation=operation, proposal=proposal,
                     action=action, payload=_payload(flow, project_id, scope, action, proposal, contract))
        rules.apply(flow, hub, event, project_id, revision)
        _commit_workflow_event(conn, meta, None, event)
        conn.commit()
        return _view(flow, project_id, max_runs, meta["project_revision"])


def start(project, scope_id, max_runs, expected_revision, key, *, contract=None):
    return _record(project, scope_id, max_runs, expected_revision, key, "start", None, contract)


def advance(project, scope_id, max_runs, expected_revision, key, proposal=None, *, contract=None):
    return _record(project, scope_id, max_runs, expected_revision, key, "advance", proposal, contract)
