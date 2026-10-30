"""Original synthetic bytes only; deterministic validation is not real V2."""

import copy

import pytest

from aegiscae.contracts.research_contracts import ContractError
from aegiscae.research.rod_evidence import SELECTOR, UNITS, validate_real_source_contract
from test_g2_rod_core import bridge, envelope, fake_evidence, intent, observe, prepare_a
from test_real_rod_preview import synthetic_dat
from test_g2_rod_core import sha

__all__ = ["bridge"]


@pytest.mark.parametrize("form", ["ascii", "cp936", "formfeed", "scientific"])
def test_bounded_applicable_layouts(bridge, form):
    prepare_a(bridge)
    intent(bridge)
    data = synthetic_dat()
    if form == "cp936":
        data = data.replace(b"30-Oct-2026", "30-10月-2026".encode("cp936"))
    elif form == "formfeed":
        data = data.replace(b"\n\nTHE FOLLOWING", b"\n\f\nTHE FOLLOWING")
    elif form == "scientific":
        data = data.replace(b"2 0.01 0 0", b"2 1.0D-2 0 0")
    final = observe(bridge, data=data)
    decision = final["attempts"]["A"]["decision"]
    assert decision["V2"] == "NOT_VERIFIED" and decision["fixture_checks"]["numerical"] == "PASS"


@pytest.mark.parametrize("before,after", [
    (b"2 0.01 0 0", b"2 NaN 0 0"), (b"2 0.01 0 0", b"2 Infinity 0 0"),
    (b"2 0.01 0 0", b"3 0.01 0 0"), (b"N mm MPa", b"N m Pa"),
    (b"STEP 1 INCREMENT 1", b"STEP 2 INCREMENT 1"), (b"1 1 1", b"1 2 1"),
    (b"NODE FOOT- U1 U2 U3", b"NODE FOOT- U1 U2 U3\nNODE FOOT- U1 U2 U3"),
    (b"WALLCLOCK TIME (SEC) = 1", b""), (b"1 -1 0 0", b"1 1 0 0")])
def test_numerical_and_format_negatives(bridge, before, after):
    prepare_a(bridge)
    intent(bridge)
    with pytest.raises(ContractError):
        observe(bridge, data=synthetic_dat().replace(before, after))
    assert bridge.inspect()["pending_or_unknown"]


@pytest.mark.parametrize("field,value", [("source", "AF_REAL"), ("real_solver_executed", True),
    ("real_solver_status", "COMPLETED"), ("execution_link", None)])
def test_envelope_cannot_upgrade_source(bridge, field, value):
    prepare_a(bridge)
    intent(bridge)
    raw = envelope(bridge)
    raw[field] = value
    with pytest.raises(ContractError):
        bridge.observe("A", fake_evidence(), raw, 5, "bad")


@pytest.mark.parametrize("field,value", [("filename", "../old.dat"), ("stable_read", False),
    ("size", True), ("units", {"displacement": "m", "stress": "Pa", "reaction": "N"}),
    ("selector", {"step": 1, "increment": 2, "node": 2, "dof": 1, "element": 1, "integration_point": 1})])
def test_artifact_scope_and_identity_negatives(bridge, field, value):
    prepare_a(bridge)
    intent(bridge)
    raw = envelope(bridge)
    raw["artifact"][field] = value
    with pytest.raises(ContractError):
        bridge.observe("A", fake_evidence(), raw, 5, "bad")


def real_schema_fixture():
    return {"schema": "af-real-rod-source-contract-v1", "source": "TEST_ONLY_REAL_SCHEMA_FIXTURE",
        "profile": "axial_rod_cload_v1", "backend_id": "abaqus-standard-rod-preview-v1",
        "project_id": "schema_project", "project_instance_id": "schema_instance",
        "plan_id": "schema_plan", "plan_digest": sha("schema_plan"),
        "candidate_id": "schema_candidate", "input_digest": sha("schema_input"),
        "grant_id": "schema_grant", "receipt_id": "schema_receipt", "run_id": "schema_run",
        "phase_attempt_id": "schema_attempt", "phase": "A", "resources_digest": sha("schema_resources"),
        "output_identity": sha("schema_output"), "output_digest": sha("schema_bytes"), "output_size": 1024,
        "verification_policy_digest": sha("schema_policy"), "selector": dict(SELECTOR), "units": dict(UNITS),
        "solver_exit_code": 0, "execution": "FINISHED", "reconciliation": "NONE",
        "managed_scope": "COMMITTED_EMPTY_SCOPE", "stable_read": True}


@pytest.mark.parametrize("source", ["TEST_ONLY_REAL_SCHEMA_FIXTURE", "AF_REAL_DECLARATION"])
def test_real_schema_consistency_does_not_authenticate_source(source):
    record = real_schema_fixture()
    record["source"] = source
    result = validate_real_source_contract(record, copy.deepcopy(record))
    assert result["schema_valid"] and result["V2"] == "NOT_VERIFIED"
    assert result["live_read_enabled"] is False and result["execution_authorized"] is False


@pytest.mark.parametrize("field,value", [("source", "SYNTHETIC_DAT"), ("solver_exit_code", True),
    ("solver_exit_code", 1), ("output_size", True), ("output_size", 1048577),
    ("execution", "UNKNOWN"), ("reconciliation", "UNKNOWN"), ("managed_scope", "UNKNOWN"),
    ("stable_read", False), ("backend_id", "fake-v1"), ("input_digest", "not-a-digest"),
    ("selector", {**SELECTOR, "step": True}), ("units", {**UNITS, "displacement": "m"})])
def test_real_schema_negative_even_when_caller_pins_same_bad_values(field, value):
    record = real_schema_fixture()
    record[field] = value
    with pytest.raises(ContractError):
        validate_real_source_contract(record, copy.deepcopy(record))


@pytest.mark.parametrize("field", ["project_id", "project_instance_id", "plan_digest", "input_digest",
                                  "grant_id", "receipt_id", "run_id", "output_digest"])
def test_real_schema_identity_substitution(field):
    expected = real_schema_fixture()
    record = copy.deepcopy(expected)
    record[field] = sha("substitution") if "digest" in field else "substituted_identity"
    with pytest.raises(ContractError, match="REAL_BINDING_MISMATCH"):
        validate_real_source_contract(record, expected)


def test_replacement_after_read_is_detected(bridge):
    prepare_a(bridge)
    intent(bridge)
    raw = copy.deepcopy(envelope(bridge))
    raw["dat_bytes"] += b"replacement"
    with pytest.raises(ContractError, match="EVIDENCE_BYTES_MISMATCH"):
        bridge.observe("A", fake_evidence(), raw, 5, "bad")
