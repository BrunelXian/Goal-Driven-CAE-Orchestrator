"""Frozen scalar contract for agent-proposed candidates in a scoped research workflow."""
import re
from copy import deepcopy
from decimal import Decimal, localcontext

from aegiscae.contracts.research_contracts import Quantity, UNITS, require
from aegiscae.research.project_tasks import description, digest
from aegiscae.research.workflow_rules import compare

SCHEMA = "agent-research-contract-v1"
EVENT_SCHEMA = "scoped-agent-workflow-v2"


def _fields(value, required, code):
    require(type(value) is dict and set(value) == set(required), code)


def quantity(value, unit):
    dimension = next((dimension for dimension, units in UNITS.items() if unit in units), None)
    require(dimension is not None, "UNIT_MISMATCH")
    quantity = Quantity(value, dimension, unit)
    quantity.validate()
    # Fixed-point outputs and validation reasons must fit the published decimal envelope.
    require(len(value) <= 48, "DECIMAL_LIMIT")
    return quantity


def _identifier(value):
    require(type(value) is str and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_. -]{0,95}", value),
            "INVALID_CONTRACT_LABEL")


def validate_agent_contract(contract):
    _fields(contract, {"schema","baseline_sha256","backend","parameter","goal"}, "INVALID_AGENT_CONTRACT")
    require(contract["schema"] == SCHEMA and type(contract["baseline_sha256"]) is str
            and re.fullmatch("[a-f0-9]{64}", contract["baseline_sha256"]), "INVALID_AGENT_CONTRACT")
    backend, parameter, goal = contract["backend"], contract["parameter"], contract["goal"]
    _fields(backend, {"kind","id"}, "INVALID_BACKEND")
    require(backend["kind"] in ("FIXTURE", "UNCONFIGURED"), "INVALID_BACKEND")
    _identifier(backend["id"])
    _fields(parameter, {"name","unit","min","max"}, "INVALID_PARAMETER")
    _identifier(parameter["name"])
    require(type(parameter["unit"]) is str, "UNIT_MISMATCH")
    lower = quantity(parameter["min"], parameter["unit"])
    upper = quantity(parameter["max"], parameter["unit"])
    require(Decimal(lower.value) < Decimal(upper.value), "INVALID_PARAMETER_RANGE")
    _fields(goal, {"metric","selector","direction","unit","target","tolerance"}, "INVALID_GOAL")
    for key in ("metric","selector","direction"):
        _identifier(goal[key])
    require(type(goal["unit"]) is str, "UNIT_MISMATCH")
    quantity(goal["target"], goal["unit"])
    tolerance = quantity(goal["tolerance"], goal["unit"])
    tolerance.validate(nonnegative=True)
    if backend["kind"] == "FIXTURE":
        from aegiscae.research.scoped_fixture_port import check_supported
        check_supported(contract)
    return deepcopy(contract)


def validate_proposal(proposal, contract, prior):
    require(proposal is not None, "AGENT_PROPOSAL_REQUIRED")
    _fields(proposal, {"parameter","unit","value","baseline_digest","reason","evidence_refs"},
            "INVALID_AGENT_PROPOSAL")
    parameter = contract["parameter"]
    require(proposal["parameter"] == parameter["name"], "PARAMETER_MISMATCH")
    require(proposal["unit"] == parameter["unit"], "UNIT_MISMATCH")
    require(proposal["baseline_digest"] == contract["baseline_sha256"], "BASELINE_MISMATCH")
    require(type(proposal["value"]) is str and len(proposal["value"]) <= 24, "DECIMAL_LIMIT")
    value = Decimal(quantity(proposal["value"], parameter["unit"]).value)
    require(Decimal(parameter["min"]) <= value <= Decimal(parameter["max"]), "PARAMETER_OUT_OF_BOUNDS")
    require(description(proposal["reason"]), "PROPOSAL_REASON_REQUIRED")
    refs = proposal["evidence_refs"]
    available = {c["evidence_digest"] for c in prior if "evidence_digest" in c}
    require(type(refs) is list and len(refs) <= len(available)
            and all(type(ref) is str and ref in available for ref in refs)
            and len(set(refs)) == len(refs)
            and (not prior or prior[-1].get("evidence_digest") in refs), "PROPOSAL_EVIDENCE_MISMATCH")


def assess(reading, contract):
    goal = contract["goal"]
    observed = quantity(reading["value"], goal["unit"])
    target = quantity(goal["target"], goal["unit"])
    tolerance = quantity(goal["tolerance"], goal["unit"])
    within = compare(observed, "EQ", target, tolerance)
    with localcontext() as context:
        context.prec = 256
        error = abs(Decimal(observed.value) - Decimal(target.value))
    return {"decision": "WITHIN_TARGET" if within else "OUTSIDE_TARGET",
            "absolute_error": str(error),
            "unit": observed.unit, "criterion": goal, "evidence_digest": digest(reading)}
