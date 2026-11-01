"""Original synthetic evidence only; no AF Owner, Solver, or source attestation."""

import copy

import pytest

from aegiscae.contracts.research_contracts import ContractError, digest_bytes
from aegiscae.research import rod_real_project as real
from aegiscae.research.rod_real_verify import (
    observation_record,
    validate_observation_record,
    verify_owner_artifact_set,
    verify_owner_evidence,
)
from test_d4_real_project import pin
from test_d4_real_verify import fixture_envelope


@pytest.fixture
def case(tmp_path):
    research = real.create_real_research(tmp_path / "a-only-evidence", "Synthetic acquisition records")
    candidate, binding = research.inspect()["candidates"]["A"], pin(research)
    return candidate, binding, fixture_envelope(research)


def artifact_set(base):
    run = base["run"]
    identity = {k: run[k] for k in ("run_id", "plan_digest", "phase_attempt_id", "project_instance_id")}
    raw = {"dat": base["artifact"]["dat_bytes"],
           "sta": b"THE ANALYSIS HAS COMPLETED SUCCESSFULLY\n",
           "msg": b"THE ANALYSIS HAS BEEN COMPLETED\n"}
    artifacts = []
    for extension, payload in raw.items():
        ref = "output:" + extension
        artifacts.append({**identity, "logical_ref": ref, "bytes": payload,
            "sha256": digest_bytes(payload), "size": len(payload),
            "input_digest": base["artifact"]["input_digest"],
            "collected_record": {"logical_ref": ref, "digest": digest_bytes(payload),
                "size": len(payload), "device": 0, "inode": 2**90 + len(artifacts),
                "mtime_ns": 99_000_000_000, "read_at": 100}})
    return {"schema": "af-rod-owner-artifact-set-v1", "source": "AF_OWNER_RECORD_CHAIN",
            "source_authentication": "NOT_VERIFIED", "owner_evidence": copy.deepcopy(base),
            "launch_intent": {**identity, "output_key": base["plan"]["output_key"],
                "owner_id": "syntheticOriginalOwner", "intent_at_ns": 98_000_000_000,
                "state": "START_INTENT"}, "artifacts": artifacts}


@pytest.mark.parametrize("key", ["step", "increment", "element", "integration_point"])
def test_policy_boolean_cannot_equal_frozen_integer(case, key):
    candidate, binding, base = case
    candidate["verification_policy"][key] = True
    with pytest.raises(ContractError, match="REAL_VERIFICATION_POLICY_CHANGED"):
        verify_owner_evidence(base, candidate, binding)


def test_candidate_boolean_cannot_reuse_integer_candidate_digest(case):
    candidate, binding, base = case
    base["plan"]["rod_contract"]["candidate"]["mutable_entity"]["dof"] = True
    with pytest.raises(ContractError, match="OWNER_CANDIDATE_MISMATCH"):
        verify_owner_evidence(base, candidate, binding)


def test_initialization_replay_rejects_boolean_frozen_policy(case):
    candidate, _, _ = case
    bundle = real.real_bundle(candidate["research_project_id"])
    payload = {"schema_version": real.VERSION, "action": "INITIALIZE", "key": "syntheticInit",
               "before_project_revision": 2, "data": {"verification_policy": copy.deepcopy(real.NUMERICAL_POLICY)}}
    assert real.apply_real_workflow(None, payload, bundle, 2, bundle.digests()["bundle"])["version"] == real.VERSION
    payload["data"]["verification_policy"]["step"] = True
    with pytest.raises(ContractError, match="REAL_VERIFICATION_POLICY_CHANGED"):
        real.apply_real_workflow(None, payload, bundle, 2, bundle.digests()["bundle"])


@pytest.mark.parametrize("field,value", [("execution_authorized", 0), ("step", True), ("increment", True)])
def test_persisted_check_is_compared_with_exact_types(case, field, value):
    candidate, binding, base = case
    record = observation_record(base, candidate, binding)
    target = record["independent"] if field == "execution_authorized" else record["independent"]["metrics"]
    target[field] = value
    with pytest.raises(ContractError, match="OWNER_REVIEW_FORGED"):
        validate_observation_record(record, candidate, binding)


def test_original_observation_roundtrip_and_additive_artifacts_do_not_authenticate(case):
    candidate, binding, base = case
    record = observation_record(base, candidate, binding)
    original = validate_observation_record(record, candidate, binding)
    wrapper = artifact_set(base)
    before = copy.deepcopy(wrapper)
    result = verify_owner_artifact_set(wrapper, candidate, binding)
    assert all(result[k] == v for k, v in original.items())
    assert result["artifact_set_check"] == "RECORDS_AND_COMPLETION_TEXT_CHECKED_UNAUTHENTICATED"
    assert result["source_authentication"] == result["V2"] == "NOT_VERIFIED"
    assert result["V3"] == result["real_goal"] == "INCONCLUSIVE"
    assert result["execution_authorized"] is False
    assert wrapper == before
    wrapper["artifacts"].reverse()
    assert verify_owner_artifact_set(wrapper, candidate, binding) == result


@pytest.mark.parametrize("field,value", [
    ("run_id", "oldRun"), ("phase_attempt_id", "oldAttempt"),
    ("project_instance_id", "otherInstance"), ("plan_digest", digest_bytes(b"oldPlan")),
    ("input_digest", digest_bytes(b"oldInput")), ("size", True),
    ("sha256", digest_bytes(b"oldBytes")), ("bytes", b"changed"),
])
@pytest.mark.parametrize("index", [0, 1, 2])
def test_artifact_exact_identity_and_content_rejections(case, field, value, index):
    candidate, binding, base = case
    wrapper = artifact_set(base)
    wrapper["artifacts"][index][field] = value
    with pytest.raises(ContractError):
        verify_owner_artifact_set(wrapper, candidate, binding)


@pytest.mark.parametrize("field,value", [
    ("logical_ref", "output:log"), ("digest", digest_bytes(b"old")), ("size", True),
    ("device", True), ("inode", False), ("device", -1), ("inode", 2**128),
    ("mtime_ns", True), ("mtime_ns", 97_000_000_000),
    ("mtime_ns", 102_000_000_000), ("read_at", True), ("read_at", 102),
])
def test_collector_rejects_mutation_and_inconsistent_time(case, field, value):
    candidate, binding, base = case
    wrapper = artifact_set(base)
    wrapper["artifacts"][1]["collected_record"][field] = value
    with pytest.raises(ContractError):
        verify_owner_artifact_set(wrapper, candidate, binding)


@pytest.mark.parametrize("field,value", [
    ("run_id", "oldRun"), ("phase_attempt_id", "oldAttempt"),
    ("project_instance_id", "otherInstance"), ("plan_digest", digest_bytes(b"oldPlan")),
    ("output_key", digest_bytes(b"oldOutput")), ("intent_at_ns", True),
    ("state", "COMPLETED"), ("owner_id", ""),
])
def test_original_intent_mismatch_rejected(case, field, value):
    candidate, binding, base = case
    wrapper = artifact_set(base)
    wrapper["launch_intent"][field] = value
    with pytest.raises(ContractError):
        verify_owner_artifact_set(wrapper, candidate, binding)


@pytest.mark.parametrize("change", ["missing", "duplicate", "extra", "collector_extra",
                                     "dat_mismatch", "dat_time", "source_promotion"])
def test_incomplete_or_unqualified_artifact_sets_rejected(case, change):
    candidate, binding, base = case
    wrapper = artifact_set(base)
    if change == "missing":
        wrapper["artifacts"].pop()
    elif change == "duplicate":
        wrapper["artifacts"][2] = copy.deepcopy(wrapper["artifacts"][1])
    elif change == "extra":
        wrapper["artifacts"].append(copy.deepcopy(wrapper["artifacts"][1]))
    elif change == "collector_extra":
        wrapper["artifacts"][0]["collected_record"]["path"] = "caller-path"
    elif change == "dat_time":
        wrapper["artifacts"][0]["collected_record"]["read_at"] = 101
    elif change == "source_promotion":
        wrapper["source_authentication"] = "PASS"
    else:
        replace_bytes(wrapper["artifacts"][0], base["artifact"]["dat_bytes"] + b"\n")
    with pytest.raises(ContractError):
        verify_owner_artifact_set(wrapper, candidate, binding)


def replace_bytes(artifact, raw):
    artifact.update(bytes=raw, sha256=digest_bytes(raw), size=len(raw))
    artifact["collected_record"].update(digest=digest_bytes(raw), size=len(raw))


@pytest.mark.parametrize("index,raw", [
    (1, b""), (2, b"unknown completion"),
    (1, b"THE ANALYSIS HAS COMPLETED SUCCESSFULLY\nHAS NOT BEEN COMPLETED"),
    (2, b"THE ANALYSIS HAS BEEN COMPLETED\nHAS NOT BEEN COMPLETED"),
    (2, b"THE ANALYSIS HAS BEEN COMPLETED\n***ERROR"),
    (1, b"THE ANALYSIS HAS COMPLETED SUCCESSFULLY\n***ERROR"),
    (2, b"THE ANALYSIS HAS BEEN COMPLETED\n" + b"x" * 1048576),
], ids=["empty-sta", "unknown-msg", "contradictory-sta", "contradictory-msg",
        "error-msg", "error-sta", "oversized-msg"])
def test_completion_rejects_absent_failed_oversized_bytes_even_with_consistent_hash(case, index, raw):
    candidate, binding, base = case
    wrapper = artifact_set(base)
    replace_bytes(wrapper["artifacts"][index], raw)
    with pytest.raises(ContractError):
        verify_owner_artifact_set(wrapper, candidate, binding)
