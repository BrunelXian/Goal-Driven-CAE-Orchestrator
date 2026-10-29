"""M03-A: isolated synthetic workflow acceptance, never AF/solver evidence."""

import copy
import json
import sqlite3
import subprocess
import sys
import time
from dataclasses import asdict, replace
from pathlib import Path

import pytest

from aegiscae.contracts.research_contracts import (
    ContractBundle, ContractError, Quantity, canonical_json, digest_bytes,
)
from aegiscae.research import budget, mutation, project as store, workflow
from aegiscae.research.budget_rules import BudgetScope
from aegiscae.research.workflow_rules import (
    SyntheticRequest, WorkflowDefinition,
)
from test_model_mutation import make_case, snapshot

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
sys.path.insert(0, str(FIXTURES))
from synthetic_workflow_port import DurableSyntheticPort, FixtureConflict  # noqa: E402

ERRORS = (ContractError, store.ProjectError)
TERMINAL = {"SYNTHETIC_TARGET_MET", "SYNTHETIC_TARGET_UNMET", "BLOCKED"}


def workflow_case(tmp_path, *, change=None, fault=None, start=True):
    def policy(raw):
        raw["goal"]["budget"]["max_solver_calls"] = 2
        raw["goal"]["hard_constraints"][0]["threshold"]["value"] = "10"
        raw["verification"]["hard_constraint_checks"][0]["rule"]["threshold"]["value"] = "10"
        if change:
            change(raw)
    case = make_case(tmp_path, change_contract=policy)
    case.scope = BudgetScope.from_bundle(case.bundle)
    case.port = DurableSyntheticPort.create(tmp_path / "fake-port", case.bundle.verification.required_evidence)
    case.port.fault = fault
    second = replace(case.request, candidate_id="candidate_" + "c" * 32,
                     output_identity="stage_" + "d" * 32, idempotency_key="candidate-two",
                     new_value=Quantity("30", "force", "N"))
    case.definition = WorkflowDefinition.from_dict({
        "schema_version": "synthetic-workflow-v1", "workflow_id": "workflow_" + "e" * 32,
        "scope": asdict(case.scope), "source_id": case.port.source_id,
        "candidates": [asdict(case.request), asdict(second)], "max_steps": 2,
        "budget_units": 2, "on_unknown": "BLOCK"})
    if start:
        workflow.create_workflow(case.writer, case.definition, 2)
    case.coordinator = workflow.WorkflowCoordinator(case.writer, case.workspace,
        case.definition.workflow_id, case.port, case.port)
    case.ledger = budget.BudgetLedger(case.writer, case.scope)
    return case


@pytest.fixture
def case(tmp_path):
    return workflow_case(tmp_path)


def advance(case):
    return case.coordinator.advance(case.writer.inspect()["project_revision"])


def until(case, predicate, maximum=32):
    for _ in range(maximum):
        state = case.coordinator.inspect()
        if predicate(state):
            return state
        assert state["state"] not in TERMINAL, state
        advance(case)
    pytest.fail("bounded synthetic test did not reach expected committed state")


def finish(case):
    return until(case, lambda state: state["state"] in TERMINAL)


def original_request(port):
    with sqlite3.connect(port.root / "fixture.sqlite3") as db:
        raw = json.loads(db.execute("SELECT receipt FROM effects ORDER BY rowid LIMIT 1").fetchone()[0])
    return SyntheticRequest.from_dict(raw["request"])


def test_w01_w02_definition_is_fixed_scoped_and_revision_checked(case):
    state = case.coordinator.inspect()
    assert state["state"] == "READY_A"
    assert len(state["definition"]["candidates"]) == 2
    assert state["definition"]["scope"] == asdict(case.scope)
    before = snapshot(case.root)
    with pytest.raises(ERRORS):
        case.coordinator.advance(2)
    assert snapshot(case.root) == before
    for field, value in (("max_steps", 3), ("budget_units", 3), ("on_unknown", "RETRY")):
        raw = asdict(case.definition)
        raw[field] = value
        with pytest.raises(ERRORS):
            WorkflowDefinition.from_dict(raw)
    with pytest.raises(ERRORS):
        workflow.create_workflow(case.writer,
            replace(case.definition, workflow_id="workflow_" + "f" * 32), state["project_revision"])
    assert case.port.oracle()["effects"] == 0


@pytest.mark.parametrize("part", ["research_project_id", "bundle_id", "goal_id", "bundle", "model", "verification"])
def test_w01_wrong_frozen_identity_cannot_create_workflow(tmp_path, part):
    case = workflow_case(tmp_path, start=False)
    raw = asdict(case.definition)
    if part in {"bundle", "model", "verification"}:
        raw["scope"]["refs"][part] = digest_bytes(b"wrong frozen identity")
    else:
        prefix = {"research_project_id": "rp", "bundle_id": "bundle", "goal_id": "goal"}[part]
        raw["scope"][part] = prefix + "_" + "f" * 32
    before = snapshot(case.root)
    with pytest.raises(ERRORS):
        workflow.create_workflow(case.writer, WorkflowDefinition.from_dict(raw),
                                 case.writer.inspect()["project_revision"])
    assert snapshot(case.root) == before


def test_w03_w06_w07_w08_w17_complete_fixed_two_step_research_loop(case):
    baseline = case.source.read_bytes()
    frozen = case.bundle.canonical_bytes()
    old = case.project.audit_events()[:2]
    at_b = until(case, lambda state: state["state"] == "READY_B")
    assert len(at_b["decisions"]) == 1
    first = at_b["decisions"][0]
    assert first["verification"]["V3"] == "NOT_MET"
    assert first["verification"]["objective_met"] is False
    assert first["verification"]["hard_constraints_pass"] is True
    assert first["evidence"]["metrics"][0]["quantity"]["value"] == "2"
    assert first["decision"]["reason"] == "VALID_SYNTHETIC_TARGET_MISS"
    assert case.port.oracle()["effects"] == 1
    assert case.ledger.inspect_budget()["charged"] == 1
    assert case.ledger.inspect_budget()["available"] == 1
    done = finish(case)
    assert done["state"] == "SYNTHETIC_TARGET_MET", done
    assert len(done["decisions"]) == 2
    second = done["decisions"][1]
    assert second["verification"]["V3"] == "MET"
    assert second["verification"]["objective_met"] is True
    assert second["evidence"]["metrics"][0]["quantity"]["value"] == "0.5"
    assert first["verification"]["rule_digest"] == second["verification"]["rule_digest"]
    assert first["verification"]["frozen_refs"] == second["verification"]["frozen_refs"]
    assert case.port.oracle()["effects"] == 2
    assert len([c for c in case.port.oracle()["calls"] if c[0] == "accept"]) == 2
    totals = case.ledger.inspect_budget()
    assert (totals["held"], totals["charged"], totals["available"]) == (0, 2, 0)
    assert case.source.read_bytes() == baseline
    assert case.project.read_frozen_bundle(case.request.refs.bundle)["bundle"].canonical_bytes() == frozen
    assert case.project.audit_events()[:2] == old
    for candidate in case.definition.candidates:
        assert mutation.inspect_candidate(case.project, case.workspace, candidate.candidate_id)["admissibility"] == "PERMITTED"
    encoded = json.dumps(done)
    assert "NOT_ASSESSED" in encoded and "INCONCLUSIVE" in encoded
    assert "GOAL_SATISFIED" not in encoded


class CheckingPort:
    def __init__(self, case):
        self.case = case
        self.source_id = case.port.source_id
        self.checks = 0

    def accept(self, request):
        state = self.case.coordinator.inspect()
        ledger = self.case.ledger.inspect_budget()
        assert state["state"] == "CLAIMED"
        matches = [r for r in ledger["reservations"]
                   if r["request"]["downstream_business_key"] == request.business_key]
        assert len(matches) == 1
        assert matches[0]["state"] == "SUBMISSION_INTENT_RECORDED"
        assert matches[0]["intent"] == {"business_key": request.business_key,
                                         "request_digest": request.digest()}
        self.checks += 1
        return self.case.port.accept(request)

    def query(self, request):
        return self.case.port.query(request)

    def read_evidence(self, request, receipt):
        return self.case.port.read_evidence(request, receipt)


def test_w04_intent_and_budget_are_committed_before_every_external_like_effect(case):
    check = CheckingPort(case)
    case.coordinator = workflow.WorkflowCoordinator(case.writer, case.workspace,
        case.definition.workflow_id, check, check)
    assert finish(case)["state"] == "SYNTHETIC_TARGET_MET"
    assert check.checks == 2


def test_w09_terminal_replay_and_third_reservation_never_add_effect(case, tmp_path):
    finish(case)
    before = case.port.oracle()
    for _ in range(3):
        assert advance(case)["state"] == "SYNTHETIC_TARGET_MET"
    revision = case.writer.inspect()["project_revision"]
    raced = race_advances(case, tmp_path, revision)
    assert all(s["result"]["state"] == "SYNTHETIC_TARGET_MET" for s in raced)
    candidate = mutation.inspect_candidate(case.project, case.workspace, case.request.candidate_id)
    with pytest.raises(ERRORS):
        case.ledger.reserve_for_candidate(case.request.candidate_id,
            candidate["candidate"]["manifest"]["output_digest"], 1, "third", "fake_third",
            case.writer.inspect()["project_revision"])
    assert case.port.oracle() == before


def test_w10_independent_fixture_exact_key_replay_and_content_conflict(case):
    until(case, lambda state: case.port.oracle()["effects"] == 1)
    request = original_request(case.port)
    first = case.port.query(request)
    assert case.port.accept(request) == first
    assert case.port.oracle()["effects"] == 1
    with pytest.raises(FixtureConflict, match="SAME_KEY_DIFFERENT_REQUEST"):
        case.port.accept(replace(request, candidate_digest=digest_bytes(b"different input")))
    with pytest.raises(FixtureConflict, match="SYNTHETIC_REQUEST_REQUIRED"):
        case.port.accept(replace(request, step_id="C", business_key="fake_third_step"))
    with pytest.raises(FixtureConflict, match="SYNTHETIC_REQUEST_REQUIRED"):
        case.port.accept(replace(request, source_classification="AUTHENTICATED_AF"))
    assert case.port.oracle()["effects"] == 1


def test_w11_response_loss_reopens_with_query_only_and_no_duplicate_effect(tmp_path):
    case = workflow_case(tmp_path, fault="response_lost")
    until(case, lambda state: case.port.oracle()["effects"] == 1)
    assert len([c for c in case.port.oracle()["calls"] if c[0] == "accept"]) == 1
    case.coordinator = workflow.WorkflowCoordinator(store.open_existing_for_explicit_write(case.root),
        case.workspace, case.definition.workflow_id, case.port, case.port)
    assert finish(case)["state"] == "SYNTHETIC_TARGET_MET"
    assert case.port.oracle()["effects"] == 2
    assert len([c for c in case.port.oracle()["calls"] if c[0] == "accept"]) == 2


def test_w11_unresolved_query_never_refunds_retries_or_starts_b(case):
    until(case, lambda state: case.port.oracle()["effects"] == 1)
    case.port.fault = "query_unknown"
    until(case, lambda state: state["state"] == "ACCEPTANCE_UNKNOWN")
    for _ in range(3):
        state = advance(case)
        assert state["state"] == "ACCEPTANCE_UNKNOWN"
    totals = case.ledger.inspect_budget()
    assert (totals["held"], totals["charged"], totals["available"]) == (1, 0, 1)
    assert case.port.oracle()["effects"] == 1
    assert len([c for c in case.port.oracle()["calls"] if c[0] == "accept"]) == 1
    assert len(state["decisions"]) == 0


class DamagedEvidencePort:
    def __init__(self, port, damage):
        self.port, self.source_id, self.damage = port, port.source_id, damage

    def accept(self, request):
        return self.port.accept(request)

    def query(self, request):
        receipt = self.port.query(request)
        if self.damage in {"source", "project", "candidate", "step", "key", "attempt", "digest"}:
            name, value = {
                "source": ("source_id", "syntheticport_" + "0" * 32),
                "project": ("research_project_id", "rp_" + "0" * 32),
                "candidate": ("candidate_id", "candidate_" + "0" * 32),
                "step": ("step_id", "B"), "key": ("business_key", "fake_wrong"),
                "attempt": ("attempt_id", "syntheticattempt_" + "0" * 32),
                "digest": ("candidate_digest", digest_bytes(b"old artifact")),
            }[self.damage]
            other = replace(receipt.request, **{name: value})
            return replace(receipt, request=other, request_digest=other.digest())
        return receipt

    def read_evidence(self, request, receipt):
        evidence = self.port.read_evidence(request, receipt)
        if self.damage == "missing":
            return None
        if self.damage == "missing_metric":
            return replace(evidence, metrics=())
        if self.damage == "protocol":
            return replace(evidence, protocol_valid=False)
        if self.damage == "old_receipt":
            return replace(evidence, receipt=replace(receipt, receipt_id="syntheticreceipt_" + "0" * 32))
        metric = evidence.metrics[0]
        if self.damage == "unit":
            metric = replace(metric, quantity=replace(metric.quantity, unit="m"))
        elif self.damage == "nan":
            metric = replace(metric, quantity=replace(metric.quantity, value="NaN"))
        elif self.damage == "frame":
            metric = replace(metric, requirement=replace(metric.requirement,
                selector=replace(metric.requirement.selector, frame=2)))
        return replace(evidence, metrics=(metric, *evidence.metrics[1:]))


@pytest.mark.parametrize("damage", ["source", "project", "candidate", "step", "key", "attempt",
                                   "digest", "missing", "missing_metric", "protocol", "old_receipt",
                                   "unit", "nan", "frame"])
def test_w05_w12_bad_receipt_or_evidence_blocks_b_and_final_claim(case, damage):
    port = DamagedEvidencePort(case.port, damage)
    case.coordinator = workflow.WorkflowCoordinator(case.writer, case.workspace,
        case.definition.workflow_id, port, port)
    done = finish(case)
    assert done["state"] == "BLOCKED", done
    assert done["reason"] in {"EVIDENCE_INCONCLUSIVE", "HUMAN_REVIEW_REQUIRED"}
    assert case.port.oracle()["effects"] == 1
    assert len(case.port.oracle()["keys"]) == 1


def test_w13_invalid_model_cannot_be_treated_as_target_miss(case):
    case.source.write_bytes(case.source.read_bytes().replace(b"E=210000", b"E=200000"))
    result = finish(case)
    assert result["state"] == "BLOCKED" and result["reason"] == "MODEL_REJECTED"
    assert case.port.oracle()["effects"] == 0
    assert not result["decisions"]


def test_w13_failed_hard_constraint_is_not_legitimate_objective_miss(tmp_path):
    def tight(raw):
        raw["goal"]["hard_constraints"][0]["threshold"]["value"] = "1"
        raw["verification"]["hard_constraint_checks"][0]["rule"]["threshold"]["value"] = "1"
    case = workflow_case(tmp_path, change=tight)
    done = finish(case)
    assert done["state"] == "BLOCKED"
    assert case.port.oracle()["effects"] == 1


def test_w13_new_frozen_criteria_blocks_current_workflow_without_rewriting_history(case):
    old = case.bundle.canonical_bytes()
    raw = copy.deepcopy(case.raw)
    raw["version"] = raw["goal"]["version"] = 2
    raw["goal"]["target"]["value"] = "0.8"
    case.writer.freeze_contract_bundle(ContractBundle.from_dict(raw),
        case.writer.inspect()["project_revision"], "later-goal")
    result = advance(case)
    assert result["state"] == "BLOCKED" and result["reason"] == "CONTRACT_STALE"
    assert case.port.oracle()["effects"] == 0
    assert case.project.read_frozen_bundle(case.request.refs.bundle)["bundle"].canonical_bytes() == old


def test_w13_exhausted_budget_blocks_b_without_effect(case):
    until(case, lambda state: state["state"] == "READY_B")
    candidate = mutation.inspect_candidate(case.project, case.workspace, case.request.candidate_id)
    case.ledger.reserve_for_candidate(case.request.candidate_id,
        candidate["candidate"]["manifest"]["output_digest"], 1, "outside-workflow", "fake_other",
        case.writer.inspect()["project_revision"])
    result = advance(case)
    assert result["state"] == "BLOCKED" and result["reason"] == "BUDGET_BLOCKED"
    assert case.port.oracle()["effects"] == 1


def test_w07_b_requires_fresh_mutation_recheck_after_valid_a(case):
    until(case, lambda state: state["state"] == "READY_B")
    case.source.write_bytes(case.source.read_bytes().replace(b"FIXED=Base", b"FIXED=Other"))
    result = finish(case)
    assert result["state"] == "BLOCKED" and result["reason"] == "MODEL_REJECTED"
    assert case.port.oracle()["effects"] == 1


@pytest.mark.parametrize("when", ["before_accept", "after_accept"])
def test_w07_w12_candidate_output_pollution_blocks_decision_and_b(case, when):
    until(case, lambda state: state["next_action"] == "CLAIM_ONCE")
    if when == "after_accept":
        advance(case)
        assert case.port.oracle()["effects"] == 1
    case.output.write_bytes(case.output.read_bytes().replace(b"LOAD_N 20", b"LOAD_N 21"))
    result = finish(case)
    assert result["state"] == "BLOCKED" and result["reason"] == "MODEL_REJECTED"
    assert case.port.oracle()["effects"] == (1 if when == "after_accept" else 0)
    assert result["decisions"] == []


def test_w13_explicit_preintent_budget_release_is_not_recreated_or_executed(case):
    state = until(case, lambda state: state["next_action"] == "RECORD_INTENT")
    case.ledger.release_before_external_intent(state["reservation_id"], state["project_revision"])
    result = advance(case)
    assert result["state"] == "BLOCKED" and result["reason"] == "BUDGET_BLOCKED"
    assert case.port.oracle()["effects"] == 0


def test_w15_existing_journal_blocks_without_read_repair_or_refund(case):
    revision = case.writer.inspect()["project_revision"]
    journal = case.root / "research.sqlite3-journal"
    journal.write_bytes(b"synthetic unclassified journal")
    before = snapshot(case.root)
    result = case.coordinator.advance(revision)
    assert result["reason"] == "JOURNAL_BLOCKED"
    assert snapshot(case.root) == before
    assert case.port.oracle()["effects"] == 0


def test_w17_persisted_decision_cannot_be_replaced_by_chat_or_local_snapshot(case):
    before = until(case, lambda state: state["state"] == "READY_B")
    before["state"] = "SYNTHETIC_TARGET_MET"
    before["decisions"].clear()
    reopened = workflow.WorkflowCoordinator(store.open_existing_readonly(case.root), case.workspace,
        case.definition.workflow_id).inspect()
    assert reopened["state"] == "READY_B"
    assert len(reopened["decisions"]) == 1
    with pytest.raises(ERRORS):
        workflow.WorkflowCoordinator(store.open_existing_readonly(case.root), case.workspace,
            case.definition.workflow_id, case.port, case.port).advance(reopened["project_revision"])


@pytest.mark.parametrize("damage", ["decision", "verification", "receipt"])
def test_w17_rehashed_forged_decision_is_recomputed_and_rejected(case, damage):
    until(case, lambda state: state["state"] == "READY_B")
    with sqlite3.connect(case.root / "research.sqlite3") as db:
        sequence, body = db.execute("SELECT sequence,body FROM audit ORDER BY sequence DESC LIMIT 1").fetchone()
        event = json.loads(body)
        assert event["workflow"]["action"] == "DECIDE"
        data = event["workflow"]["data"]
        if damage == "decision":
            data["decision"]["reason"] = "SYNTHETIC_TARGET_MET"
        elif damage == "verification":
            data["verification"]["V3"] = "MET"
        else:
            data["evidence"]["receipt"]["receipt_id"] = "syntheticreceipt_" + "0" * 32
        event["metadata_digest"] = digest_bytes(canonical_json(event["workflow"]))
        body = canonical_json(event)
        db.execute("UPDATE audit SET body=?,digest=? WHERE sequence=?", (body, digest_bytes(body), sequence))
    before = snapshot(case.root)
    with pytest.raises(ERRORS):
        case.coordinator.inspect()
    assert snapshot(case.root) == before
    assert case.port.oracle()["effects"] == 1


CHILD_SETUP = """
import json,sys,os
from pathlib import Path
sys.path.insert(0,sys.argv[5])
from synthetic_workflow_port import DurableSyntheticPort
from aegiscae.research import project,mutation,workflow
p=project.open_existing_for_explicit_write(sys.argv[1])
w=mutation.SyntheticWorkspace(Path(sys.argv[2]),sys.argv[3])
port=DurableSyntheticPort(Path(sys.argv[4]))
c=workflow.WorkflowCoordinator(p,w,sys.argv[6],port,port)
"""


def child_args(case):
    return [str(case.root), str(case.workspace._root), case.workspace.workspace_id,
            str(case.port.root), str(FIXTURES), case.definition.workflow_id]


def test_w16_separate_python_reconstructs_decision_and_continues_only_eligible_b(case):
    before = until(case, lambda state: state["state"] == "READY_B")
    code = CHILD_SETUP + """
s=c.inspect()
assert s['state']=='READY_B' and len(s['decisions'])==1
for _ in range(20):
    s=c.inspect()
    if s['state']=='SYNTHETIC_TARGET_MET':break
    c.advance(s['project_revision'])
print(json.dumps(c.inspect()))
"""
    result = subprocess.run([sys.executable, "-B", "-c", code, *child_args(case)],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    after = json.loads(result.stdout)
    assert after["state"] == "SYNTHETIC_TARGET_MET"
    assert after["decisions"][0] == before["decisions"][0]
    assert case.port.oracle()["effects"] == 2


def race_advances(case, tmp_path, revision):
    code = CHILD_SETUP + """
Path(sys.argv[7]).write_text('ready')
sys.stdin.readline()
try:
    print(json.dumps({'result':c.advance(int(sys.argv[8]))}))
except Exception as exc:
    if not hasattr(exc,'code'):raise
    print(json.dumps({'error':exc.code}))
"""
    children = []
    for number in range(2):
        ready = tmp_path / f"ready-{number}.txt"
        process = subprocess.Popen([sys.executable, "-B", "-c", code, *child_args(case),
                                    str(ready), str(revision)], stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        children.append((process, ready))
    try:
        deadline = time.monotonic() + 15
        while not all(path.exists() for _, path in children) and time.monotonic() < deadline:
            if any(p.poll() is not None for p, _ in children):
                break
            time.sleep(0.02)
        assert all(path.exists() for _, path in children)
        for process, _ in children:
            process.stdin.write("go\n")
            process.stdin.flush()
        results = []
        for process, _ in children:
            out, err = process.communicate(timeout=25)
            assert process.returncode == 0, err
            results.append(json.loads(out))
        assert len(results) == 2
        return results
    finally:
        for process, _ in children:
            if process.poll() is None:
                process.kill()  # Only a directly owned synthetic test Python child.
                process.wait(timeout=10)


def test_w14_two_processes_race_for_claim_only_one_calls_accept(case, tmp_path):
    until(case, lambda state: state["next_action"] == "CLAIM_ONCE")
    race_advances(case, tmp_path, case.writer.inspect()["project_revision"])
    assert case.port.oracle()["effects"] == 1
    assert len([c for c in case.port.oracle()["calls"] if c[0] == "accept"]) == 1


@pytest.mark.parametrize("point", ["after_candidate", "before_reserve", "after_reserve",
                                  "before_intent", "after_intent", "after_claim", "before_effect",
                                  "after_effect", "after_evidence", "before_decision",
                                  "after_decision", "before_b_admission", "after_charge"])
def test_w15_committed_boundary_hard_exit_never_repeats_accept(case, point):
    code = CHILD_SETUP + """
def stop(stage):
    if stage==sys.argv[7]:os._exit(73)
workflow._fault=stop
for _ in range(30):
    s=c.inspect()
    if s['state'] in ('BLOCKED','SYNTHETIC_TARGET_MET','SYNTHETIC_TARGET_UNMET'):break
    c.advance(s['project_revision'])
raise RuntimeError('requested synthetic fault not reached')
"""
    result = subprocess.run([sys.executable, "-B", "-c", code, *child_args(case), point],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 73, result.stderr
    prior_count = case.port.oracle()["effects"]
    reopened = workflow.WorkflowCoordinator(store.open_existing_for_explicit_write(case.root),
        case.workspace, case.definition.workflow_id, case.port, case.port)
    case.coordinator = reopened
    if point in {"after_claim", "before_effect"}:
        for _ in range(4):
            result = advance(case)
        assert result["state"] == "ACCEPTANCE_UNKNOWN"
        assert case.port.oracle()["effects"] == prior_count == 0
    else:
        assert finish(case)["state"] == "SYNTHETIC_TARGET_MET"
        assert case.port.oracle()["effects"] == 2
    assert len([c for c in case.port.oracle()["calls"] if c[0] == "accept"]) <= 2


def test_w15_fixture_accepted_before_process_death_is_queryable_without_resubmit(case):
    until(case, lambda state: state["state"] == "PREPARED"
          and bool(case.ledger.inspect_budget()["reservations"])
          and case.ledger.inspect_budget()["reservations"][0]["intent"] is not None)
    code = CHILD_SETUP + """
port.fault='exit_after_accept'
c.advance(c.inspect()['project_revision'])
"""
    result = subprocess.run([sys.executable, "-B", "-c", code, *child_args(case)],
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 74, result.stderr
    assert case.port.oracle()["effects"] == 1
    assert finish(case)["state"] == "SYNTHETIC_TARGET_MET"
    assert case.port.oracle()["effects"] == 2
    assert len([c for c in case.port.oracle()["calls"] if c[0] == "accept"]) == 2


@pytest.mark.parametrize("point", ["workflow_event_before_commit", "workflow_event_after_commit"])
def test_w15_workflow_transaction_hard_exit_preserves_or_blocks_without_recovery(case, point):
    code = CHILD_SETUP + """
def stop(stage):
    if stage==sys.argv[7]:os._exit(73)
workflow._fault=stop
c.advance(c.inspect()['project_revision'])
"""
    result = subprocess.run([sys.executable, "-B", "-c", code, *child_args(case), point],
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 73, result.stderr
    before = snapshot(case.root)
    if (case.root / "research.sqlite3-journal").exists():
        with pytest.raises(store.ProjectError, match="STORE_BUSY"):
            store.open_existing_readonly(case.root)
        assert snapshot(case.root) == before
        assert case.port.oracle()["effects"] == 0
    else:
        assert finish(case)["state"] == "SYNTHETIC_TARGET_MET"
        assert case.port.oracle()["effects"] == 2


@pytest.mark.parametrize("point", ["after_reserve", "after_intent", "after_effect", "before_decision"])
def test_w15_exception_at_boundary_keeps_committed_state(case, monkeypatch, point):
    def fail(stage):
        if stage == point:
            raise RuntimeError("SYNTHETIC_INTERRUPTION")
    monkeypatch.setattr(workflow, "_fault", fail)
    with pytest.raises(RuntimeError, match="SYNTHETIC_INTERRUPTION"):
        finish(case)
    monkeypatch.setattr(workflow, "_fault", lambda _: None)
    assert finish(case)["state"] == "SYNTHETIC_TARGET_MET"
    assert case.port.oracle()["effects"] == 2
    assert len([c for c in case.port.oracle()["calls"] if c[0] == "accept"]) == 2


def test_w18_w19_no_af_network_process_or_physical_authority_during_workflow(case):
    code = """
import sys
observed=[]
def guard(event,args):
    denied=(event.startswith('subprocess.') or event.startswith('socket.')
            or event in ('os.system','os.posix_spawn','os.spawn','os.startfile'))
    if event=='import' and args and isinstance(args[0],str):
        denied=denied or args[0].lower().startswith(('abaqus','abqjobpilot'))
    if denied:
        observed.append(event)
        raise AssertionError('external effect attempted')
sys.addaudithook(guard)
""" + CHILD_SETUP + """
for _ in range(25):
    state=c.inspect()
    if state['state']=='SYNTHETIC_TARGET_MET':break
    c.advance(state['project_revision'])
print(json.dumps({'state':c.inspect(),'external_events':observed}))
"""
    proc = subprocess.run([sys.executable, "-B", "-c", code, *child_args(case)],
                          capture_output=True, text=True, timeout=40)
    assert proc.returncode == 0, proc.stderr
    output = json.loads(proc.stdout)
    assert output["external_events"] == []
    state = output["state"]
    assert state["state"] == "SYNTHETIC_TARGET_MET"
    assert state["source_classification"] == "SYNTHETIC_TEST_ONLY"
    assert state["qualification"] == "NOT_ABAQUS_QUALIFIED"
    assert state["physical_evidence_eligible"] is False
    for flag in ("execution_authorized", "AF_WORKFLOW_COMPATIBILITY_VERIFIED",
                 "SCIENTIFIC_VERIFICATION_AVAILABLE", "ABAQUS_PARAMETERIZED_EXECUTION_VERIFIED",
                 "CODEX_AUTOMATIC_MAIN_CONTINUATION_VERIFIED"):
        assert state[flag] is False
    for record in state["decisions"]:
        verification = record["verification"]
        assert verification["V2"] == "NOT_RUN" and verification["V4"] == "NOT_ASSESSED"
        assert verification["missing_real_checks"] == ["V2", "V4"]
        assert verification["real_goal"] == "INCONCLUSIVE"
        assert verification["physical_evidence_eligible"] is False
