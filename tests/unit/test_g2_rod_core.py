"""New isolated G2 contract fixtures; no AF IPC, Solver, real Grant or OS isolation."""

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import pytest

from aegiscae.contracts.research_contracts import ContractError, canonical_json, digest_bytes
from aegiscae.research import project as store, rod_preview
from aegiscae.research.rod_bridge import RodBridge
from aegiscae.research.rod_evidence import SELECTOR, UNITS, af_digest
from aegiscae.research.rod_preview import RealPreviewAdapter, create_preview
from aegiscae.research.rod_preview_rules import RodPreviewContract
from test_real_rod_preview import synthetic_dat


def sha(text):
    return digest_bytes(text.encode())


class InertPort:
    """Only a unit fixture; real public AF product is tested cross-repository."""

    def prepare(self, **request):
        resources = {"cpus": 1, "memory_mb": 256, "timeout_seconds": 60}
        self.ref = {"schema": "af-rod-plan-ref-v1", "source": "INERT_ROD_PLAN",
            "profile": "axial_rod_cload_v1", "project_id": "rod_project_A",
            "project_instance_id": "rod_instance_A", "plan_id": "rod_plan_A",
            "plan_digest": sha("rod-plan-A"), "candidate_id": request["candidate_id"],
            "candidate_digest": sha("unit-candidate-metadata"),
            "input_digest": digest_bytes(request["candidate_bytes"]),
            "input_size": len(request["candidate_bytes"]), "resources": resources,
            "resources_digest": af_digest(resources), "output_identity": sha("rod-output-A"),
            "input_path": "Q:/unit/inert/input.inp", "output_path": "Q:/unit/inert/output",
            "contract_digest": request["contract_digest"],
            "research_project_id": request["research_project_id"],
            "research_revision": request["research_revision"], "phase": request["phase"],
            "expires_at": request["expires_at"], "load_n": request["load_n"],
            "tolerances": request["tolerances"],
            "verification_policy_digest": af_digest(request["tolerances"]),
            "authorization_state": "NOT_AUTHORIZED", "execution_authorized": False}
        return copy.deepcopy(self.ref)

    def inspect(self, plan_id, expected_digest, *, at_time):
        assert plan_id == self.ref["plan_id"] and expected_digest == self.ref["plan_digest"]
        assert at_time < self.ref["expires_at"]
        return copy.deepcopy(self.ref)


def fake_plan(step="A"):
    return {"schema": "af-fake-plan-ref-v1", "source": "FAKE_TEST_ONLY", "phase": step,
        "project_id": "ipc_project_" + step, "project_instance_id": "ipc_instance_" + step,
        "plan_id": "ipc_plan_" + step, "plan_digest": sha("ipc-plan-" + step),
        "input_digest": sha("ipc-fixed-input"), "grant_id": "test_grant_" + step,
        "request_key": "original_key_" + step, "output_identity": sha("ipc-output-" + step)}


def fake_evidence(step="A"):
    plan = fake_plan(step)
    binding = {k: plan[k] for k in ("source", "project_id", "project_instance_id",
                                   "plan_id", "plan_digest", "input_digest")}
    binding.update(run_id="run_" + step, phase_attempt_id="attempt_" + step,
                   receipt_id="receipt_" + step)
    receipt = {"request_id": binding["receipt_id"], "idempotency_key": plan["request_key"],
               "request_status": "ACCEPTED", "run_id": binding["run_id"], "accepted_sequence": 1}
    run = {k: binding[k] for k in ("project_id", "project_instance_id", "plan_id", "plan_digest",
                                   "run_id", "phase_attempt_id")}
    run.update(grant_id=plan["grant_id"], attempt_no=1, retry_of=None, backend_id="fake-v1",
        simulation=True, solver_conclusion="NOT_RUN", execution="FINISHED",
        artifact_validation="VALID", reconciliation="NONE", phase="FAKE", backend_outcome="COMPLETED")
    return {"schema": "af-fake-evidence-v1", "source": "FAKE_TEST_ONLY", "phase": step,
        "project_directory": "Q:/unit/ipc_" + step, "plan_ref": plan, "binding": binding,
        "receipt": receipt, "run": run,
        "events": [{"run_id": binding["run_id"], "project_sequence": 1, "type": "REQUEST_ACCEPTED"},
                   {"run_id": binding["run_id"], "project_sequence": 2, "type": "START_INTENT"},
                   {"run_id": binding["run_id"], "project_sequence": 3, "type": "FAKE_COMPLETED"},
                   {"run_id": binding["run_id"], "project_sequence": 4, "type": "VALIDATION_RECORDED"}],
        "validations": [{"run_id": binding["run_id"], "phase_attempt_id": binding["phase_attempt_id"],
                         "scope": "simulation", "policy_id": "fake-result-v1", "verdict": "PASS"}],
        "real_solver_executed": False, "all_owned_processes_exited": True,
        "owned_process_count": 1, "normal_exit": True, "raw_handle_proof": "Q:/unit/lifecycle.json",
        "runtime_origin": {"schema": "af-g2-runtime-origin-v1", "scope": "FAKE_TEST_ONLY",
                           "package_path": "Q:/unit/abqjobpilot",
                           "service_path": "Q:/unit/abqjobpilot/execution/service.py",
                           "supervisor_path": "Q:/unit/abqjobpilot/execution/supervisor.py"}}


def envelope(bridge, step="A", data=None):
    view = bridge.inspect()
    numeric = bridge.numeric_reference(step)
    data = synthetic_dat(view["attempts"][step]["candidate"]["load_n"]) if data is None else data
    return {"schema": "af-rod-evidence-envelope-v1" if step == "A" else "gdcae-synthetic-evidence-envelope-v1", "source": "SYNTHETIC_DAT",
        "evidence_key": "numeric_" + step, "plan_ref": numeric, "plan_ref_digest": af_digest(numeric),
        "artifact": {"filename": "synthetic.dat", "output_identity": numeric["output_identity"],
                     "output_digest": digest_bytes(data), "size": len(data), "stable_read": step == "A",
                     "selector": dict(SELECTOR), "units": dict(UNITS)},
        "execution_link": fake_evidence(step)["binding"], "real_solver_executed": False,
        "real_solver_status": "NOT_RUN", "dat_bytes": data}


@pytest.fixture
def bridge(tmp_path):
    return RodBridge(create_preview(tmp_path / "research", "G2 unit only", RodPreviewContract()))


def prepare_a(bridge):
    candidate = bridge.proposal("A", "1", "candidate_A")
    bridge.admit(candidate, 2, "admit_A")
    port = InertPort()
    bridge.prepare_a(port, revision=3, key="plan_A", request_key="prepare_A", at_time=100,
                     expires_at=200)
    return port


def intent(bridge, step="A"):
    return bridge.fake_intent(step, fake_plan(step), bridge.inspect()["project_revision"], "intent_" + step)


def observe(bridge, step="A", data=None):
    return bridge.observe(step, fake_evidence(step), envelope(bridge, step, data),
                          bridge.inspect()["project_revision"], "observe_" + step)


def test_reopen_two_source_chain_and_no_real_verdict(bridge):
    prepare_a(bridge)
    assert bridge.inspect()["budget"]["held_or_charged"] == 0
    intent(bridge)
    observe(bridge)
    b = bridge.propose_b("candidate_B")
    assert b["load_n"] == "2" and b["causal"]["a_receipt_digest"] == af_digest(fake_evidence()["receipt"])
    bridge.admit(b, bridge.inspect()["project_revision"], "admit_B")
    assert bridge.numeric_reference("B")["source"] == "SYNTHETIC_NOT_REGISTERED"
    intent(bridge, "B")
    final = observe(bridge, "B")
    assert final["budget"]["held_or_charged"] == 2 and final["real_solver_calls"] == 0
    assert final["attempts"]["B"]["decision"]["fixture_checks"]["goal"] == "SATISFIED"
    assert final["attempts"]["B"]["decision"]["V2"] == "NOT_VERIFIED"
    assert final["attempts"]["B"]["decision"]["V3"] == "INCONCLUSIVE"
    reopened = RodBridge(RealPreviewAdapter(store.open_existing_readonly(bridge.preview.project._root)))
    assert reopened.inspect() == {k: v for k, v in final.items() if k != "replayed"}
    safe = reopened.public_summary()
    assert "dat_hex_chunks" not in json.dumps(safe) and "run_A" not in json.dumps(safe)
    with pytest.raises(ContractError):
        bridge.proposal("B", "2.1", "candidate_C")


def test_measured_a_sensitivity(tmp_path):
    proposed = []
    for index, value in enumerate(("0.0099995", "0.0100005")):
        bridge = RodBridge(create_preview(tmp_path / str(index), "Sensitivity", RodPreviewContract()))
        prepare_a(bridge)
        intent(bridge)
        observe(bridge, data=synthetic_dat().replace(b"2 0.01 0 0", ("2 " + value + " 0 0").encode()))
        proposed.append(bridge.propose_b("candidate_B")["load_n"])
    assert proposed == ["2.000100005", "1.999900005"]


def test_satisfied_fixture_a_stops_b(tmp_path):
    contract = RodPreviewContract(goal_min_mm="0.009", goal_max_mm="0.011")
    bridge = RodBridge(create_preview(tmp_path / "satisfied", "Fixture only", contract))
    prepare_a(bridge)
    intent(bridge)
    observe(bridge)
    with pytest.raises(ContractError, match="A_NOT_ELIGIBLE"):
        bridge.propose_b("candidate_B")


def test_no_true_b_plan_and_no_v1_budget_bypass(bridge):
    prepare_a(bridge)
    intent(bridge)
    observe(bridge)
    b = bridge.propose_b("candidate_B")
    bridge.admit(b, 6, "admit_B")
    assert bridge.inspect()["attempts"]["B"]["inert_plan"] is None
    with pytest.raises(ContractError, match="PLAN_STATE_CONFLICT"):
        bridge.prepare_a(InertPort(), revision=7, key="plan_B", request_key="prepare_B",
                         at_time=100, expires_at=200)
    with pytest.raises(ContractError, match="PREVIEW_ROUTE_MISMATCH"):
        bridge.preview.record_intent("B", {}, 7, "legacy_bypass")
    intent(bridge, "B")
    with pytest.raises(ContractError):
        bridge.fake_intent("B", fake_plan("B"), 8, "third_attempt")
    assert bridge.inspect()["budget"]["available"] == 0


def test_unknown_blocks_followup_and_preserves_same_key(bridge):
    prepare_a(bridge)
    first = intent(bridge)
    replay = bridge.fake_intent("A", fake_plan(), 4, "intent_A")
    assert replay["replayed"] and replay["project_revision"] == first["project_revision"]
    bridge.unknown("A", 5, "unknown_A")
    assert bridge.inspect()["budget"]["held_or_charged"] == 1
    assert bridge.public_summary()["pending_or_unknown"]
    with pytest.raises(ContractError):
        bridge.propose_b("candidate_B")
    with pytest.raises(ContractError):
        bridge.fake_intent("A", fake_plan(), 6, "new_key")
    observe(bridge)
    assert bridge.propose_b("candidate_B")["causal"]["a_run_id"] == "run_A"


def test_plan_replay_and_conflict(bridge):
    port = prepare_a(bridge)
    replay = bridge.prepare_a(port, revision=3, key="plan_A", request_key="prepare_A",
                              at_time=101, expires_at=200)
    assert replay["replayed"] and replay["project_revision"] == 4
    with pytest.raises(ContractError, match="IDEMPOTENCY_CONFLICT"):
        bridge.prepare_a(port, revision=3, key="plan_A", request_key="changed_key",
                         at_time=101, expires_at=200)
    with pytest.raises(ContractError, match="PREPARATION_CONTENT_CONFLICT"):
        bridge.prepare_a(port, revision=3, key="plan_A", request_key="prepare_A",
                         at_time=101, expires_at=201)
    with pytest.raises(ContractError, match="PLAN_ALREADY_BOUND"):
        bridge.prepare_a(port, revision=4, key="new_key", request_key="prepare_A",
                         at_time=101, expires_at=200)


@pytest.mark.parametrize("field,value", [("source", "AF_REAL"), ("phase", "B"),
    ("input_digest", sha("different-input")), ("contract_digest", sha("different-contract")),
    ("execution_authorized", True), ("resources_digest", sha("different-resource")),
    ("verification_policy_digest", sha("different-tol")), ("research_revision", True)])
def test_inert_plan_substitution(bridge, field, value):
    bridge.admit(bridge.proposal("A", "1", "candidate_A"), 2, "admit_A")
    class Altered(InertPort):
        def prepare(self, **kwargs):
            super().prepare(**kwargs)
            self.ref[field] = value
            return copy.deepcopy(self.ref)
    with pytest.raises(ContractError):
        bridge.prepare_a(Altered(), revision=3, key="plan_A", request_key="prepare_A",
                         at_time=100, expires_at=200)
    assert bridge.inspect()["budget"]["held_or_charged"] == 0


@pytest.mark.parametrize("part,field,value", [
    ("receipt", "idempotency_key", "different_key"), ("receipt", "run_id", "different_run"),
    ("run", "backend_id", "abaqus-standard"), ("run", "simulation", False),
    ("run", "attempt_no", 2), ("run", "reconciliation", "UNKNOWN"),
    ("run", "plan_digest", sha("wrong-plan")), ("run", "phase_attempt_id", "wrong_attempt")])
def test_wrong_fake_evidence_holds_budget(bridge, part, field, value):
    prepare_a(bridge)
    intent(bridge)
    raw = fake_evidence()
    raw[part][field] = value
    with pytest.raises(ContractError):
        bridge.observe("A", raw, envelope(bridge), 5, "bad")
    assert bridge.inspect()["budget"]["held_or_charged"] == 1


@pytest.mark.parametrize("field,value", [("all_owned_processes_exited", False),
    ("real_solver_executed", True), ("normal_exit", False), ("validations", []), ("events", [])])
def test_missing_cleanup_validation_or_events(bridge, field, value):
    prepare_a(bridge)
    intent(bridge)
    raw = fake_evidence()
    raw[field] = value
    with pytest.raises(ContractError):
        bridge.observe("A", raw, envelope(bridge), 5, "bad")


def test_inconsistent_owner_origin_record_refused(bridge):
    prepare_a(bridge)
    intent(bridge)
    raw = fake_evidence()
    raw["runtime_origin"]["service_path"] = "Q:/different/execution/service.py"
    with pytest.raises(ContractError, match="FAKE_ORIGIN_MISMATCH"):
        bridge.observe("A", raw, envelope(bridge), 5, "bad")


@pytest.mark.parametrize("damage", ["missing_start", "repeated_start", "wrong_order", "backend_unknown"])
def test_fake_execution_sequence_is_not_inferred_from_final_pass(bridge, damage):
    prepare_a(bridge)
    intent(bridge)
    raw = fake_evidence()
    if damage == "missing_start":
        raw["events"] = [e for e in raw["events"] if e["type"] != "START_INTENT"]
    elif damage == "repeated_start":
        raw["events"][2]["type"] = "START_INTENT"
    elif damage == "wrong_order":
        raw["events"][1]["type"], raw["events"][2]["type"] = "FAKE_COMPLETED", "START_INTENT"
    else:
        raw["run"]["backend_outcome"] = "UNKNOWN"
    with pytest.raises(ContractError):
        bridge.observe("A", raw, envelope(bridge), 5, "bad")


def test_v1_and_v2_writes_cannot_mix(bridge):
    prepare_a(bridge)
    with pytest.raises(ContractError, match="PREVIEW_ROUTE_MISMATCH"):
        bridge.preview.mark_unknown("A", 4, "old_route")


def test_concurrent_intents_one_allocation(bridge):
    prepare_a(bridge)
    def writer(index):
        try:
            bridge.fake_intent("A", fake_plan(), 4, "claim_" + str(index))
            return "accepted"
        except (ContractError, store.ProjectError):
            return "refused"
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(writer, range(2))) == ["accepted", "refused"]
    assert bridge.inspect()["budget"]["held_or_charged"] == 1


@pytest.mark.parametrize("stage,committed", [("preview_before_commit", False),
                                          ("preview_after_commit", True)])
def test_transaction_failure_replay(bridge, monkeypatch, stage, committed):
    prepare_a(bridge)
    def fail(at):
        if at == stage:
            raise OSError("UNIT_INJECTED")
    monkeypatch.setattr(rod_preview, "_fault", fail)
    with pytest.raises(store.ProjectError, match="STORE_UNAVAILABLE"):
        intent(bridge)
    monkeypatch.setattr(rod_preview, "_fault", lambda _stage: None)
    assert bridge.inspect()["budget"]["held_or_charged"] == int(committed)
    assert bridge.fake_intent("A", fake_plan(), 4, "intent_A")["replayed"] is committed


def test_independent_process_reopen(bridge):
    prepare_a(bridge)
    intent(bridge)
    bridge.unknown("A", 5, "unknown_A")
    script = (
        "import json,sys;from aegiscae.research.project import open_existing_readonly;"
        "from aegiscae.research.rod_preview import RealPreviewAdapter;"
        "from aegiscae.research.rod_bridge import RodBridge;"
        "print(json.dumps(RodBridge(RealPreviewAdapter(open_existing_readonly(sys.argv[1]))).public_summary()))")
    environment = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[2] / "src")}
    result = subprocess.run([sys.executable, "-B", "-c", script, str(bridge.preview.project._root)],
                            env=environment, capture_output=True, timeout=30, check=False)
    assert result.returncode == 0
    summary = json.loads(result.stdout)
    assert summary["pending_or_unknown"] and summary["budget"]["held_or_charged"] == 1


def test_hard_exit_after_commit_keeps_original_intent(bridge):
    prepare_a(bridge)
    script = (
        "import json,os,sys;from aegiscae.research import rod_preview;"
        "from aegiscae.research.project import open_existing_for_explicit_write;"
        "from aegiscae.research.rod_bridge import RodBridge;"
        "rod_preview._fault=lambda s:os._exit(77) if s=='preview_after_commit' else None;"
        "RodBridge(rod_preview.RealPreviewAdapter(open_existing_for_explicit_write(sys.argv[1])))"
        ".fake_intent('A',json.loads(sys.argv[2]),4,'intent_A')")
    environment = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[2] / "src")}
    result = subprocess.run([sys.executable, "-B", "-c", script,
                             str(bridge.preview.project._root), json.dumps(fake_plan())],
                            env=environment, capture_output=True, timeout=30, check=False)
    assert result.returncode == 77
    assert bridge.inspect()["pending_or_unknown"]
    assert bridge.fake_intent("A", fake_plan(), 4, "intent_A")["replayed"]
    with pytest.raises(ContractError):
        bridge.fake_intent("A", fake_plan(), 5, "retry_key")


def test_idempotency_conflict_and_stale_causal(bridge):
    prepare_a(bridge)
    intent(bridge)
    with pytest.raises(ContractError, match="IDEMPOTENCY_CONFLICT"):
        bridge.fake_intent("A", {**fake_plan(), "request_key": "new"}, 4, "intent_A")
    observe(bridge)
    candidate = bridge.propose_b("candidate_B")
    candidate["causal"]["a_receipt_digest"] = sha("other")
    with pytest.raises(ContractError, match="CAUSAL_EVIDENCE_MISMATCH"):
        bridge.admit(candidate, 6, "bad_B")


def test_rehashed_g2_event_corruption_rejected(bridge):
    import sqlite3
    prepare_a(bridge)
    with sqlite3.connect(bridge.preview.project._root / "research.sqlite3") as db:
        sequence, body = db.execute("SELECT sequence,body FROM audit ORDER BY sequence DESC LIMIT 1").fetchone()
        event = json.loads(body)
        event["workflow"]["data"]["plan_ref"]["input_digest"] = sha("tampered")
        event["metadata_digest"] = digest_bytes(canonical_json(event["workflow"]))
        changed = canonical_json(event)
        db.execute("UPDATE audit SET body=?,digest=? WHERE sequence=?", (changed, digest_bytes(changed), sequence))
    with pytest.raises(store.ProjectError, match="INTEGRITY_ERROR"):
        store.open_existing_readonly(bridge.preview.project._root)
