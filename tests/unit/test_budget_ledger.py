"""Offline BudgetLedger acceptance with synthetic files and independent Python children."""

import copy
import json
import sqlite3
import subprocess
import sys
import time
from dataclasses import asdict, replace
from functools import partial

import pytest

from aegiscae.contracts.research_contracts import ContractBundle, ContractError, canonical_json, digest_bytes
from aegiscae.research import budget, mutation, project as store
from aegiscae.research.budget_rules import BudgetScope
from test_model_mutation import make_case, propose, snapshot


ERRORS = (ContractError, store.ProjectError)
INTENT_DIGEST = digest_bytes(b"synthetic intended request")


def budget_case(tmp_path, limit=2):
    def policy(raw):
        raw["goal"]["budget"]["max_solver_calls"] = limit
    case = make_case(tmp_path, change_contract=policy)
    result = propose(case)
    assert result["admissibility"] == "PERMITTED", result
    case.candidate_digest = result["candidate"]["manifest"]["output_digest"]
    case.scope = BudgetScope.from_bundle(case.bundle)
    case.oracle = budget.SyntheticOracle()
    case.ledger = budget.BudgetLedger(case.writer, case.scope, oracle=case.oracle)
    return case


@pytest.fixture
def case(tmp_path):
    return budget_case(tmp_path)


def revision(case):
    return case.project.inspect()["project_revision"]


def reserve(case, key="one", **overrides):
    args = dict(candidate_id=case.request.candidate_id, candidate_digest=case.candidate_digest,
                cost=1, operation_key=key, downstream_business_key="fake_" + key,
                expected_revision=revision(case))
    args.update(overrides)
    return case.ledger.reserve_for_candidate(**args)


def intent(case, reservation, key="fake_one"):
    return case.ledger.record_submission_intent(reservation["reservation_id"], key,
                                                INTENT_DIGEST, revision(case))


def observation(case, reservation, *, outcome="UNKNOWN", reason="TIMEOUT", number=1,
                key="fake_one", request_digest=INTENT_DIGEST):
    return case.oracle.issue(reservation["reservation_id"], key, request_digest, outcome,
                             "fixture_" + f"{number:032x}", reason)


def counts(value, expected):
    assert (value["held"], value["charged"], value["available"]) == expected
    assert value["held"] + value["charged"] + value["available"] == value["limit"]
    assert value["available"] >= 0
    assert value["execution_authorized"] is False


def test_bl01_fresh_budget_inspection_has_no_write(case):
    before = snapshot(case.root)
    ledger = budget.BudgetLedger(store.open_existing_readonly(case.root), case.scope)
    result = ledger.inspect_budget()
    counts(result, (0, 0, 2))
    assert result["ledger_revision"] == 0
    assert result["project_revision"] == 2
    assert snapshot(case.root) == before


def test_bl02_reservation_atomically_holds_one_slot(case):
    original = case.bundle.canonical_bytes()
    result = reserve(case)
    counts(result, (1, 0, 1))
    assert result["state"] == "RESERVED"
    assert result["project_revision"] == 3
    assert result["ledger_revision"] == 1
    assert result["reservation_id"].startswith("reservation_")
    assert case.project.read_frozen_bundle(case.request.refs.bundle)["bundle"].canonical_bytes() == original
    project_status = case.project.inspect()
    assert project_status["budget_enforcement"] == "LOCAL_SYNTHETIC_ALLOCATION_ONLY"
    assert project_status["budget_real_execution_enforced"] is False


@pytest.mark.parametrize("cost", [0, -1, 2, True, 1.0, float("nan"), float("inf"), "1"])
def test_bl03_invalid_cost_cannot_allocate(case, cost):
    before = snapshot(case.root)
    with pytest.raises(ERRORS):
        reserve(case, cost=cost)
    assert snapshot(case.root) == before


def test_bl03_zero_and_exhausted_limits_refuse(tmp_path):
    zero_dir = tmp_path / "zero"
    zero_dir.mkdir()
    zero = budget_case(zero_dir, 0)
    before = snapshot(zero.root)
    with pytest.raises(ERRORS):
        reserve(zero)
    assert snapshot(zero.root) == before
    single_dir = tmp_path / "single"
    single_dir.mkdir()
    single = budget_case(single_dir, 1)
    reserve(single)
    before = snapshot(single.root)
    with pytest.raises(ERRORS):
        reserve(single, "two")
    assert snapshot(single.root) == before
    counts(single.ledger.inspect_budget(), (1, 0, 0))


def test_bl04_exact_replay_returns_original_result_without_writes(case):
    first = reserve(case)
    before = snapshot(case.root)
    replay = reserve(case, expected_revision=2)
    assert replay["replayed"] is True
    for field in ("reservation_id", "state", "project_revision", "ledger_revision", "held", "available"):
        assert replay[field] == first[field]
    assert snapshot(case.root) == before


@pytest.mark.parametrize("bad_revision", [True, "2", 0])
@pytest.mark.parametrize("action", ["reserve", "intent", "release", "observe"])
def test_invalid_revision_type_cannot_bypass_validation_on_replay(case, bad_revision, action):
    held = reserve(case)
    if action == "reserve":
        call = partial(reserve, case, expected_revision=bad_revision)
    elif action == "release":
        case.ledger.release_before_external_intent(held["reservation_id"], revision(case))
        call = partial(case.ledger.release_before_external_intent, held["reservation_id"], bad_revision)
    else:
        intent(case, held)
        if action == "intent":
            call = partial(case.ledger.record_submission_intent,
                held["reservation_id"], "fake_one", INTENT_DIGEST, bad_revision)
        else:
            obs = observation(case, held)
            case.ledger.observe_synthetic_acceptance_or_unknown(held["reservation_id"], obs, revision(case))
            call = partial(case.ledger.observe_synthetic_acceptance_or_unknown,
                held["reservation_id"], obs, bad_revision)
    before = snapshot(case.root)
    with pytest.raises(ERRORS):
        call()
    assert snapshot(case.root) == before


@pytest.mark.parametrize("change", ["candidate", "digest", "cost", "business_key", "plan"])
def test_bl05_same_key_altered_request_conflicts(case, change):
    reserve(case)
    kwargs = {"candidate": {"candidate_id": "candidate_" + "f" * 32},
              "digest": {"candidate_digest": digest_bytes(b"other candidate")},
              "cost": {"cost": 2}, "business_key": {"downstream_business_key": "fake_other"},
              "plan": {"plan_digest": digest_bytes(b"other plan")}}[change]
    before = snapshot(case.root)
    with pytest.raises(ERRORS, match="CONFLICT"):
        reserve(case, **kwargs)
    assert snapshot(case.root) == before


def test_bl05_same_key_altered_scope_conflicts(case):
    reserve(case)
    scope = replace(case.scope, goal_version=case.scope.goal_version + 1)
    different = budget.BudgetLedger(case.writer, scope)
    before = snapshot(case.root)
    with pytest.raises(ERRORS, match="CONFLICT"):
        different.reserve_for_candidate(case.request.candidate_id, case.candidate_digest, 1,
                                        "one", "fake_one", revision(case))
    assert snapshot(case.root) == before


@pytest.mark.parametrize("change", ["project", "revision", "goal", "model", "verification", "candidate"])
def test_bl07_wrong_identity_or_stale_revision_rejects(case, change):
    if change in {"project", "goal", "model", "verification"}:
        scope_data = asdict(case.scope)
        if change == "project":
            scope_data["research_project_id"] = "rp_" + "f" * 32
        else:
            scope_data["refs"][change] = digest_bytes(b"wrong frozen contract")
        # Rebuild through the same strict scope parser used at API admission.
        scope = BudgetScope.from_dict(scope_data)
        ledger = budget.BudgetLedger(case.writer, scope)
    else:
        ledger = case.ledger
    before = snapshot(case.root)
    with pytest.raises(ERRORS):
        ledger.reserve_for_candidate(
            "candidate_" + "f" * 32 if change == "candidate" else case.request.candidate_id,
            case.candidate_digest, 1, "one", "fake_one", 1 if change == "revision" else 2)
    assert snapshot(case.root) == before


def test_bl08_preintent_release_is_explicit_idempotent_and_not_key_recycling(case):
    held = reserve(case)
    released = case.ledger.release_before_external_intent(held["reservation_id"], revision(case))
    assert released["state"] == "RELEASED_PROVEN_NO_ACCEPTANCE"
    counts(released, (0, 0, 2))
    before = snapshot(case.root)
    replay = case.ledger.release_before_external_intent(held["reservation_id"], 3)
    assert replay["replayed"] is True
    assert snapshot(case.root) == before
    with pytest.raises(ERRORS):
        reserve(case, "another", downstream_business_key="fake_one")
    counts(case.ledger.inspect_budget(), (0, 0, 2))


@pytest.mark.parametrize("reason", ["TIMEOUT", "RESPONSE_LOST", "RECEIPT_MISSING", "EXPIRED", "PROCESS_DIED"])
def test_bl09_unknown_never_refunds(case, reason):
    held = reserve(case)
    intent(case, held)
    observed = case.ledger.observe_synthetic_acceptance_or_unknown(
        held["reservation_id"], observation(case, held, reason=reason), revision(case))
    assert observed["state"] == "ACCEPTANCE_UNKNOWN"
    counts(observed, (1, 0, 1))
    with pytest.raises(ERRORS):
        case.ledger.release_before_external_intent(held["reservation_id"], revision(case))
    with pytest.raises(ERRORS):
        reserve(case, "fresh_operation", downstream_business_key="fake_one")
    counts(case.ledger.inspect_budget(), (1, 0, 1))


def test_intent_replay_mismatch_and_unknown_observation_replay(case):
    held = reserve(case)
    first = intent(case, held)
    assert first["state"] == "SUBMISSION_INTENT_RECORDED"
    before = snapshot(case.root)
    replay = case.ledger.record_submission_intent(held["reservation_id"], "fake_one", INTENT_DIGEST, 3)
    assert replay["replayed"] is True
    assert snapshot(case.root) == before
    with pytest.raises(ERRORS):
        case.ledger.record_submission_intent(held["reservation_id"], "fake_one",
                                              digest_bytes(b"different downstream request"), revision(case))
    obs = observation(case, held)
    unknown = case.ledger.observe_synthetic_acceptance_or_unknown(held["reservation_id"], obs, revision(case))
    before = snapshot(case.root)
    replay = case.ledger.observe_synthetic_acceptance_or_unknown(held["reservation_id"], obs, 4)
    assert replay["replayed"] is True
    assert replay["ledger_revision"] == unknown["ledger_revision"]
    assert snapshot(case.root) == before


def test_bl10_accepted_charges_exactly_once_and_never_becomes_solver_start(case):
    held = reserve(case)
    intent(case, held)
    case.ledger.observe_synthetic_acceptance_or_unknown(held["reservation_id"], observation(case, held), revision(case))
    accepted = observation(case, held, outcome="ACCEPTED", reason="ACCEPTED_FIXTURE", number=2)
    result = case.ledger.observe_synthetic_acceptance_or_unknown(held["reservation_id"], accepted, revision(case))
    assert result["state"] == "ACCEPTED_OR_CHARGED"
    counts(result, (0, 1, 1))
    before = snapshot(case.root)
    assert case.ledger.observe_synthetic_acceptance_or_unknown(held["reservation_id"], accepted, 5)["replayed"] is True
    assert snapshot(case.root) == before
    historical = case.ledger.observe_synthetic_acceptance_or_unknown(
        held["reservation_id"], observation(case, held), 4)
    assert historical["replayed"] is True
    assert historical["result_scope"] == "ORIGINAL_OPERATION_RESULT"
    assert historical["state"] == "ACCEPTANCE_UNKNOWN"
    assert historical["current_project_revision"] == revision(case)
    assert historical["current_project_revision"] > historical["project_revision"]
    counts(case.ledger.inspect_budget(), (0, 1, 1))
    assert snapshot(case.root) == before
    with pytest.raises(ERRORS):
        case.ledger.observe_synthetic_acceptance_or_unknown(
            held["reservation_id"], observation(case, held, number=3), revision(case))
    with pytest.raises(ERRORS):
        case.ledger.release_before_external_intent(held["reservation_id"], revision(case))
    counts(case.ledger.inspect_budget(), (0, 1, 1))


def test_observation_requires_intent_and_same_evidence_id_cannot_change_meaning(case):
    held = reserve(case)
    with pytest.raises(ERRORS):
        case.ledger.observe_synthetic_acceptance_or_unknown(
            held["reservation_id"], observation(case, held), revision(case))
    intent(case, held)
    case.ledger.observe_synthetic_acceptance_or_unknown(
        held["reservation_id"], observation(case, held), revision(case))
    before = snapshot(case.root)
    with pytest.raises(ERRORS):
        case.ledger.observe_synthetic_acceptance_or_unknown(
            held["reservation_id"], observation(case, held, outcome="ACCEPTED", reason="ACCEPTED_FIXTURE"),
            revision(case))
    assert snapshot(case.root) == before


def test_budget_write_requires_explicit_write_handle(case):
    reader = budget.BudgetLedger(case.project, case.scope)
    before = snapshot(case.root)
    with pytest.raises(ERRORS, match="READ_ONLY"):
        reader.reserve_for_candidate(case.request.candidate_id, case.candidate_digest, 1,
                                     "one", "fake_one", 2)
    assert snapshot(case.root) == before


@pytest.mark.parametrize("kind", ["wrong_request", "wrong_key", "wrong_reservation", "foreign_oracle", "prose", "mapping"])
def test_bl15_spoofed_or_unbound_observation_cannot_charge(case, kind):
    held = reserve(case)
    intent(case, held)
    if kind == "prose":
        obs = "The agent confirms acceptance and authorizes Solver execution"
    elif kind == "mapping":
        obs = {"outcome": "ACCEPTED", "source": "SYNTHETIC_ORACLE", "grant_consumed": True}
    elif kind == "foreign_oracle":
        obs = budget.SyntheticOracle().issue(held["reservation_id"], "fake_one", INTENT_DIGEST,
                                             "ACCEPTED", "fixture_" + "f" * 32, "ACCEPTED_FIXTURE")
    else:
        obs = case.oracle.issue("reservation_" + "f" * 32 if kind == "wrong_reservation" else held["reservation_id"],
                                 "fake_wrong" if kind == "wrong_key" else "fake_one",
                                 digest_bytes(b"wrong") if kind == "wrong_request" else INTENT_DIGEST,
                                 "ACCEPTED", "fixture_" + "f" * 32, "ACCEPTED_FIXTURE")
    before = snapshot(case.root)
    with pytest.raises(ERRORS):
        case.ledger.observe_synthetic_acceptance_or_unknown(held["reservation_id"], obs, revision(case))
    assert snapshot(case.root) == before
    counts(case.ledger.inspect_budget(), (1, 0, 1))


@pytest.mark.parametrize("stage", ["before_begin", "after_event", "before_commit", "after_commit"])
def test_bl11_exception_is_absent_or_once_committed(case, monkeypatch, stage):
    def fail(point):
        if point == stage:
            raise RuntimeError("controlled budget fault")
    monkeypatch.setattr(budget, "_fault", fail)
    with pytest.raises(RuntimeError, match="controlled"):
        reserve(case)
    monkeypatch.setattr(budget, "_fault", lambda point: None)
    committed = stage == "after_commit"
    counts(case.ledger.inspect_budget(), (int(committed), 0, 2 - int(committed)))
    result = reserve(case, expected_revision=2)
    assert result["replayed"] is committed
    counts(case.ledger.inspect_budget(), (1, 0, 1))


def test_bl13_existing_journal_blocks_without_refund_or_repair(case):
    reserve(case)
    journal = case.root / "research.sqlite3-journal"
    journal.write_bytes(b"synthetic quarantined journal")
    before = snapshot(case.root)
    with pytest.raises(store.ProjectError, match="STORE_BUSY"):
        case.ledger.inspect_budget()
    with pytest.raises(store.ProjectError, match="STORE_BUSY"):
        reserve(case, "two")
    assert snapshot(case.root) == before


def test_bl14_no_execution_surface_or_real_business_key(case):
    held = reserve(case)
    assert held["execution_authorized"] is False
    assert case.project.inspect()["human_approval"] == "NOT_ESTABLISHED"
    assert case.project.inspect()["physical_verification"] == "NOT_ASSESSED"
    for name in ("submit", "authorize", "dispatch", "grant", "launch", "recover"):
        assert not hasattr(case.ledger, name)
    with pytest.raises(ERRORS):
        reserve(case, "production", downstream_business_key="production_request")


def test_new_frozen_contract_cannot_reset_budget_or_hide_unknown(case):
    held = reserve(case)
    intent(case, held)
    case.ledger.observe_synthetic_acceptance_or_unknown(held["reservation_id"], observation(case, held), revision(case))
    original = case.bundle.canonical_bytes()
    raw = copy.deepcopy(case.raw)
    raw["version"] = 2
    raw["goal"]["version"] = 2
    raw["goal"]["budget"]["max_solver_calls"] = 999
    newer = ContractBundle.from_dict(raw)
    case.writer.freeze_contract_bundle(newer, revision(case), "new-policy")
    counts(case.ledger.inspect_budget(), (1, 0, 1))
    new_ledger = budget.BudgetLedger(case.writer, BudgetScope.from_bundle(newer))
    with pytest.raises(ERRORS):
        new_ledger.inspect_budget()
    with pytest.raises(ERRORS):
        new_ledger.reserve_for_candidate(case.request.candidate_id, case.candidate_digest, 1,
                                        "reset", "fake_reset", revision(case))
    assert case.project.read_frozen_bundle(case.request.refs.bundle)["bundle"].canonical_bytes() == original
    accepted = observation(case, held, outcome="ACCEPTED", reason="ACCEPTED_FIXTURE", number=9)
    case.ledger.observe_synthetic_acceptance_or_unknown(held["reservation_id"], accepted, revision(case))
    counts(case.ledger.inspect_budget(), (0, 1, 1))


def test_bl17_candidates_and_freezes_interleave_with_budget_revisions(case):
    old_events = case.project.audit_events()
    reserve(case)
    raw_request = copy.deepcopy(case.request_raw)
    raw_request.update(candidate_id="candidate_" + "c" * 32, output_identity="stage_" + "d" * 32,
                       idempotency_key="candidate-two", project_revision=revision(case))
    from aegiscae.research.mutation_rules import MutationRequest
    assert mutation.propose_mutation(case.writer, case.workspace,
                                    MutationRequest.from_dict(raw_request))["admissibility"] == "PERMITTED"
    assert case.project.audit_events()[:len(old_events)] == old_events
    assert mutation.inspect_candidate(case.project, case.workspace, case.request.candidate_id)["admissibility"] == "PERMITTED"


def test_mixed_sequence_never_returns_unknown_exposure_to_capacity(case):
    def invariant():
        state = case.ledger.inspect_budget()
        assert state["available"] == state["limit"] - state["charged"] - state["held"]
        assert state["held"] + state["charged"] <= state["limit"]
    first = reserve(case)
    invariant()
    intent(case, first)
    invariant()
    case.ledger.observe_synthetic_acceptance_or_unknown(first["reservation_id"], observation(case, first), revision(case))
    invariant()
    second = reserve(case, "two")
    invariant()
    case.ledger.release_before_external_intent(second["reservation_id"], revision(case))
    invariant()
    third = reserve(case, "three")
    invariant()
    intent(case, third, "fake_three")
    invariant()
    accepted = observation(case, third, outcome="ACCEPTED", reason="ACCEPTED_FIXTURE", number=3, key="fake_three")
    case.ledger.observe_synthetic_acceptance_or_unknown(third["reservation_id"], accepted, revision(case))
    invariant()
    counts(case.ledger.inspect_budget(), (1, 1, 0))
    with pytest.raises(ERRORS):
        reserve(case, "four")
    invariant()


@pytest.mark.parametrize("damage", ["sum", "revision", "ledger_revision", "removed_event", "source", "schema"])
def test_bl16_tampered_or_missing_budget_history_cannot_create_optimistic_credit(case, damage):
    reserve(case)
    with sqlite3.connect(case.root / "research.sqlite3") as connection:
        sequence, body = connection.execute("SELECT sequence,body FROM audit ORDER BY sequence DESC LIMIT 1").fetchone()
        event = json.loads(body)
        if damage == "removed_event":
            connection.execute("DELETE FROM audit WHERE sequence=?", (sequence,))
        else:
            payload = event["budget"]
            if damage == "sum":
                payload["held"], payload["available"] = 0, 2
            elif damage == "revision":
                payload["before_project_revision"] += 1
            elif damage == "ledger_revision":
                payload["ledger_revision"] += 1
            elif damage == "source":
                payload["source_classification"] = "REAL_AF_RECEIPT"
            else:
                payload["schema_version"] = "budget-event-v999"
            event["metadata_digest"] = digest_bytes(canonical_json(payload))
            encoded = canonical_json(event)
            connection.execute("UPDATE audit SET body=?,digest=? WHERE sequence=?",
                               (encoded, digest_bytes(encoded), sequence))
    before = snapshot(case.root)
    with pytest.raises(ERRORS):
        case.ledger.inspect_budget()
    assert snapshot(case.root) == before


CHILD_SETUP = """
import json,sys
from pathlib import Path
from aegiscae.research import budget,project
from aegiscae.research.budget_rules import BudgetScope
p=project.open_existing_for_explicit_write(sys.argv[1])
scope=BudgetScope.from_bundle(p.read_frozen_bundle(sys.argv[2])['bundle'])
ledger=budget.BudgetLedger(p,scope)
"""


def test_bl06_two_independent_processes_compete_for_final_slot(tmp_path):
    case = budget_case(tmp_path, 1)
    code = CHILD_SETUP + """
Path(sys.argv[5]).write_text('ready')
sys.stdin.readline()
try:
    result=ledger.reserve_for_candidate(sys.argv[3],sys.argv[4],1,sys.argv[6],'fake_'+sys.argv[6],2)
    print(json.dumps({'winner':True,'result':result}))
except Exception as exc:
    if not hasattr(exc,'code'): raise
    print(json.dumps({'winner':False,'code':exc.code}))
"""
    processes = []
    for i in range(2):
        ready = tmp_path / f"ready{i}.txt"
        proc = subprocess.Popen([sys.executable, "-B", "-c", code, str(case.root), case.request.refs.bundle,
                                 case.request.candidate_id, case.candidate_digest, str(ready), f"worker{i}"],
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        processes.append((proc, ready))
    try:
        deadline = time.monotonic() + 15
        while not all(path.exists() for _, path in processes) and time.monotonic() < deadline:
            if any(proc.poll() is not None for proc, _ in processes):
                break
            time.sleep(0.02)
        assert all(path.exists() for _, path in processes)
        for proc, _ in processes:
            proc.stdin.write("go\n")
            proc.stdin.flush()
        results = []
        for proc, _ in processes:
            out, err = proc.communicate(timeout=20)
            assert proc.returncode == 0, err
            results.append(json.loads(out))
    finally:
        # Only children launched by this test can be terminated on fixture failure.
        for proc, _ in processes:
            if proc.poll() is None:
                proc.kill()
            proc.communicate(timeout=10)
    assert sum(row["winner"] for row in results) == 1, results
    assert next(row["code"] for row in results if not row["winner"]) in {
        "STORE_BUSY", "REVISION_CONFLICT", "BUDGET_EXHAUSTED"}
    counts(case.ledger.inspect_budget(), (1, 0, 0))


def test_bl14_budget_lifecycle_has_no_external_process_network_or_solver_import(case):
    code = """
import sys
observed=[]
def guard(event,args):
    denied=event.startswith(('socket.','os.spawn')) or event in ('subprocess.Popen','os.system')
    if event=='import':
        denied=denied or args[0].lower().startswith(('abaqus','abqjobpilot'))
    if denied:
        observed.append(event)
        raise AssertionError('external effect attempted: '+event)
sys.addaudithook(guard)
""" + CHILD_SETUP + """
oracle=budget.SyntheticOracle()
ledger=budget.BudgetLedger(p,scope,oracle)
held=ledger.reserve_for_candidate(sys.argv[3],sys.argv[4],1,'one','fake_one',2)
ledger.record_submission_intent(held['reservation_id'],'fake_one','sha256:'+'a'*64,3)
receipt=oracle.issue(held['reservation_id'],'fake_one','sha256:'+'a'*64,'ACCEPTED','fixture_'+'a'*32,'ACCEPTED_FIXTURE')
result=ledger.observe_synthetic_acceptance_or_unknown(held['reservation_id'],receipt,4)
print(json.dumps({'result':result,'external_events':observed}))
"""
    proc = subprocess.run([sys.executable, "-B", "-c", code, str(case.root), case.request.refs.bundle,
                           case.request.candidate_id, case.candidate_digest],
                          capture_output=True, text=True, timeout=20, check=False)
    assert proc.returncode == 0, proc.stderr
    output = json.loads(proc.stdout)
    assert output["external_events"] == []
    counts(output["result"], (0, 1, 1))
    for field in ("execution_authorized", "real_acceptance_established", "grant_consumed", "solver_start_observed"):
        assert output["result"][field] is False


def test_bl12_independent_process_reopen_preserves_unknown_and_readonly_bytes(case):
    held = reserve(case)
    intent(case, held)
    case.ledger.observe_synthetic_acceptance_or_unknown(held["reservation_id"], observation(case, held), revision(case))
    before = snapshot(case.root)
    code = CHILD_SETUP.replace("open_existing_for_explicit_write", "open_existing_readonly") + """
print(json.dumps({'budget':ledger.inspect_budget(),'events':p.audit_events(),
                  'bundle':p.read_frozen_bundle(sys.argv[2])['digests']}))
"""
    proc = subprocess.run([sys.executable, "-B", "-c", code, str(case.root), case.request.refs.bundle],
                          capture_output=True, text=True, timeout=20, check=False)
    assert proc.returncode == 0, proc.stderr
    result = json.loads(proc.stdout)
    counts(result["budget"], (1, 0, 1))
    assert "ACCEPTANCE_UNKNOWN" in json.dumps(result["budget"])
    assert result["bundle"] == case.bundle.digests()
    assert result["events"] == json.loads(json.dumps(case.project.audit_events()))
    assert snapshot(case.root) == before


@pytest.mark.parametrize("stage", ["before_begin", "after_event", "before_commit", "after_commit"])
def test_bl12_hard_exit_never_optimistically_refunds_or_retries(case, stage):
    code = CHILD_SETUP + """
import os
def crash(point):
    if point==sys.argv[5]: os._exit(73)
budget._fault=crash
ledger.reserve_for_candidate(sys.argv[3],sys.argv[4],1,'one','fake_one',2)
"""
    proc = subprocess.run([sys.executable, "-B", "-c", code, str(case.root), case.request.refs.bundle,
                           case.request.candidate_id, case.candidate_digest, stage],
                          capture_output=True, text=True, timeout=20, check=False)
    assert proc.returncode == 73, proc.stderr
    before = snapshot(case.root)
    if (case.root / "research.sqlite3-journal").exists():
        with pytest.raises(store.ProjectError, match="STORE_BUSY"):
            case.ledger.inspect_budget()
        assert snapshot(case.root) == before
        return
    committed = stage == "after_commit"
    counts(case.ledger.inspect_budget(), (int(committed), 0, 2 - int(committed)))
    assert snapshot(case.root) == before
    result = reserve(case, expected_revision=2)
    assert result["replayed"] is committed
