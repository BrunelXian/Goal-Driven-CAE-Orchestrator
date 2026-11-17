"""Fixed in-process test instrument. Only its caller's Core transaction records the effect.

No execution commands, queues, external submissions, model files or physical qualification.
There is no asynchronous acceptance gap with an external execution system.
"""
from decimal import Decimal, ROUND_HALF_UP

from aegiscae.contracts.research_contracts import require
from aegiscae.research.project_tasks import digest

BASELINE = {
    "schema": "scoped-spring-fixture-v1", "backend_kind": "FIXTURE",
    "measurement": "downward-positive", "selector": "fixture-tip",
    "stiffness_N_per_mm": "100", "force_unit": "N", "output_unit": "mm",
    "allowed_parameter": "F", "load_min_N": 1, "load_max_N": 200,
}


GOAL = {"target_mm": "1.0", "tolerance_mm": "0.1", "selector": "fixture-tip",
        "direction": "downward-positive", "unit": "mm"}

def fixture_contract(target="1", tolerance="0.1"):
    """Explicit test adapter configuration for an operator-selected regression case."""
    return {"schema": "agent-research-contract-v1", "baseline_sha256": digest(BASELINE),
            "backend": {"kind": "FIXTURE", "id": BASELINE["schema"]},
            "parameter": {"name": BASELINE["allowed_parameter"], "unit": BASELINE["force_unit"],
                          "min": str(BASELINE["load_min_N"]), "max": str(BASELINE["load_max_N"])},
            "goal": {"metric": "displacement", "direction": BASELINE["measurement"],
                     "selector": BASELINE["selector"], "unit": BASELINE["output_unit"],
                     "target": target, "tolerance": tolerance}}


def check_supported(contract):
    expected = fixture_contract(contract["goal"]["target"], contract["goal"]["tolerance"])
    require(contract["backend"] == expected["backend"] and contract["goal"] == expected["goal"]
            and contract["baseline_sha256"] == expected["baseline_sha256"]
            and contract["parameter"]["name"] == BASELINE["allowed_parameter"]
            and contract["parameter"]["unit"] == BASELINE["force_unit"]
            and BASELINE["load_min_N"] <= Decimal(contract["parameter"]["min"])
            and Decimal(contract["parameter"]["max"]) <= BASELINE["load_max_N"],
            "FIXTURE_CONTRACT_UNSUPPORTED")


def validate_candidate(proposal):
    require(type(proposal) is dict and set(proposal) == {"force_N", "unit", "baseline_digest"},
            "INVALID_CANDIDATE")
    require(proposal["unit"] == "N", "UNIT_MISMATCH")
    require(proposal["baseline_digest"] == digest(BASELINE), "BASELINE_MISMATCH")
    require(type(proposal["force_N"]) is int and 1 <= proposal["force_N"] <= 200,
            "LOAD_OUT_OF_BOUNDS")


def measure(inputs, contract=None):
    """A linear spring surrogate driven solely by its executable input."""
    if contract is None:
        validate_candidate(inputs["proposal"])
        force = Decimal(inputs["proposal"]["force_N"])
    else:
        check_supported(contract)
        require(inputs["contract_digest"] == digest(contract), "FIXTURE_CONTRACT_MISMATCH")
        force = Decimal(inputs["proposal"]["value"])
    mm = force / Decimal(BASELINE["stiffness_N_per_mm"])
    receipt = {"request_key": inputs["request_key"], "input_digest": digest(inputs),
            "project": inputs["project"], "scope": inputs["scope"],
            "baseline_digest": digest(BASELINE), "backend_kind": "FIXTURE",
            "real_solver_executed": False, "selector": BASELINE["selector"],
            "direction": BASELINE["measurement"], "unit": "mm", "value": str(mm)}
    if contract is not None:
        receipt.update(metric=contract["goal"]["metric"], backend_id=contract["backend"]["id"],
                       contract_digest=digest(contract), value=format(mm, "f"))
    return receipt


def rehearsal_proposal(flow):
    force = 50
    if flow["candidates"]:
        previous = flow["candidates"][-1]
        mm = Decimal(previous["observed_mm"])
        require(mm > 0, "INVERSE_UNDEFINED")
        force = int((Decimal(previous["force_N"]) * Decimal("1.0") / mm)
                    .to_integral_value(rounding=ROUND_HALF_UP))
    proposal = {"force_N": force, "unit": "N", "baseline_digest": digest(BASELINE)}
    validate_candidate(proposal)
    return proposal
