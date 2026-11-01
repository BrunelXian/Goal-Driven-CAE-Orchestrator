"""One exact A-only hold from synthetic public preflight, never execution."""

import copy
from concurrent.futures import ThreadPoolExecutor
from pathlib import PureWindowsPath
import time

import pytest

from aegiscae.contracts.research_contracts import ContractError, digest_bytes
from aegiscae.research import project as store, rod_real_project as real
from aegiscae.research.rod_evidence import af_digest
from test_d4_real_project import pin


@pytest.fixture
def research(tmp_path):
    return real.create_real_research(tmp_path / "d6-a-only", "D6 synthetic A-only")


def fixture_preflight(research):
    candidate = research.inspect()["candidates"]["A"]
    binding = pin(research)
    root = PureWindowsPath("C:/SyntheticD6/engineering")
    job = "rod_" + "a" * 32
    binding["output_identity"] = af_digest({"cwd": str(root).casefold(), "job": job})
    raw = {"schema": "af-rod-preflight-v1", "status": "PRECONDITIONS_CHECKED",
        **{k: binding[k] for k in ("project_id", "project_instance_id", "plan_id", "plan_digest")},
        "research_contract": {"research_project_id": candidate["research_project_id"],
            "contract_digest": candidate["contract_digest"], "research_revision": candidate["admitted_revision"],
            "candidate_id": candidate["candidate_id"], "request_nonce": binding["request_nonce"],
            "input_digest": candidate["input_digest"]},
        "resources": copy.deepcopy(real.RESOURCES), "input_path": str(root / "axial_bar.inp"),
        "load_n": "1", "runtime_binding_digest": digest_bytes(b"synthetic runtime"),
        "engineering": str(root), "scratch": str(root / "scratch"),
        "output_key": binding["output_identity"], "expires_at": int(time.time()) + 3600,
        "gate_version": 0, "declared_outputs": [
            {"logical_ref": "output:" + ext, "path": str(root / (job + "." + ext)),
             "binding": "ORIGINAL_RUN_ATTEMPT_INTENT_AND_COLLECTOR_DIGEST"}
            for ext in ("dat", "sta", "msg")],
        "execution_authorized": False, "host_qualification": "NOT_VERIFIED",
        "operator_deployment": "NOT_VERIFIED", "real_a_output": "NOT_PRODUCED",
        "source_authentication": "NOT_VERIFIED"}
    return binding, raw


class Port:
    def __init__(self, raw):
        self.raw = copy.deepcopy(raw)
        self.calls = 0

    def preflight_real(self, **expected):
        self.calls += 1
        assert expected["expected_contract"] == self.raw["research_contract"]
        assert expected["plan_id"] == self.raw["plan_id"]
        assert expected["expected_plan_digest"] == self.raw["plan_digest"]
        return copy.deepcopy(self.raw)


class Unavailable:
    def preflight_real(self, **_kwargs):
        raise AssertionError("public port must not be queried on committed replay")


def test_one_exact_application_atomic_hold_and_readonly_reopen(research):
    binding, raw = fixture_preflight(research)
    port = Port(raw)
    result = research.hold_a_for_review(port, binding, 3, "hold_A")
    assert port.calls == 1 and result["project_revision"] == 4
    assert result["budget"] == {"limit": 2, "held": 1, "charged": 0, "available": 1}
    form = result["form"]
    assert form["preflight"] == raw and form["binding"] == binding
    assert form["status"] == "NOT_EXECUTABLE" and form["solver_attempts_requested"] == 1
    assert form["decision_options"] == ["APPROVE_EXACT_A", "DENY"]
    assert not form["execution_authorized"] and form["b_plan_or_grant"] == "NOT_REQUESTED"
    path = research.project._root / "research.sqlite3"
    before = path.read_bytes()
    reopened = real.RealRodProject(store.open_existing_readonly(research.project._root))
    assert reopened.a_only_application()["application_digest"] == result["application_digest"]
    assert path.read_bytes() == before


def test_unknown_replay_uses_original_snapshot_without_remote_read_or_new_key(research):
    binding, raw = fixture_preflight(research)
    first = research.hold_a_for_review(Port(raw), binding, 3, "hold_A")
    research.record_intent_a(4, "intent_A")
    research.mark_unknown_a(5, "unknown_A")
    replay = research.hold_a_for_review(Unavailable(), binding, 3, "hold_A")
    assert replay["replayed"] and replay["query_first_required"]
    assert replay["application_digest"] == first["application_digest"]
    assert replay["reservation_state"] == "ACCEPTANCE_UNKNOWN"
    assert replay["budget"]["held"] == 1
    with pytest.raises(ContractError, match="REAL_ATTEMPT_ALREADY_RESERVED"):
        research.hold_a_for_review(Unavailable(), binding, 6, "new_request")
    with pytest.raises(ContractError, match="AUTHENTICATED_REAL_A_REQUIRED"):
        research.propose_b({"reviewer": "PASS", "approved": True}, 6, "premature_B")
    assert set(research.inspect()["candidates"]) == {"A"}


@pytest.mark.parametrize("field", ["plan_id", "plan_digest", "request_key", "request_nonce",
                                   "project_id", "project_instance_id", "output_identity"])
def test_same_key_cannot_regenerate_or_rebind_request(research, field):
    binding, raw = fixture_preflight(research)
    research.hold_a_for_review(Port(raw), binding, 3, "hold_A")
    changed = {**binding, field: "changed"}
    with pytest.raises(ContractError, match="IDEMPOTENCY_CONFLICT"):
        research.hold_a_for_review(Unavailable(), changed, 4, "hold_A")
    assert research.inspect()["budget"]["held"] == 1


@pytest.mark.parametrize("path,value", [
    (("execution_authorized",), True),
    (("operator_deployment",), "PASS"),
    (("source_authentication",), "VERIFIED"),
    (("Reviewer",), "PASS"),
    (("project_instance_id",), "wrong-instance"),
    (("resources", "cpus"), 2),
    (("resources", "slots"), True),
    (("load_n",), "2"),
    (("runtime_binding_digest",), "not-a-digest"),
    (("scratch",), "C:/Elsewhere/scratch"),
    (("input_path",), "C:/SyntheticD6/engineering/../old.inp"),
    (("engineering",), "//server/share/engineering"),
    (("engineering",), "C:/NUL/engineering"),
    (("engineering",), "C:/SyntheticD6/./engineering"),
    (("gate_version",), True),
    (("gate_version",), 2**63),
])
def test_untrusted_preflight_never_holds_budget(research, path, value):
    binding, raw = fixture_preflight(research)
    target = raw
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value
    with pytest.raises(ContractError):
        research.hold_a_for_review(Port(raw), binding, 3, "bad_hold")
    assert research.inspect()["budget"]["held"] == 0


@pytest.mark.parametrize("damage", ["foreign_contract", "wrong_revision", "missing_msg", "old_output",
                                    "expired", "phase_B"])
def test_scope_time_and_output_negatives(research, damage):
    binding, raw = fixture_preflight(research)
    if damage == "foreign_contract":
        raw["research_contract"]["contract_digest"] = digest_bytes(b"other")
    elif damage == "wrong_revision":
        raw["research_contract"]["research_revision"] = 4
    elif damage == "missing_msg":
        raw["declared_outputs"].pop()
    elif damage == "old_output":
        raw["declared_outputs"][0]["path"] = raw["declared_outputs"][0]["path"].replace("rod_", "old_")
    elif damage == "expired":
        raw["expires_at"] = int(time.time()) - 1
    else:
        raw["research_contract"]["phase"] = "B"

    class CorruptPort:
        def preflight_real(self, **_kwargs):
            return copy.deepcopy(raw)
    with pytest.raises(ContractError):
        research.hold_a_for_review(CorruptPort(), binding, 3, "bad_hold")
    assert research.inspect()["project_revision"] == 3


@pytest.mark.parametrize("stage", ["before_commit", "after_commit"])
def test_fault_and_lost_response_hold_is_atomic(research, monkeypatch, stage):
    binding, raw = fixture_preflight(research)
    def fault(at):
        if at == stage:
            raise RuntimeError("TEST_D6_INTERRUPTION")
    monkeypatch.setattr(real, "_fault", fault)
    with pytest.raises(RuntimeError, match="TEST_D6_INTERRUPTION"):
        research.hold_a_for_review(Port(raw), binding, 3, "hold_A")
    monkeypatch.setattr(real, "_fault", lambda _stage: None)
    if stage == "before_commit":
        assert research.inspect()["budget"]["held"] == 0
        result = research.hold_a_for_review(Port(raw), binding, 3, "hold_A")
        assert not result["replayed"]
    else:
        result = research.hold_a_for_review(Unavailable(), binding, 3, "hold_A")
        assert result["replayed"]
    assert result["budget"]["held"] == 1


def test_concurrent_application_key_is_single_persistent_hold(research):
    binding, raw = fixture_preflight(research)
    def reserve(_):
        return research.hold_a_for_review(Port(raw), binding, 3, "hold_A")
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(reserve, range(2)))
    assert len({x["application_digest"] for x in results}) == 1
    assert sorted(x["replayed"] for x in results) == [False, True]
    assert research.inspect()["project_revision"] == 4


def test_old_reserve_schema_preserved_and_campaign_is_later_b_gate(research):
    report = research.pre_a_dossier()
    assert report["general_cross_project_scheduler_required_before_a"] is False
    assert "SINGLE_TOTAL_ATTEMPT_AUTHORITY_FOR_THIS_RESEARCH_PROJECT" in report["later_b_prerequisites"]
    research.reserve_a(pin(research), 3, "legacy_hold")
    with pytest.raises(ContractError, match="REAL_APPLICATION_UNAVAILABLE"):
        research.a_only_application()
    assert research.reserve_a(pin(research), 3, "legacy_hold")["replayed"]
