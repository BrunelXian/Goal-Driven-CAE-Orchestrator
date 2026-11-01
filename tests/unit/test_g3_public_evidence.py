"""Original G3 public-record fixtures; no AF connection, Owner or real output."""

import copy
import json
from concurrent.futures import ThreadPoolExecutor

import pytest

from aegiscae.contracts.research_contracts import ContractError
from aegiscae.research.project import ProjectError, open_existing_readonly
from aegiscae.research.rod_bridge import RodBridge
from aegiscae.research.rod_evidence import af_digest
from aegiscae.research.rod_preview import RealPreviewAdapter, create_preview
from aegiscae.research.rod_preview_rules import RodPreviewContract
from aegiscae.research.rod_public_evidence import PublicRodEvidence
from test_g2_rod_core import envelope, fake_evidence, intent, prepare_a, sha


def rehash(bundle):
    projection = {k: v for k, v in bundle.items() if k != "bindings_digest"}
    projection["synthetic_envelope"] = {
        k: v for k, v in bundle["synthetic_envelope"].items() if k != "dat_bytes"}
    bundle["bindings_digest"] = af_digest(projection)
    return bundle


@pytest.fixture
def case(tmp_path):
    bridge = RodBridge(create_preview(tmp_path / "research", "G3 fixture", RodPreviewContract()))
    prepare_a(bridge)
    intent(bridge)
    raw = fake_evidence()
    raw["run"]["revision"] = 4
    raw["run"].update(process_observation="NOT_APPLICABLE", exit_verification="NOT_APPLICABLE")
    raw["validations"][0]["evidence_refs"] = ["fixture_observation"]
    raw["validations"][0]["validation_id"] = "fixture_validation"
    for index, event in enumerate(raw["events"], 1):
        event.update(run_sequence=index, payload={"revision": index})
    raw["events"][-1]["evidence_refs"] = ["fixture_observation", "fixture_validation"]
    fake = bridge.inspect()["attempts"]["A"]["binding"]
    public = {k: fake[k] for k in ("project_id", "project_instance_id", "plan_id",
        "plan_digest", "input_digest", "output_identity")}
    public.update(schema="af-public-fake-plan-v1", source="PERSISTED_FAKE_PLAN",
        backend_id="fake-v1", backend_version=1, input_size=10,
        resources_digest=sha("fixture-resources"), configuration_digest=sha("fixture-config"),
        execution_authorized=False)
    ref = bridge.numeric_reference("A")
    bundle = {"schema": "af-rod-public-evidence-bundle-v1",
        "source": "OFFLINE_PUBLIC_PORT_FIXTURE_PLUS_SYNTHETIC_DAT",
        "rod_plan_ref": ref, "rod_plan_ref_digest": af_digest(ref),
        "contract_revisions": {"goal_revision": 2, "model_revision": 2,
                               "research_revision": ref["research_revision"]},
        "fake_plan": public, **{k: copy.deepcopy(raw[k]) for k in
                               ("receipt", "run", "events", "validations")},
        "synthetic_envelope": envelope(bridge), "raw_solver_logs": "ABSENT_NOT_REAL_SOLVER",
        "real_solver_executed": False, "real_source_authentication": "NOT_VERIFIED",
        "V2": "NOT_VERIFIED", "V4": "NOT_ASSESSED", "ODB": "NOT_VERIFIED"}
    return bridge, raw, rehash(bundle), PublicRodEvidence(bridge.preview)


def test_independent_public_verification_is_read_only_and_never_real(case):
    bridge, raw, bundle, reader = case
    before = bridge.inspect()
    result = reader.verify(bundle, expected_revision=5, fake_evidence=raw)
    assert result["fixture_checks"] == {
        "provenance": "PASS", "numerical": "PASS", "goal": "NOT_SATISFIED"}
    assert result["metrics"]["displacement_mm"] == "0.01"
    assert result["V0"] == result["V2"] == result["ODB"] == "NOT_VERIFIED"
    assert result["V3"] == result["real_goal"] == "INCONCLUSIVE"
    assert result["V4"] == "NOT_ASSESSED" and result["execution_authorized"] is False
    assert result["public_record_persisted"] is False
    assert "Q:/" not in json.dumps(result) and "dat_bytes" not in json.dumps(result)
    assert bridge.inspect() == before


def test_frozen_identity_comes_from_committed_combined_contract(case):
    bridge, raw, bundle, reader = case
    identity = reader.frozen_identity()
    assert identity["shared_bundle_freeze_revision"] == 2
    assert identity["current_project_revision"] == 5
    assert identity["goal_component_digest"] != identity["model_component_digest"]
    reader.verify(bundle, expected_revision=5, fake_evidence=raw, expected_identity=identity)
    reopened = PublicRodEvidence(RealPreviewAdapter(
        open_existing_readonly(bridge.preview.project._root)))
    assert reopened.frozen_identity() == identity


@pytest.mark.parametrize("field", ["goal_component_digest", "model_component_digest",
                                  "shared_bundle_freeze_revision", "contract_digest"])
def test_wrong_component_identity_is_rejected(case, field):
    _bridge, raw, bundle, reader = case
    identity = reader.frozen_identity()
    identity[field] = 3 if field.endswith("revision") else sha("substitution")
    with pytest.raises(ContractError, match="FROZEN_COMPONENT_MISMATCH"):
        reader.verify(bundle, expected_revision=5, fake_evidence=raw, expected_identity=identity)


@pytest.mark.parametrize("field,value", [
    ("goal_revision", 1), ("model_revision", 5), ("research_revision", 5),
    ("goal_revision", True), ("model_revision", "2"),
])
def test_revision_dimensions_cannot_be_substituted(case, field, value):
    _bridge, raw, bundle, reader = case
    bundle["contract_revisions"][field] = value
    with pytest.raises(ContractError, match="PUBLIC_REVISION_MISMATCH"):
        reader.verify(rehash(bundle), expected_revision=5, fake_evidence=raw)


@pytest.mark.parametrize("field,value", [
    ("source", "AF_REAL_DECLARATION"), ("source", "TEST_ONLY_REAL_SCHEMA_FIXTURE"),
    ("real_solver_executed", True), ("real_source_authentication", "PASS"),
    ("V2", "PASS"), ("V4", "PASS"), ("ODB", "PASS"),
    ("raw_solver_logs", "SOLVER TEXT SAYS COMPLETED"),
    ("raw_solver_logs", None),
])
def test_fake_or_schema_declaration_never_becomes_authenticated_real(case, field, value):
    _bridge, raw, bundle, reader = case
    bundle[field] = value
    with pytest.raises(ContractError, match="PUBLIC_SOURCE_UNQUALIFIED"):
        reader.verify(rehash(bundle), expected_revision=5, fake_evidence=raw)


@pytest.mark.parametrize("record,field,value", [
    ("receipt", "request_status", "UNKNOWN"), ("receipt", "run_id", "other_run"),
    ("run", "backend_outcome", "UNKNOWN"), ("run", "execution", "RUNNING"),
    ("run", "solver_conclusion", "COMPLETED"), ("run", "phase_attempt_id", "other_attempt"),
    ("run", "revision", True), ("run", "revision", 0),
])
def test_correlated_bad_raw_records_fail_even_after_rehash(case, record, field, value):
    _bridge, raw, bundle, reader = case
    raw[record][field] = bundle[record][field] = value
    with pytest.raises(ContractError):
        reader.verify(rehash(bundle), expected_revision=5, fake_evidence=raw)


@pytest.mark.parametrize("mutation", ["missing_start", "missing_produced", "wrong_order",
    "wrong_attempt", "missing_validation", "missing_refs", "invalid_ref", "wrong_raw"])
def test_incomplete_raw_event_validation_history_is_rejected(case, mutation):
    _bridge, raw, bundle, reader = case
    if mutation == "missing_start":
        raw["events"].pop(1)
    elif mutation == "missing_produced":
        raw["events"].pop(2)
    elif mutation == "wrong_order":
        raw["events"][1]["type"], raw["events"][2]["type"] = (
            raw["events"][2]["type"], raw["events"][1]["type"])
    elif mutation == "wrong_attempt":
        raw["events"][1]["phase_attempt_id"] = "wrong_attempt"
    elif mutation == "missing_validation":
        raw["validations"] = []
    elif mutation == "missing_refs":
        raw["validations"][0]["evidence_refs"] = []
    elif mutation == "invalid_ref":
        raw["validations"][0]["evidence_refs"] = [None]
    else:
        bundle["receipt"]["request_id"] = "other_receipt"
    if mutation != "wrong_raw":
        bundle["events"], bundle["validations"] = copy.deepcopy((raw["events"], raw["validations"]))
    with pytest.raises(ContractError):
        reader.verify(rehash(bundle), expected_revision=5, fake_evidence=raw)


@pytest.mark.parametrize("mutation", ["bytes", "units", "entity", "step", "old_plan",
    "foreign_fake", "digest", "filename", "unstable"])
def test_corrupt_or_old_artifacts_cannot_pass_public_interface(case, mutation):
    _bridge, raw, bundle, reader = case
    env = bundle["synthetic_envelope"]
    if mutation == "bytes":
        env["dat_bytes"] += b"corrupt"
    elif mutation == "units":
        env["artifact"]["units"]["displacement"] = "m"
    elif mutation == "entity":
        env["artifact"]["selector"]["node"] = 1
    elif mutation == "step":
        env["artifact"]["selector"]["step"] = True
    elif mutation == "old_plan":
        bundle["rod_plan_ref"]["plan_id"] = "old_rod_plan"
    elif mutation == "foreign_fake":
        bundle["fake_plan"]["project_instance_id"] = "other_instance"
    elif mutation == "digest":
        bundle["bindings_digest"] = sha("wrong")
    elif mutation == "filename":
        env["artifact"]["filename"] = "../old.dat"
    else:
        env["artifact"]["stable_read"] = False
    if mutation != "digest":
        rehash(bundle)
    with pytest.raises(ContractError):
        reader.verify(bundle, expected_revision=5, fake_evidence=raw)


@pytest.mark.parametrize("fault", ["duplicate", "changed_component"])
def test_public_audit_freeze_is_unique_and_consistent(case, monkeypatch, fault):
    bridge, _raw, _bundle, reader = case
    original = bridge.preview.project.audit_events

    def altered(_self, *args):
        events = copy.deepcopy(list(original(*args)))
        freeze = next(e for e in events if e["kind"] == "WORKFLOW_RECORDED"
                      and e["workflow"]["action"] == "FREEZE")
        if fault == "duplicate":
            events.append(copy.deepcopy(freeze))
        else:
            freeze["workflow"]["data"]["goal_min_mm"] = "0.018"
        return events

    monkeypatch.setattr(type(bridge.preview.project), "audit_events", altered)
    with pytest.raises(ContractError):
        reader.frozen_identity()


def test_public_port_receives_exact_pins_and_is_not_retried(case):
    bridge, raw, bundle, reader = case

    class Port:
        calls = 0

        def read_test_evidence(self, **request):
            self.calls += 1
            assert request["goal_revision"] == request["model_revision"] == 2
            assert request["rod_plan_ref"] == bridge.numeric_reference("A")
            assert request["run_id"] == raw["run"]["run_id"]
            assert request["fake_plan_ref"] == raw["plan_ref"]
            return copy.deepcopy(bundle)

    port = Port()
    result = reader.read(port, expected_revision=5, fake_evidence=raw,
        evidence_key="numeric_A", output_digest=bundle["synthetic_envelope"]["artifact"]["output_digest"],
        at_time=100)
    assert port.calls == 1 and result["V2"] == "NOT_VERIFIED"

    class LostReply:
        calls = 0

        def read_test_evidence(self, **_request):
            self.calls += 1
            raise TimeoutError("synthetic response loss")

    lost = LostReply()
    before = bridge.inspect()
    with pytest.raises(TimeoutError):
        reader.read(lost, expected_revision=5, fake_evidence=raw,
            evidence_key="numeric_A", output_digest=sha("output"), at_time=100)
    assert lost.calls == 1 and bridge.inspect() == before


def test_state_changes_during_public_read_are_rejected(case):
    bridge, raw, bundle, reader = case

    class Port:
        def read_test_evidence(self, **_request):
            bridge.unknown("A", 5, "lost_submission")
            return bundle

    with pytest.raises(ContractError, match="RESEARCH_CHANGED_DURING_READ"):
        reader.read(Port(), expected_revision=5, fake_evidence=raw,
            evidence_key="numeric_A", output_digest=sha("output"), at_time=100)
    assert bridge.inspect()["pending_or_unknown"] is True
    assert bridge.inspect()["budget"]["held_or_charged"] == 1
    with pytest.raises(ContractError):
        bridge.propose_b("candidate_B")


def test_public_observe_persists_old_format_with_exact_replay_and_causal_b(case):
    bridge, raw, bundle, _reader = case
    result = bridge.observe_public(bundle, raw, 5, "observe_public_A")
    assert result["workflow"]["attempts"]["A"]["status"] == "G2_OBSERVED"
    assert result["verification"]["public_record_persisted"] is False
    replay = bridge.observe_public(bundle, raw, 5, "observe_public_A")
    assert replay["workflow"]["replayed"] is True
    proposal = bridge.propose_b("candidate_B")
    assert proposal["causal"]["a_run_id"] == raw["run"]["run_id"]
    assert proposal["causal"]["a_receipt_digest"] == af_digest(raw["receipt"])
    bridge.admit(proposal, 6, "admit_B")
    assert bridge.inspect()["attempts"]["B"]["inert_plan"] is None
    assert bridge.inspect()["budget"]["held_or_charged"] == 1
    reopened = RodBridge(RealPreviewAdapter(open_existing_readonly(bridge.preview.project._root)))
    assert reopened.inspect() == bridge.inspect()


def test_two_public_observers_have_one_durable_effect(case):
    bridge, raw, bundle, _reader = case

    def record(key):
        try:
            return bridge.observe_public(bundle, raw, 5, key)["workflow"]["project_revision"]
        except (ContractError, ProjectError):
            return "REFUSED"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(record, ("observer_one", "observer_two")))
    assert results.count(6) == 1 and results.count("REFUSED") == 1
    assert bridge.inspect()["budget"]["held_or_charged"] == 1


@pytest.mark.parametrize("mutation", ["event_revision", "event_sequence", "event_bool",
    "extra_event", "refs_missing", "refs_wrong", "validation_id", "process_unknown",
    "exit_unknown", "terminal_revision"])
def test_history_completeness_is_checked_independently_of_af(case, mutation):
    _bridge, raw, bundle, reader = case
    if mutation == "event_revision":
        raw["events"][1]["payload"]["revision"] = 3
    elif mutation == "event_sequence":
        raw["events"][1]["run_sequence"] = 4
    elif mutation == "event_bool":
        raw["events"][0]["run_sequence"] = True
    elif mutation == "extra_event":
        raw["events"].append({"run_id": "run_A", "type": "EXTRA", "project_sequence": 5})
    elif mutation == "refs_missing":
        del raw["events"][-1]["evidence_refs"]
    elif mutation == "refs_wrong":
        raw["events"][-1]["evidence_refs"] = ["unrelated_observation"]
    elif mutation == "validation_id":
        del raw["validations"][0]["validation_id"]
    elif mutation == "process_unknown":
        raw["run"]["process_observation"] = "UNKNOWN"
    elif mutation == "exit_unknown":
        raw["run"]["exit_verification"] = "UNKNOWN"
    else:
        raw["run"]["revision"] = 5
    for key in ("events", "validations", "run"):
        bundle[key] = copy.deepcopy(raw[key])
    with pytest.raises(ContractError):
        reader.verify(rehash(bundle), expected_revision=5, fake_evidence=raw)
