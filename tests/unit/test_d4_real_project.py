"""Fresh fixed rod contracts; no external processes, Grant, Owner or Solver."""

import copy
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict

import pytest

from aegiscae.contracts.research_contracts import ContractError, digest_bytes
from aegiscae.research import project as store, rod_real_project as real
from aegiscae.research.rod_preview import create_preview
from aegiscae.research.rod_preview_rules import RodPreviewContract, TEMPLATE
from aegiscae.research.rod_evidence import af_digest


@pytest.fixture
def research(tmp_path):
    return real.create_real_research(tmp_path / "new-real-intent", "D4 declared rod")


def pin(research):
    candidate = research.inspect()["candidates"]["A"]
    return {"project_id": "fixtureAF", "project_instance_id": "fixtureInstance", "plan_id": "fixturePlan",
            "plan_digest": digest_bytes(b"fixturePlan"), "input_digest": candidate["input_digest"],
            "resources_digest": af_digest(real.RESOURCES), "output_identity": digest_bytes(b"physicalOutput"),
            "backend_id": real.BACKEND, "candidate_output_identity": candidate["output_identity"],
            "request_key": "fixtureRequest", "request_nonce": "fixtureNonce"}


def test_new_real_intent_bundle_and_a_are_frozen_without_authority(research):
    state = research.inspect()
    assert state["project_revision"] == 3 and set(state["candidates"]) == {"A"}
    assert state["candidates"]["A"]["load_n"] == "1"
    assert research.candidate_input() == TEMPLATE
    assert state["budget"] == {"limit": 2, "held": 0, "charged": 0, "available": 2}
    record = research.project.read_frozen_bundle(state["contract_digest"])
    bundle = record["bundle"]
    assert bundle.model.artifacts[0].source_kind == "DECLARED_EXTERNAL"
    assert bundle.goal.budget.max_solver_calls == 2
    assert {c.threshold.value for c in bundle.goal.hard_constraints} == {"0.019", "0.021"}
    assert len(bundle.verification.hard_constraint_checks) == 2
    assert record["hard_constraint_coverage"] == "COMPLETE_DECLARED"
    assert record["human_approval"] == "NOT_ESTABLISHED" and not state["execution_authorized"]
    assert state["verification"]["V2"] == "NOT_VERIFIED" and state["verification"]["V3"] == "INCONCLUSIVE"


def test_readonly_reopen_and_old_preview_remain_separate(research, tmp_path):
    before = research.project._root.joinpath("research.sqlite3").read_bytes()
    reopened = real.RealRodProject(store.open_existing_readonly(research.project._root))
    assert reopened.inspect() == research.inspect()
    assert research.project._root.joinpath("research.sqlite3").read_bytes() == before
    old = create_preview(tmp_path / "old-route", "Old synthetic preview", RodPreviewContract())
    assert old.inspect()["evidence_mode"] == "OFFLINE_AF_SUBSTITUTE"
    with pytest.raises(ContractError, match="REAL_PROJECT_SCHEMA_REQUIRED"):
        real.RealRodProject(old.project).inspect()


def test_exact_reservation_replay_and_changed_content(research):
    data = pin(research)
    first = research.reserve_a(data, 3, "reserve_A")
    assert first["budget"]["held"] == 1
    assert research.reserve_a(data, 3, "reserve_A")["replayed"]
    changed = {**data, "plan_digest": digest_bytes(b"other")}
    with pytest.raises(ContractError, match="IDEMPOTENCY_CONFLICT"):
        research.reserve_a(changed, 4, "reserve_A")
    with pytest.raises(ContractError, match="REAL_ATTEMPT_ALREADY_RESERVED"):
        research.reserve_a(changed, 4, "new_ID_bypass")
    assert research.inspect()["budget"]["held"] == 1


@pytest.mark.parametrize("field,value", [
    ("input_digest", digest_bytes(b"wrong")), ("candidate_output_identity", digest_bytes(b"old_output")),
    ("resources_digest", digest_bytes(b"wrong_resources")),
    ("backend_id", "fake-v1"), ("backend_id", "abaqus-standard-v1"),
])
def test_wrong_plan_ref_never_reserves(research, field, value):
    raw = pin(research)
    raw[field] = value
    with pytest.raises(ContractError, match="REAL_PLAN_BINDING_MISMATCH"):
        research.reserve_a(raw, 3, "bad")
    assert research.inspect()["budget"]["available"] == 2


def test_unknown_holds_budget_and_blocks_b_and_new_a(research):
    research.reserve_a(pin(research), 3, "reserve_A")
    research.record_intent_a(4, "intent_A")
    state = research.mark_unknown_a(5, "unknown_A")
    assert state["budget"] == {"limit": 2, "held": 1, "charged": 0, "available": 1}
    with pytest.raises(ContractError, match="AUTHENTICATED_REAL_A_REQUIRED"):
        research.propose_b({"load_n": "2", "review": "PASS", "real": True}, 6, "forged_B")
    with pytest.raises(ContractError, match="REAL_ATTEMPT_ALREADY_RESERVED"):
        research.reserve_a(pin(research), 6, "third_call_other_ID")
    assert set(research.inspect()["candidates"]) == {"A"}


@pytest.mark.parametrize("revision", [1, 2, 4, True, "3"])
def test_revision_conflict_cannot_hold_budget(research, revision):
    with pytest.raises(ContractError):
        research.reserve_a(pin(research), revision, "bad_revision")
    assert research.inspect()["budget"]["held"] == 0


def test_concurrent_reservation_has_one_winner(research):
    raw = pin(research)
    def reserve(number):
        try:
            return research.reserve_a(raw, 3, "race_" + str(number))["replayed"]
        except (ContractError, store.ProjectError):
            return "REJECTED"
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(reserve, range(2)))
    assert results.count(False) == 1 and results.count("REJECTED") == 1
    assert research.inspect()["budget"]["held"] == 1


@pytest.mark.parametrize("stage", ["before_commit", "after_commit"])
def test_fault_atomicity_and_lost_response_replay(research, monkeypatch, stage):
    raw = pin(research)
    def fail(point):
        if point == stage:
            raise RuntimeError("SYNTHETIC_INTERRUPTION")
    monkeypatch.setattr(real, "_fault", fail)
    with pytest.raises(RuntimeError):
        research.reserve_a(raw, 3, "reserve_A")
    monkeypatch.setattr(real, "_fault", lambda _stage: None)
    state = research.inspect()
    assert state["budget"]["held"] == (stage == "after_commit")
    resumed = research.reserve_a(raw, 3, "reserve_A")
    assert resumed["budget"]["held"] == 1
    assert resumed["replayed"] == (stage == "after_commit")


def test_real_contract_shape_cannot_be_relabelled_or_weakened(research):
    bundle = real.real_bundle(research.inspect()["research_project_id"])
    raw = copy.deepcopy(asdict(bundle))
    raw["goal"]["budget"]["max_solver_calls"] = 3
    altered = type(bundle).from_dict(raw)
    payload = {"schema_version": real.VERSION, "before_project_revision": 2,
               "action": "INITIALIZE", "data": {"verification_policy": copy.deepcopy(real.NUMERICAL_POLICY)}, "key": "initialize"}
    with pytest.raises(ContractError, match="REAL_FROZEN_CONTRACT_MISMATCH"):
        real.apply_real_workflow(None, payload, altered, 2, altered.digests()["bundle"])


def test_interrupted_initialization_keeps_frozen_contract_and_resumes(tmp_path, monkeypatch):
    root = tmp_path / "partial-create"
    def fail(stage):
        if stage == "before_commit":
            raise RuntimeError("SYNTHETIC_INTERRUPTION")
    monkeypatch.setattr(real, "_fault", fail)
    with pytest.raises(RuntimeError):
        real.create_real_research(root, "Interrupted declaration")
    project = store.open_existing_for_explicit_write(root)
    assert project.inspect()["bundle_count"] == 1 and project.inspect()["project_revision"] == 2
    bundle_digest = project.inspect()["latest_bundle_digest"]
    monkeypatch.setattr(real, "_fault", lambda _stage: None)
    resumed = real.RealRodProject(project)
    assert resumed.initialize_a()["project_revision"] == 3
    assert resumed.inspect()["contract_digest"] == bundle_digest
    assert resumed.initialize_a()["replayed"]


def test_actual_validator_bytes_and_explicit_tolerances_are_frozen(research):
    state = research.inspect()
    bundle = research.project.read_frozen_bundle(state["contract_digest"])["bundle"]
    assert {v.level: v.sha256 for v in bundle.verification.validators} == real.implementation_hashes()
    policy = state["candidates"]["A"]["verification_policy"]
    assert policy == real.NUMERICAL_POLICY
    assert policy["displacement_tolerance_mm"] == "0.000001"
    assert policy["stress_tolerance_mpa"] == policy["reaction_tolerance_n"] == "0.0001"


def test_parser_source_drift_fails_read_and_admission_without_migration(research, monkeypatch):
    hashes = real.implementation_hashes()
    hashes["V2"] = digest_bytes(b"different-parser-code")
    monkeypatch.setattr(real, "implementation_hashes", lambda: hashes)
    with pytest.raises(store.ProjectError, match="INTEGRITY_ERROR"):
        research.inspect()
    with pytest.raises(store.ProjectError, match="INTEGRITY_ERROR"):
        research.reserve_a({}, 3, "after_code_changed")


def test_numerical_policy_drift_fails_frozen_replay(research, monkeypatch):
    changed = {**real.NUMERICAL_POLICY, "displacement_tolerance_mm": "0.1"}
    monkeypatch.setattr(real, "NUMERICAL_POLICY", changed)
    with pytest.raises(store.ProjectError, match="INTEGRITY_ERROR"):
        research.inspect()
