"""Fixed in-process test instrument. Only its caller's Core transaction records the effect.

No execution commands, queues, external submissions, model files or physical qualification.
There is no asynchronous acceptance gap with an external execution system.
"""
from decimal import Decimal

from aegiscae.contracts.research_contracts import require
from aegiscae.research.task_cards import digest

BASELINE = {
    "schema": "scoped-spring-fixture-v1", "backend_kind": "FIXTURE",
    "measurement": "downward-positive", "selector": "fixture-tip",
    "stiffness_N_per_mm": "100", "force_unit": "N", "output_unit": "mm",
    "allowed_parameter": "F", "load_min_N": 1, "load_max_N": 200,
}


def validate_candidate(proposal):
    require(type(proposal) is dict and set(proposal) == {"force_N", "unit", "baseline_digest"},
            "INVALID_CANDIDATE")
    require(proposal["unit"] == "N", "UNIT_MISMATCH")
    require(proposal["baseline_digest"] == digest(BASELINE), "BASELINE_MISMATCH")
    require(type(proposal["force_N"]) is int and 1 <= proposal["force_N"] <= 200,
            "LOAD_OUT_OF_BOUNDS")


def measure(inputs):
    """A linear spring surrogate driven solely by its executable input."""
    validate_candidate(inputs["proposal"])
    mm = Decimal(inputs["proposal"]["force_N"]) / Decimal(BASELINE["stiffness_N_per_mm"])
    return {"request_key": inputs["request_key"], "input_digest": digest(inputs),
            "project": inputs["project"], "scope": inputs["scope"],
            "baseline_digest": digest(BASELINE), "backend_kind": "FIXTURE",
            "real_solver_executed": False, "selector": BASELINE["selector"],
            "direction": BASELINE["measurement"], "unit": "mm", "value": str(mm)}
