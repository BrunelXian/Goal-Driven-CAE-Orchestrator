"""G1 offline substitutes only; these values are not Abaqus execution evidence."""

import json
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, replace
from decimal import Decimal
from pathlib import Path
import subprocess
import sys
import sqlite3

import pytest

from aegiscae.contracts.research_contracts import ContractError, canonical_json, digest_bytes
from aegiscae.research import project as store, rod_preview
from aegiscae.research.rod_preview import RealPreviewAdapter, create_preview
from aegiscae.research.rod_preview_rules import (
    BASELINE, SOURCE, TEMPLATE, RodPreviewContract, candidate_bytes, check_candidate,
)

ERRORS = (ContractError, store.ProjectError)


def synthetic_dat(load="1"):
    force = Decimal(load)
    return (
        "Abaqus 2024 Date 30-Oct-2026 Time 12:00:00\n"
        "R010 axial bar a19d17ea - N mm MPa STEP 1 INCREMENT 1\n"
        "S T E P 1 S T A T I C A N A L Y S I S\nINCREMENT 1 SUMMARY\n"
        "TIME INCREMENT COMPLETED 1 , FRACTION OF STEP COMPLETED 1\n"
        "STEP TIME COMPLETED 1 , TOTAL TIME COMPLETED 1\n"
        "THE FOLLOWING TABLE IS PRINTED AT THE INTEGRATION POINTS FOR ELEMENT TYPE T3D2 AND ELEMENT SET\n"
        f"BAR\nELEMENT PT FOOT- S11\nNOTE\n1 1 {force}\n\n"
        "THE FOLLOWING TABLE IS PRINTED FOR ALL NODES\nNODE FOOT- U1 U2 U3\nNOTE\n"
        f"1 0 0 0\n2 {force / 100} 0 0\n\n"
        "THE FOLLOWING TABLE IS PRINTED FOR ALL NODES\nNODE FOOT- RF1 RF2 RF3\nNOTE\n"
        f"1 {-force} 0 0\n2 0 0 0\n\n"
        "THE ANALYSIS HAS BEEN COMPLETED\nANALYSIS COMPLETE\nJOB TIME SUMMARY\n"
        "USER TIME (SEC) = 1\nSYSTEM TIME (SEC) = 0\nTOTAL CPU TIME (SEC) = 1\n"
        "WALLCLOCK TIME (SEC) = 1\n"
    ).encode("ascii")


def proposal(adapter, step="A", load="1"):
    view = adapter.inspect()
    contract = RodPreviewContract.from_dict(view["contract"])
    return {"candidate_id": "candidate_" + step, "step": step, "load_n": load, "unit": "N",
            "input_digest": digest_bytes(candidate_bytes(load, contract)),
            "contract_digest": view["contract_digest"],
            "research_project_id": view["research_project_id"],
            "project_revision": view["project_revision"], "created_at_utc": store._utc(),
            "causal": adapter.causal_reference() if step == "B" else None}


def binding(adapter, step="A"):
    view = adapter.inspect()
    return {"source": SOURCE, "managed_scope": True, "project_id": "af_project_" + step,
            "project_instance_id": "af_instance_" + step,
            "plan_digest": digest_bytes(("plan" + step).encode()),
            "input_digest": view["attempts"][step]["candidate"]["input_digest"],
            "request_key": "request_" + step, "output_identity": "output_" + step,
            "resources_digest": digest_bytes(b"cpu1_memory256_timeout60"),
            "authorization_digest": digest_bytes(("TEST_ONLY_approval" + step).encode()),
            "authorization_kind": "TEST_ONLY", "attempt_allowance": 1}


def observation(adapter, step="A", data=None):
    attempt = adapter.inspect()["attempts"][step]
    data = synthetic_dat(attempt["candidate"]["load_n"]) if data is None else data
    hexadecimal = data.hex()
    return {"binding": attempt["binding"], "run_id": "run_" + step,
            "attempt_id": "attempt_" + step, "receipt_digest": digest_bytes(step.encode()),
            "output_digest": digest_bytes(data), "solver_exit_code": 0, "source": SOURCE,
            "dat_hex_chunks": [hexadecimal[i:i + 1024] for i in range(0, len(hexadecimal), 1024)]}


def advance_intent(adapter, step="A", load="1"):
    raw = proposal(adapter, step, load)
    adapter.admit(raw, adapter.inspect()["project_revision"], "admit_" + step)
    adapter.record_intent(step, binding(adapter, step), adapter.inspect()["project_revision"],
                          "intent_" + step)


def observe(adapter, step="A"):
    return adapter.observe(step, observation(adapter, step), adapter.inspect()["project_revision"],
                           "observe_" + step)


@pytest.fixture
def adapter(tmp_path):
    return create_preview(tmp_path / "new-preview", "Offline G1", RodPreviewContract())


def test_offline_chain_and_independent_reopen(adapter):
    assert digest_bytes(TEMPLATE) == BASELINE
    advance_intent(adapter)
    first = observe(adapter)
    assert first["attempts"]["A"]["decision"]["V3"] == "NOT_SATISFIED"
    # Derive B from measured A, never put a fixed candidate B in the contract.
    measured = Decimal(first["attempts"]["A"]["decision"]["displacement_mm"])
    target = (Decimal(first["contract"]["goal_min_mm"]) +
              Decimal(first["contract"]["goal_max_mm"])) / 2
    proposed_load = str(Decimal("1") * target / measured)
    advance_intent(adapter, "B", proposed_load)
    final = observe(adapter, "B")
    assert final["attempts"]["B"]["decision"]["V3"] == "SATISFIED"
    assert final["real_goal"] == "INCONCLUSIVE" and not final["execution_authorized"]
    assert final["budget"] == {"maximum": 2, "held_or_charged": 2, "available": 0}
    assert final["attempts"]["B"]["decision"]["V4"] == "NOT_ASSESSED"
    assert final["attempts"]["B"]["decision"]["ODB"] == "NOT_VERIFIED"
    reopened = RealPreviewAdapter(store.open_existing_readonly(adapter.project._root))
    assert reopened.inspect() == {k: v for k, v in final.items() if k != "replayed"}


@pytest.mark.parametrize("load", ["NaN", "Infinity", "-Infinity", "1e0", "01", "0", "2.6",
                                  "0.49", "1\n*INCLUDE", "1;command", 1, True])
def test_invalid_loads(load):
    with pytest.raises(ContractError):
        candidate_bytes(load, RodPreviewContract())


@pytest.mark.parametrize("before,after", [(b"1000,0.3", b"999,0.3"),
    (b"1,1,3,0", b"1,1,2,0"), (b"*STEP", b"*STEP, NLGEOM=YES"),
    (b"2,1,1", b"1,1,1"), (b"*END STEP", b"*INCLUDE, INPUT=secret.inp\n*END STEP")])
def test_only_allowed_token_can_change(before, after):
    with pytest.raises(ContractError, match="MODEL_MUTATION_REJECTED"):
        check_candidate(TEMPLATE.replace(before, after), "1", RodPreviewContract())


@pytest.mark.parametrize("field,value", [("max_solver_calls", 3), ("max_solver_calls", True),
    ("units", "N_m_Pa"), ("target_entity", "node1_U1_step1_increment1"),
    ("displacement_tolerance_mm", "0.01"), ("baseline_digest", "sha256:" + "0" * 64),
    ("evidence_mode", "AF_REAL"), ("required_v4", True), ("required_odb", True)])
def test_invalid_frozen_contract(field, value):
    with pytest.raises(ContractError):
        RodPreviewContract.from_dict(asdict(replace(RodPreviewContract(), **{field: value})))


def test_schema1_is_unchanged_and_cannot_be_used(tmp_path):
    old = store.create_research_project(tmp_path / "synthetic", "Old")
    assert old.inspect()["schema_version"] == 1
    with pytest.raises(ContractError, match="PREVIEW_SCHEMA_REQUIRED"):
        RealPreviewAdapter(old).inspect()


def test_read_only_cannot_mutate(adapter):
    reader = RealPreviewAdapter(store.open_existing_readonly(adapter.project._root))
    with pytest.raises(store.ProjectError, match="READ_ONLY"):
        reader.admit(proposal(adapter), 2, "admit")


def test_duplicate_conflict_and_revision(adapter):
    raw = proposal(adapter)
    first = adapter.admit(raw, 2, "admit")
    replay = adapter.admit(raw, 2, "admit")
    assert replay["replayed"] and first["project_revision"] == replay["project_revision"]
    with pytest.raises(ContractError, match="IDEMPOTENCY_CONFLICT"):
        adapter.admit({**raw, "load_n": "2"}, 2, "admit")
    with pytest.raises(ContractError, match="REVISION_CONFLICT"):
        adapter.record_intent("A", binding(adapter), 2, "intent")


def test_unknown_holds_budget_and_blocks_b_and_new_intent(adapter):
    advance_intent(adapter)
    adapter.mark_unknown("A", 4, "unknown")
    reopened = RealPreviewAdapter(store.open_existing_for_explicit_write(adapter.project._root))
    assert reopened.inspect()["budget"]["held_or_charged"] == 1
    with pytest.raises(ContractError, match="A_NOT_ELIGIBLE"):
        reopened.causal_reference()
    with pytest.raises(ContractError, match="INTENT_ALREADY_RECORDED"):
        reopened.record_intent("A", binding(adapter), 5, "retry")
    assert observe(reopened)["attempts"]["A"]["status"] == "OBSERVED"


@pytest.mark.parametrize("field,value", [("source", "AF_REAL"), ("managed_scope", False),
    ("authorization_kind", "REAL"), ("attempt_allowance", 2), ("request_key", "fake_request"),
    ("output_identity", "../outside"), ("input_digest", "sha256:" + "0" * 64)])
def test_invalid_plan_approval_boundary(adapter, field, value):
    adapter.admit(proposal(adapter), 2, "admit")
    with pytest.raises(ContractError):
        adapter.record_intent("A", {**binding(adapter), field: value}, 3, "intent")
    assert adapter.inspect()["budget"]["held_or_charged"] == 0


@pytest.mark.parametrize("before,after", [(b"2 0.01 0 0", b"2 10 0 0"),
    (b"2 0.01 0 0", b"3 0.01 0 0"), (b"1 1 1", b"1 2 1"),
    (b"1 -1 0 0", b"1 1 0 0"), (b"2 0 0 0\n\nTHE ANALYSIS", b"\nTHE ANALYSIS"),
    (b"STEP 1 INCREMENT 1", b"STEP 2 INCREMENT 1"),
    (b"N mm MPa", b"N m Pa"), (b"2 0.01 0 0", b"2 NaN 0 0"),
    (b"THE ANALYSIS HAS BEEN COMPLETED", b"THE ANALYSIS HAS NOT BEEN COMPLETED"),
    (b"WALLCLOCK TIME (SEC) = 1", b"")])
def test_bad_dat_does_not_advance_or_release_budget(adapter, before, after):
    advance_intent(adapter)
    with pytest.raises(ContractError):
        adapter.observe("A", observation(adapter, data=synthetic_dat().replace(before, after)),
                        4, "bad-data")
    assert adapter.inspect()["attempts"]["A"]["status"] == "INTENT"


@pytest.mark.parametrize("field,value", [("source", "AF_REAL"), ("solver_exit_code", 1),
    ("output_digest", "sha256:" + "0" * 64)])
def test_wrong_evidence(adapter, field, value):
    advance_intent(adapter)
    with pytest.raises(ContractError):
        adapter.observe("A", {**observation(adapter), field: value}, 4, "bad")


def test_wrong_plan_and_false_reviewer_pass_rejected(adapter):
    advance_intent(adapter)
    raw = observation(adapter)
    raw["binding"] = {**raw["binding"], "project_id": "different"}
    with pytest.raises(ContractError, match="EVIDENCE_BINDING_MISMATCH"):
        adapter.observe("A", raw, 4, "wrong")
    with pytest.raises(ContractError, match="INVALID_PREVIEW_FIELDS"):
        adapter.observe("A", {**observation(adapter), "reviewer_pass": True}, 4, "pass")


@pytest.mark.parametrize("mutation", ["metric", "run", "goal", "revision", "time"])
def test_stale_or_substituted_causal_evidence(adapter, mutation):
    advance_intent(adapter)
    observe(adapter)
    raw = proposal(adapter, "B", "2")
    if mutation == "metric":
        raw["causal"]["a_metric_mm"] = "0.02"
    elif mutation == "run":
        raw["causal"]["a_run_id"] = "run_other"
    elif mutation == "goal":
        raw["contract_digest"] = "sha256:" + "0" * 64
    elif mutation == "revision":
        raw["project_revision"] -= 1
    else:
        raw["created_at_utc"] = "2020-01-01T00:00:00.000000Z"
    with pytest.raises(ContractError):
        adapter.admit(raw, 5, "bad-b")


def test_satisfied_a_prevents_b(adapter):
    advance_intent(adapter, load="2")
    observe(adapter)
    with pytest.raises(ContractError, match="A_NOT_ELIGIBLE"):
        adapter.causal_reference()


def test_old_a_artifact_cannot_be_b(adapter):
    advance_intent(adapter)
    observe(adapter)
    advance_intent(adapter, "B", "2")
    with pytest.raises(ContractError, match="OLD_OUTPUT_REUSED"):
        adapter.observe("B", observation(adapter, "B", synthetic_dat("1")), 7, "bad-b")


@pytest.mark.parametrize("stage,committed", [("preview_before_commit", False),
                                           ("preview_after_commit", True)])
def test_transaction_fault_and_lost_response(adapter, monkeypatch, stage, committed):
    raw = proposal(adapter)

    def fail(current):
        if current == stage:
            raise RuntimeError("INJECTED_OFFLINE_FAILURE")

    monkeypatch.setattr(rod_preview, "_fault", fail)
    with pytest.raises(RuntimeError):
        adapter.admit(raw, 2, "admit")
    monkeypatch.setattr(rod_preview, "_fault", lambda _: None)
    reopened = RealPreviewAdapter(store.open_existing_for_explicit_write(adapter.project._root))
    assert ("A" in reopened.inspect()["attempts"]) is committed
    assert reopened.admit(raw, 2, "admit")["replayed"] is committed


def test_concurrent_same_intent_charges_once(adapter):
    adapter.admit(proposal(adapter), 2, "admit")
    exact = binding(adapter)

    def work(_):
        try:
            client = RealPreviewAdapter(store.open_existing_for_explicit_write(adapter.project._root))
            return client.record_intent("A", exact, 3, "one-intent")["replayed"]
        except store.ProjectError as exc:
            assert exc.code == "STORE_BUSY"
            return "busy"

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(work, range(2)))
    assert False in results and adapter.inspect()["budget"]["held_or_charged"] == 1


def test_independent_process_reopen_unknown(adapter):
    advance_intent(adapter)
    adapter.mark_unknown("A", 4, "unknown")
    script = (
        "import json,sys; from aegiscae.research.project import open_existing_readonly; "
        "from aegiscae.research.rod_preview import RealPreviewAdapter; "
        "v=RealPreviewAdapter(open_existing_readonly(sys.argv[1])).inspect(); "
        "print(json.dumps({'held':v['budget']['held_or_charged'],"
        "'pending':v['pending_or_unknown'],'real_goal':v['real_goal']}))"
    )
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[2] / "src")}
    result = subprocess.run([sys.executable, "-B", "-c", script, str(adapter.project._root)],
                            env=env, capture_output=True, timeout=30, check=False)
    assert result.returncode == 0
    assert json.loads(result.stdout) == {"held": 1, "pending": True, "real_goal": "INCONCLUSIVE"}


def _child_environment():
    return {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[2] / "src")}


def test_hard_exit_after_intent_preserves_claim_and_budget(adapter):
    adapter.admit(proposal(adapter), 2, "admit")
    script = (
        "import json,os,sys; from aegiscae.research import rod_preview; "
        "from aegiscae.research.project import open_existing_for_explicit_write; "
        "rod_preview._fault=lambda s: os._exit(77) if s=='preview_after_commit' else None; "
        "rod_preview.RealPreviewAdapter(open_existing_for_explicit_write(sys.argv[1]))"
        ".record_intent('A',json.loads(sys.argv[2]),3,'intent')"
    )
    result = subprocess.run([sys.executable, "-B", "-c", script, str(adapter.project._root),
                             json.dumps(binding(adapter))], env=_child_environment(),
                            capture_output=True, timeout=30, check=False)
    assert result.returncode == 77
    fresh = RealPreviewAdapter(store.open_existing_for_explicit_write(adapter.project._root))
    assert fresh.inspect()["pending_or_unknown"]
    assert fresh.inspect()["budget"]["held_or_charged"] == 1
    assert fresh.record_intent("A", binding(adapter), 3, "intent")["replayed"]
    with pytest.raises(ContractError, match="INTENT_ALREADY_RECORDED"):
        fresh.record_intent("A", binding(adapter), 4, "new-key")


def test_two_processes_compete_for_one_intent(adapter):
    adapter.admit(proposal(adapter), 2, "admit")
    script = """
import json,sys
from aegiscae.research.rod_preview import RealPreviewAdapter
from aegiscae.research.project import open_existing_for_explicit_write,ProjectError
from aegiscae.contracts.research_contracts import ContractError
try:
    a=RealPreviewAdapter(open_existing_for_explicit_write(sys.argv[1]))
    a.record_intent('A',json.loads(sys.argv[2]),3,sys.argv[3])
except ProjectError as e:
    sys.exit(10 if e.code == 'STORE_BUSY' else 99)
except ContractError as e:
    sys.exit(11 if e.code == 'REVISION_CONFLICT' else 98)
"""
    commands = [[sys.executable, "-B", "-c", script, str(adapter.project._root),
                 json.dumps(binding(adapter)), "claim_" + str(i)] for i in range(2)]
    children = [subprocess.Popen(command, env=_child_environment(),
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                for command in commands]
    for child in children:
        child.communicate(timeout=30)
    codes = [child.returncode for child in children]
    assert codes.count(0) == 1 and all(code in (0, 10, 11) for code in codes)
    assert adapter.inspect()["budget"]["held_or_charged"] == 1


def test_rehashed_tampered_semantics_rejected(adapter):
    adapter.admit(proposal(adapter), 2, "admit")
    with sqlite3.connect(adapter.project._root / "research.sqlite3") as db:
        sequence, body = db.execute("SELECT sequence,body FROM audit ORDER BY sequence DESC LIMIT 1").fetchone()
        event = json.loads(body)
        event["workflow"]["data"]["load_n"] = "2"
        event["metadata_digest"] = digest_bytes(canonical_json(event["workflow"]))
        changed = canonical_json(event)
        db.execute("UPDATE audit SET body=?,digest=? WHERE sequence=?",
                   (changed, digest_bytes(changed), sequence))
    with pytest.raises(store.ProjectError, match="INTEGRITY_ERROR"):
        store.open_existing_readonly(adapter.project._root)


def test_offline_labels_and_declared_grant_do_not_establish_real_authority(adapter):
    advance_intent(adapter)
    final = observe(adapter)
    assert final["human_approval"] == "NOT_ESTABLISHED"
    assert final["hil_isolation"] == "BLOCKED_HIL_STRONG_ISOLATION"
    assert final["live_dispatch"] == "BLOCKED_LIVE_DISPATCH_UNREGISTERED"
    assert final["real_goal"] == "INCONCLUSIVE"
    assert final["attempts"]["A"]["decision"]["real_goal"] == "INCONCLUSIVE"
    assert not hasattr(adapter, "submit") and not hasattr(adapter, "dispatch")
    assert not hasattr(adapter, "authorize")


def test_distinct_frozen_goal_changes_derived_proposal(tmp_path):
    proposed = []
    for index, bounds in enumerate((("0.019", "0.021"), ("0.014", "0.016"))):
        adapter = create_preview(tmp_path / ("case" + str(index)), "Offline goal variation",
            replace(RodPreviewContract(), goal_min_mm=bounds[0], goal_max_mm=bounds[1]))
        advance_intent(adapter)
        state = observe(adapter)
        metric = Decimal(state["attempts"]["A"]["decision"]["displacement_mm"])
        load = str((Decimal(bounds[0]) + Decimal(bounds[1])) / 2 / metric)
        raw = proposal(adapter, "B", load)
        adapter.admit(raw, state["project_revision"], "admit-b")
        proposed.append(raw["input_digest"])
    assert proposed[0] != proposed[1]


def test_canonical_decimal_matches_exact_artifact():
    contract = RodPreviewContract()
    assert candidate_bytes("1", contract) == candidate_bytes("1.0", contract) == TEMPLATE
    assert candidate_bytes("2", contract) == candidate_bytes("2.00", contract)
    assert b"2,1,1.000000000000000000000000001\n" in candidate_bytes(
        "1.000000000000000000000000001", contract)


def test_existing_project_is_not_migrated(tmp_path):
    root = tmp_path / "old"
    store.create_research_project(root, "Original")
    before = (root / "research.sqlite3").read_bytes()
    with pytest.raises(store.ProjectError, match="ROOT_EXISTS"):
        create_preview(root, "New", RodPreviewContract())
    assert (root / "research.sqlite3").read_bytes() == before


def test_no_third_attempt_or_reused_af_project(adapter):
    advance_intent(adapter)
    observe(adapter)
    raw = proposal(adapter, "B", "2")
    adapter.admit(raw, 5, "admit-b")
    duplicate = binding(adapter, "B")
    duplicate["project_id"] = binding(adapter, "A")["project_id"]
    with pytest.raises(ContractError, match="ATTEMPT_IDENTITY_REUSED"):
        adapter.record_intent("B", duplicate, 6, "reuse-project")
    adapter.record_intent("B", binding(adapter, "B"), 6, "intent-b")
    observe(adapter, "B")
    with pytest.raises(ContractError, match="ATTEMPT_EXISTS"):
        adapter.admit({**raw, "step": "C"}, 8, "third-attempt")


@pytest.mark.parametrize("preview,new_schema", [(False, 2), (True, 1)])
def test_creation_schema_cannot_be_changed_by_rehashing_metadata(tmp_path, preview, new_schema):
    root = tmp_path / "schema-identity"
    store.create_research_project(root, "Schema identity", rod_preview=preview)
    with sqlite3.connect(root / "research.sqlite3") as db:
        body = db.execute("SELECT body FROM project").fetchone()[0]
        meta = json.loads(body)
        meta["schema_version"] = new_schema
        encoded = canonical_json(meta)
        db.execute("UPDATE project SET body=?,digest=? WHERE singleton=1",
                   (encoded, digest_bytes(encoded)))
    with pytest.raises(store.ProjectError, match="INTEGRITY_ERROR"):
        store.open_existing_readonly(root)


@pytest.mark.parametrize("mutation", ["remove", "wrong_type", "wrong_value"])
def test_preview_creation_marker_is_mandatory_and_exact(tmp_path, mutation):
    root = tmp_path / "creation-marker"
    store.create_research_project(root, "Creation marker", rod_preview=True)
    with sqlite3.connect(root / "research.sqlite3") as db:
        body = db.execute("SELECT body FROM audit WHERE sequence=1").fetchone()[0]
        event = json.loads(body)
        if mutation == "remove":
            del event["creation_schema"]
        else:
            event["creation_schema"] = "2" if mutation == "wrong_type" else 1
        encoded = canonical_json(event)
        db.execute("UPDATE audit SET body=?,digest=? WHERE sequence=1",
                   (encoded, digest_bytes(encoded)))
    with pytest.raises(store.ProjectError, match="INTEGRITY_ERROR"):
        store.open_existing_readonly(root)
