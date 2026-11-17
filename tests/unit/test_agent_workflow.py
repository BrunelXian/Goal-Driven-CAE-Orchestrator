"""Agent-proposal mode exercises the common project ledger without any solver calls."""
from copy import deepcopy
from decimal import Decimal, localcontext

import pytest

from aegiscae.contracts.research_contracts import ContractError
from aegiscae.research import agent_contract, project_tasks, scoped_fixture, workflow
from aegiscae.research.project import create_research_project, open_agreement_project
from aegiscae.research.scoped_fixture_port import fixture_contract

SCOPE = "a" * 64


@pytest.fixture
def research(tmp_path):
    root = tmp_path / "research"
    create_research_project(root, "Explicit research proposal", research_agreements=True)
    return open_agreement_project(root, write=True)


def pressure_contract():
    return {"schema": "agent-research-contract-v1", "baseline_sha256": "b" * 64,
            "backend": {"kind": "UNCONFIGURED", "id": "local-unconfigured"},
            "parameter": {"name": "dwell", "min": "0.5", "max": "12", "unit": "s"},
            "goal": {"metric": "pressure", "selector": "probe-3", "direction": "compression",
                     "target": "20", "tolerance": "0.5", "unit": "MPa"}}


def proposed(contract, value, evidence=()):
    return {"parameter": contract["parameter"]["name"], "unit": contract["parameter"]["unit"],
            "baseline_digest": contract["baseline_sha256"], "value": value,
            "reason": "Operator-declared test observation and bounded proposal.",
            "evidence_refs": list(evidence)}


def test_contract_is_not_a_fixture_or_model_qualification(research):
    contract = pressure_contract()
    assert workflow.validate_agent_contract(contract) == contract
    started = workflow.agent_start(research, SCOPE, 0, 1, "start", contract=contract)
    assert started["state"] == "CONTRACT_FROZEN" and started["next_action"] == "PROPOSE_CANDIDATE"
    assert started["model_qualification"] == "DECLARED_IDENTITY_ONLY"
    assert started["contract"] == contract and started["goal"]["unit"] == "MPa"
    with pytest.raises(ContractError, match="AGENT_PROPOSAL_REQUIRED"):
        workflow.agent_advance(research, SCOPE, 0, 2, "missing", contract=contract)
    assert started == workflow.agent_status(research, SCOPE, 0, contract=contract)
    with pytest.raises(ContractError, match="CONTRACT_MISMATCH"):
        scoped_fixture.advance(research, SCOPE, 0, 2, "legacy")
    p = proposed(contract, "3.5")
    admitted = workflow.agent_advance(research, SCOPE, 0, 2, "agent-proposal", p, contract=contract)
    assert admitted["state"] == "BACKEND_UNAVAILABLE"
    assert (admitted["real_solver_executed"], admitted["runs_used"]) == (False, 0)
    assert admitted["candidates"][0]["inputs"]["proposal"] == p
    assert "receipt" not in admitted["candidates"][0]
    reopened = open_agreement_project(research._root, write=True)
    assert workflow.agent_status(reopened, SCOPE, 0, contract=contract) == admitted
    assert workflow.agent_start(reopened, SCOPE, 0, 1, "start", contract=contract) == started
    assert workflow.agent_advance(reopened, SCOPE, 0, 2, "agent-proposal", p, contract=contract) == admitted
    tasks = project_tasks.view(reopened)["tasks"]
    assert next(t for t in tasks if t["task_id"] == "T03")["execution"] == "SUBMITTED"
    assert next(t for t in tasks if t["task_id"] == "T04")["execution"] == "BLOCKED"
    assert "dwell" in next(t for t in tasks if t["task_id"] == "T03")["goal"]
    with pytest.raises(ContractError, match="ILLEGAL_STEP"):
        workflow.agent_advance(reopened, SCOPE, 0, 3, "run", contract=contract)


def test_explicit_fixture_adapter_rejects_incompatible_bindings_and_proposals(research):
    contract = fixture_contract(target="1.25", tolerance="0.03")
    for keys, replacement in [(("backend", "id"), "other"), (("goal", "selector"), "old-tip"),
                              (("parameter", "name"), "dwell"), (("parameter", "max"), "1000")]:
        invalid = deepcopy(contract)
        invalid[keys[0]][keys[1]] = replacement
        with pytest.raises(ContractError, match="FIXTURE_CONTRACT_UNSUPPORTED"):
            workflow.validate_agent_contract(invalid)
    started = workflow.agent_start(research, SCOPE, 3, 1, "start", contract=contract)
    p = proposed(contract, "71")
    for changes, reason in [({"value": "201"}, "PARAMETER_OUT_OF_BOUNDS"),
                            ({"reason": " "}, "PROPOSAL_REASON_REQUIRED"),
                            ({"unit": "mm"}, "UNIT_MISMATCH"),
                            ({"evidence_refs": ["1" * 64]}, "PROPOSAL_EVIDENCE_MISMATCH"),
                            ({"parameter": "material"}, "PARAMETER_MISMATCH"),
                            ({"baseline_digest": "1" * 64}, "BASELINE_MISMATCH")]:
        with pytest.raises(ContractError, match=reason):
            workflow.agent_advance(research, SCOPE, 3, 2, "proposal", p | changes, contract=contract)
    with pytest.raises(ContractError, match="AGENT_PROPOSAL_REQUIRED"):
        workflow.agent_advance(research, SCOPE, 3, 2, "proposal", contract=contract)
    assert workflow.agent_status(research, SCOPE, 3, contract=contract) == started
    admitted = workflow.agent_advance(research, SCOPE, 3, 2, "proposal", p, contract=contract)
    assert admitted["candidates"][0]["value"] == "71"
    assert admitted["runs_used"] == 0 and admitted["next_action"] == "EXECUTE_FIXTURE_ONCE"
    with pytest.raises(ContractError, match="CONTRACT_MISMATCH"):
        workflow.agent_status(research, SCOPE, 3, contract=fixture_contract())


def test_feedback_must_cite_current_bound_observation():
    contract = fixture_contract()
    prior = [{"evidence_digest": "1" * 64}, {"evidence_digest": "2" * 64}]
    for refs in ([], ["1" * 64], ["e" * 64]):
        with pytest.raises(ContractError, match="PROPOSAL_EVIDENCE_MISMATCH"):
            agent_contract.validate_proposal(proposed(contract, "103", refs), contract, prior)
    agent_contract.validate_proposal(proposed(contract, "103", ["2" * 64]), contract, prior)


def test_comparison_and_reason_ignore_ambient_decimal_precision():
    contract = pressure_contract()
    contract["goal"].update(target="2", tolerance="0.999999999999999999999999999999999999")
    reading = {"value": "1.000000000000000000000000000000000009"}
    with localcontext() as context:
        context.prec = 4
        result = agent_contract.assess(reading, contract)
    assert result["decision"] == "WITHIN_TARGET"
    assert Decimal(result["absolute_error"]) == Decimal("0.999999999999999999999999999999999991")
