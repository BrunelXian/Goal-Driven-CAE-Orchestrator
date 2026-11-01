"""New original synthetic DAT/record fixtures, never original Solver evidence."""

import copy

import pytest

from aegiscae.contracts.research_contracts import ContractError, digest_bytes
from aegiscae.research import rod_real_project as real
from aegiscae.research.rod_evidence import af_digest
from aegiscae.research.rod_preview_rules import BASELINE, PROFILE
from aegiscae.research.rod_real_verify import (
    EVENTS, observation_record, validate_observation_record, verify_owner_evidence,
)
from test_d4_real_project import pin
from test_real_rod_preview import synthetic_dat


def fixture_envelope(research):
    state, binding = research.inspect(), pin(research)
    candidate = state["candidates"]["A"]
    metadata = {"profile": PROFILE, "schema": "rod-candidate-v1", "baseline_digest": BASELINE,
        "input_digest": candidate["input_digest"], "load_n": "1", "unit": "N",
        "minimum_n": "0.5", "maximum_n": "2.5", "mutable_entity": {"keyword": "CLOAD", "node": 2, "dof": 1},
        "dimensions": {"length_mm": "10", "area_mm2": "1", "modulus_mpa": "1000"}}
    metadata["candidate_digest"] = af_digest(metadata)
    raw = synthetic_dat()
    return {"schema": "af-rod-owner-evidence-v1", "source": "AF_OWNER_RECORD_CHAIN",
        "source_authentication": "NOT_VERIFIED", "collector_version": "rod-owner-collector-v1",
        "collected_at": 100, "acquired_at": 101, "validation_ref": "fixtureValidation",
        "plan": {"plan_id": binding["plan_id"], "plan_digest": binding["plan_digest"],
            "backend_id": real.BACKEND, "backend_version": 1, "project_id": binding["project_id"],
            "project_instance_id": binding["project_instance_id"], "resources": dict(real.RESOURCES),
            "output_key": binding["output_identity"], "validation_policy": "axial-rod-owner-dat-v1",
            "rod_contract": {"research_project_id": state["research_project_id"],
                "contract_digest": state["contract_digest"], "research_revision": 3,
                "candidate_id": candidate["candidate_id"], "request_nonce": binding["request_nonce"],
                "phase": "A", "candidate": metadata}},
        "receipt": {"request_id": "fixtureReceipt", "request_digest": digest_bytes(b"fixtureRequest"),
            "idempotency_key": binding["request_key"], "run_id": "fixtureRun", "accepted_sequence": 11},
        "run": {"run_id": "fixtureRun", "project_id": binding["project_id"],
            "project_instance_id": binding["project_instance_id"], "plan_id": binding["plan_id"],
            "plan_digest": binding["plan_digest"], "grant_id": "fixtureGrantDeclarationOnly",
            "phase_attempt_id": "fixtureAttempt", "phase": "STANDARD_ANALYSIS", "revision": 9,
            "simulation": False, "execution": "FINISHED", "backend_outcome": "COMPLETED",
            "reconciliation": "NONE", "managed_completion": "COMMITTED_EMPTY_SCOPE"},
        "events": [{"type": kind, "project_sequence": i + 11, "run_sequence": i + 1, "run_id": "fixtureRun"}
                   for i, kind in enumerate(EVENTS)],
        "artifact": {"logical_ref": "output:dat", "dat_bytes": raw, "sha256": digest_bytes(raw),
            "size": len(raw), "input_digest": candidate["input_digest"], "step": 1, "increment": 1,
            "units": {"length": "mm", "force": "N", "stress": "MPa"}},
        "V2": "NOT_VERIFIED", "V3": "INCONCLUSIVE", "V4": "NOT_ASSESSED", "ODB": "NOT_VERIFIED"}


@pytest.fixture
def case(tmp_path):
    research = real.create_real_research(tmp_path / "new-owner-read-fixture", "D4 synthetic owner envelope")
    return research, fixture_envelope(research)


def check(case, envelope=None):
    research, raw = case
    return verify_owner_evidence(envelope or raw, research.inspect()["candidates"]["A"], pin(research))


def test_original_revision_and_extra_events_not_fixture_revision_three(case):
    research, raw = case
    result = check(case)
    assert result["numerical_bytes_check"] == "PASS"
    assert result["metrics"]["displacement_mm"] == "0.01"
    assert result["V2"] == "NOT_VERIFIED" and result["V3"] == "INCONCLUSIVE"
    assert not result["execution_authorized"]
    raw["events"].append({"type": "OBSERVATION_RECORDED", "project_sequence": 25,
                          "run_sequence": 7, "run_id": raw["run"]["run_id"]})
    raw["run"]["revision"] = 17
    assert check(case)["V2"] == "NOT_VERIFIED"
    assert set(research.inspect()["candidates"]) == {"A"}


@pytest.mark.parametrize("section,key,value", [
    (None, "source_authentication", "PASS"), (None, "V2", "PASS"),
    (None, "V3", "SATISFIED"), (None, "source", "FAKE_TEST_ONLY"),
    (None, "collector_version", "caller-supplied"), (None, "collected_at", 102),
    ("plan", "plan_digest", digest_bytes(b"other")), ("plan", "output_key", digest_bytes(b"old")),
    ("run", "project_id", "otherProject"), ("run", "revision", True),
    ("run", "phase", "STANDARD"), ("run", "simulation", True),
    ("run", "execution", "UNKNOWN"), ("run", "managed_completion", "UNKNOWN"),
    ("receipt", "idempotency_key", "otherRequest"), ("receipt", "run_id", "otherRun"),
    ("receipt", "accepted_sequence", 1), ("artifact", "input_digest", digest_bytes(b"other")),
    ("artifact", "step", 2), ("artifact", "increment", True),
    ("artifact", "units", {"length": "m", "force": "N", "stress": "Pa"}),
])
def test_wrong_source_identity_and_status_rejected(case, section, key, value):
    _, raw = case
    target = raw if section is None else raw[section]
    target[key] = value
    with pytest.raises(ContractError):
        check(case)


@pytest.mark.parametrize("change", ["duplicate", "reorder", "wrong_run", "gap", "missing"])
def test_original_history_causal_rejections(case, change):
    _, raw = case
    if change == "duplicate":
        raw["events"][2]["type"] = raw["events"][0]["type"]
    elif change == "reorder":
        raw["events"][1]["type"], raw["events"][2]["type"] = raw["events"][2]["type"], raw["events"][1]["type"]
    elif change == "wrong_run":
        raw["events"][1]["run_id"] = "oldRun"
    elif change == "gap":
        raw["events"][1]["run_sequence"] = 3
    else:
        raw["events"].pop()
    with pytest.raises(ContractError):
        check(case)


@pytest.mark.parametrize("change", ["truncated", "nan", "wrong_node", "wrong_step", "wrong_numeric", "duplicate_page", "bad_cp936"])
def test_dat_parser_independently_rejects_bad_bytes_even_with_matching_hash(case, change):
    _, raw = case
    body = raw["artifact"]["dat_bytes"]
    if change == "truncated":
        body = body[:len(body) // 2]
    elif change == "nan":
        body = body.replace(b"2 0.01 0 0", b"2 NaN 0 0")
    elif change == "wrong_node":
        body = body.replace(b"2 0.01 0 0", b"3 0.01 0 0")
    elif change == "wrong_step":
        body = body.replace(b"STEP 1 INCREMENT", b"STEP 2 INCREMENT")
    elif change == "wrong_numeric":
        body = body.replace(b"2 0.01 0 0", b"2 0.02 0 0")
    elif change == "duplicate_page":
        body += b"\fR010 axial bar a19d17ea - N mm MPa STEP 1 INCREMENT 1\n"
    else:
        body = b"\x81\x30" + body
    raw["artifact"].update(dat_bytes=body, sha256=digest_bytes(body), size=len(body))
    with pytest.raises(ContractError):
        check(case)


def test_cp936_date_and_valid_formfeed_do_not_change_numerics(case):
    _, raw = case
    body = raw["artifact"]["dat_bytes"].replace(b"30-Oct-2026", "30-10月-2026".encode("cp936"))
    body = body.replace(b"NODE FOOT- U1", b"\fNODE FOOT- U1")
    raw["artifact"].update(dat_bytes=body, sha256=digest_bytes(body), size=len(body))
    assert check(case)["metrics"]["displacement_mm"] == "0.01"


def test_bound_public_read_persists_unverified_evidence_and_holds_budget(case):
    research, raw = case
    class Port:
        def read_real_artifact(self, **kwargs):
            assert kwargs == {"plan_id": pin(research)["plan_id"],
                "expected_plan_digest": pin(research)["plan_digest"], "request_key": pin(research)["request_key"]}
            return copy.deepcopy(raw)
    research.reserve_a(pin(research), 3, "reserve_A")
    research.record_intent_a(4, "intent_A")
    state = research.observe_a(Port(), 5, "observe_A")
    assert state["budget"]["held"] == 1 and state["budget"]["charged"] == 0
    assert state["observations"]["A"]["independent"]["V2"] == "NOT_VERIFIED"
    assert state["reservations"]["A"]["state"] == "ACCEPTANCE_UNKNOWN"
    class NoReadAllowed:
        def read_real_artifact(self, **kwargs):
            raise AssertionError("Idempotent replay must not reacquire")
    assert research.observe_a(NoReadAllowed(), 5, "observe_A")["replayed"]
    with pytest.raises(ContractError, match="AUTHENTICATED_REAL_A_REQUIRED"):
        research.propose_b({"load_n": "2", "native_role": "gdcae-inverse"}, 6, "B")


def test_forged_persisted_independent_review_rejected(case):
    research, raw = case
    candidate, binding = research.inspect()["candidates"]["A"], pin(research)
    record = observation_record(raw, candidate, binding)
    record["independent"]["V2"] = "PASS"
    with pytest.raises(ContractError, match="OWNER_REVIEW_FORGED"):
        validate_observation_record(record, candidate, binding)
