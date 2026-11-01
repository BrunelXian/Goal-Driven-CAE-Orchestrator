"""Pre-A qualification uses new synthetic files, never a Solver or real Grant."""

import copy
from dataclasses import asdict

import pytest

from aegiscae.contracts.research_contracts import ContractError, digest_bytes
from aegiscae.research import project as store, rod_real_project as real
from aegiscae.research.rod_real_verify import (
    READ_LIMITS, observation_record, validate_observation_record, verify_owner_evidence,
)
from test_d4_real_project import pin
from test_d4_real_verify import fixture_envelope


@pytest.fixture
def research(tmp_path):
    return real.create_real_research(tmp_path / "d5-synthetic-preflight", "D5 synthetic preflight")


def test_dossier_is_readonly_and_separates_future_output_from_pre_a_requirements(research):
    path = research.project._root / "research.sqlite3"
    before = path.read_bytes()
    reopened = real.RealRodProject(store.open_existing_readonly(research.project._root))
    report = reopened.pre_a_dossier()
    assert report["status"] == "NOT_EXECUTABLE" and not report["execution_authorized"]
    assert report["input_compliance"] == "FROZEN_TEMPLATE_CHECKED"
    assert report["scientific_contract"]["proposed_a_n"] == "1"
    assert report["scientific_contract"]["goal_min_mm"] == "0.019"
    assert report["candidate_a"]["input_digest"] == digest_bytes(research.candidate_input())
    assert report["read_limits"] == READ_LIMITS
    assert "SOURCE_ACQUISITION_MECHANISM_QUALIFICATION" in report["pre_execution_prerequisites"]
    assert "THIS_A_ORIGINAL_DAT_STA_MSG" not in report["pre_execution_prerequisites"]
    assert "THIS_A_ORIGINAL_DAT_STA_MSG" in report["post_execution_requirements"]
    assert report["real_a_output"] == "NOT_AVAILABLE_TO_PROJECT"
    assert report["budget"] == {"limit": 2, "held": 0, "charged": 0, "available": 2}
    assert report["budget_scope"] == "RESEARCH_PROJECT_ONLY"
    assert report["campaign_budget_enforcement"] == "NOT_QUALIFIED"
    assert report["b_state"] == "NO_CANDIDATE_PLAN_OR_GRANT"
    report["candidate_a"]["load_n"] = "2"
    assert research.inspect()["candidates"]["A"]["load_n"] == "1"
    assert path.read_bytes() == before


def test_unknown_preflight_demands_query_first_and_does_not_release_or_retry(research):
    research.reserve_a(pin(research), 3, "reserve_A")
    research.record_intent_a(4, "intent_A")
    research.mark_unknown_a(5, "unknown_A")
    report = research.pre_a_dossier()
    assert report["query_first_required"] is True
    assert report["reservation_state"] == "ACCEPTANCE_UNKNOWN"
    assert report["budget"]["held"] == 1 and report["budget"]["available"] == 1
    before = research.inspect()
    with pytest.raises(ContractError, match="REAL_ATTEMPT_ALREADY_RESERVED"):
        research.reserve_a(pin(research), 6, "replacement_key")
    with pytest.raises(ContractError, match="AUTHENTICATED_REAL_A_REQUIRED"):
        research.propose_b({"approved": True, "reviewer": "PASS"}, 6, "forged_success")
    assert research.inspect() == before


@pytest.mark.parametrize("section,field,value", [
    ("model", "material_assumptions", ["Elastic E 2000 MPa"]),
    ("model", "boundary_assumptions", ["Node 2 free transverse DOFs"]),
    ("model", "integration_assumptions", ["Two T3D2 elements"]),
    ("model", "force_unit", "kN"),
    ("goal", "tolerance", {"value": "0.01", "dimension": "length", "unit": "mm"}),
    ("verification", "goal_tolerance", {"value": "0.01", "dimension": "length", "unit": "mm"}),
])
def test_rehashed_model_or_tolerance_change_cannot_become_frozen_real_route(research, section, field, value):
    bundle = real.real_bundle(research.inspect()["research_project_id"])
    changed = copy.deepcopy(asdict(bundle))
    changed[section][field] = value
    event = {"schema_version": real.VERSION, "action": "INITIALIZE", "key": "altered_contract",
             "before_project_revision": 2, "data": {"verification_policy": real.NUMERICAL_POLICY}}
    with pytest.raises(ContractError) as error:
        altered = type(bundle).from_dict(changed)
        real.apply_real_workflow(None, event, altered, 2, altered.digests()["bundle"])
    assert error.value.code in {"REAL_FROZEN_CONTRACT_MISMATCH", "INVALID_CONTRACT",
                                "VERIFICATION_TOLERANCE_MISMATCH"}
    assert research.inspect()["project_revision"] == 3


@pytest.mark.parametrize("field,value", [
    ("backend_id", "fake-v1"),
    ("candidate_output_identity", digest_bytes(b"other-research-candidate-output")),
    ("input_digest", digest_bytes(b"other-input")),
    ("resources_digest", digest_bytes(b"other-resources")),
    ("plan_id", "../escape"),
])
def test_pure_verifier_independently_rejects_wrong_expected_binding(research, field, value):
    binding = pin(research)
    binding[field] = value
    with pytest.raises(ContractError):
        verify_owner_evidence(fixture_envelope(research), research.inspect()["candidates"]["A"], binding)


def test_same_model_bytes_cannot_substitute_other_research_project_envelope(research, tmp_path):
    other = real.create_real_research(tmp_path / "distinct-project", "Distinct synthetic project")
    assert other.candidate_input() == research.candidate_input()
    with pytest.raises(ContractError, match="OWNER_RESEARCH_MISMATCH"):
        verify_owner_evidence(fixture_envelope(other), research.inspect()["candidates"]["A"], pin(research))
    assert research.inspect()["budget"]["held"] == other.inspect()["budget"]["held"] == 0


def test_unavailable_read_port_does_not_change_budget_revision_or_b(research):
    research.reserve_a(pin(research), 3, "reserve_A")
    research.record_intent_a(4, "intent_A")
    research.mark_unknown_a(5, "unknown_A")
    before = research.inspect()
    class Unavailable:
        def read_real_artifact(self, **_kwargs):
            raise RuntimeError("TEST_ONLY_NO_ORIGINAL_OUTPUT")
    with pytest.raises(RuntimeError, match="TEST_ONLY_NO_ORIGINAL_OUTPUT"):
        research.observe_a(Unavailable(), 6, "read_A")
    assert research.inspect() == before


@pytest.mark.parametrize("extra", [0, 1])
def test_dat_consumer_limit_is_explicit_and_fail_closed(research, extra):
    raw = fixture_envelope(research)
    body = raw["artifact"]["dat_bytes"]
    body += b" " * (READ_LIMITS["dat_bytes"] + extra - len(body))
    raw["artifact"].update(dat_bytes=body, sha256=digest_bytes(body), size=len(body))
    candidate = research.inspect()["candidates"]["A"]
    if extra:
        with pytest.raises(ContractError, match="OWNER_ARTIFACT_MISMATCH"):
            observation_record(raw, candidate, pin(research))
    else:
        record = observation_record(raw, candidate, pin(research))
        assert len(record["evidence"]["artifact"]["dat_hex_chunks"]) == READ_LIMITS["hex_chunks"]
        assert validate_observation_record(record, candidate, pin(research))["V2"] == "NOT_VERIFIED"


@pytest.mark.parametrize("extra", [0, 1])
def test_event_consumer_limit_is_explicit_and_fail_closed(research, extra):
    raw = fixture_envelope(research)
    for index in range(len(raw["events"]), READ_LIMITS["events"] + extra):
        raw["events"].append({"type": "OBSERVATION_RECORDED", "project_sequence": index + 11,
                              "run_sequence": index + 1, "run_id": raw["run"]["run_id"]})
    if extra:
        with pytest.raises(ContractError, match="OWNER_HISTORY_INCOMPLETE"):
            verify_owner_evidence(raw, research.inspect()["candidates"]["A"], pin(research))
    else:
        result = verify_owner_evidence(raw, research.inspect()["candidates"]["A"], pin(research))
        assert result["real_goal"] == "INCONCLUSIVE" and result["V2"] == "NOT_VERIFIED"


def test_record_only_observation_does_not_masquerade_as_authentic_dossier(research):
    raw = fixture_envelope(research)
    class Port:
        def read_real_artifact(self, **_kwargs):
            return copy.deepcopy(raw)
    research.reserve_a(pin(research), 3, "reserve_A")
    research.record_intent_a(4, "intent_A")
    research.observe_a(Port(), 5, "observe_A")
    report = research.pre_a_dossier()
    assert report["real_a_output"] == "UNAUTHENTICATED_RECORD_ONLY"
    assert report["verification"]["V2"] == "NOT_VERIFIED"
    assert report["verification"]["V3"] == "INCONCLUSIVE"
    assert report["budget"]["held"] == 1 and not report["execution_authorized"]
