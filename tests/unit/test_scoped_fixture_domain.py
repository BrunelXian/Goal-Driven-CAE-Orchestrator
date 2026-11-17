"""Frozen replay rules, true scope rejections and raw evidence corruption (zero new simulations)."""
import json
import sqlite3

import pytest

from aegiscae.contracts.research_contracts import ContractError, canonical_json, digest_bytes
from aegiscae.research import project as store
from aegiscae.research import scoped_fixture as main
from aegiscae.research import scoped_fixture_rules as rules
from aegiscae.research import task_cards
from aegiscae.research.scoped_fixture_port import BASELINE

SCOPE = "1" * 64


@pytest.fixture()
def project(tmp_path):
    root = tmp_path / "fixture"
    store.create_research_project(root, "Fixture", research_agreements=True)
    return store.open_agreement_project(root, write=True)


def test_invalid_candidate_does_not_change_scope_or_revision(project):
    started = main.start(project, SCOPE, 1, 1, "intake")
    assert started["next_action"] == "PROPOSE_CANDIDATE"
    original = dict(force_N=50, unit="N", baseline_digest=started["baseline_digest"])
    for changes, error in [({"force_N": 201}, "LOAD_OUT_OF_BOUNDS"), ({"force_N": 0}, "LOAD_OUT_OF_BOUNDS"),
                           ({"force_N": True}, "LOAD_OUT_OF_BOUNDS"), ({"unit":"kN"}, "UNIT_MISMATCH"),
                           ({"baseline_digest":"0"*64}, "BASELINE_MISMATCH"),
                           ({"tolerance_mm":"1"}, "INVALID_CANDIDATE")]:
        with pytest.raises(ContractError, match=error):
            main.advance(project, SCOPE, 1, 2, "propose", original | changes)
        assert main.status(project, SCOPE, 1) == started
    admitted = main.advance(project, SCOPE, 1, 2, "propose", original)
    assert admitted["runs_used"] == 0
    assert main.advance(project, SCOPE, 1, 2, "propose", original) == admitted
    assert main.start(project, SCOPE, 1, 1, "intake") == started
    for other in (("0"*64, 1), (SCOPE, 3)):
        with pytest.raises(ContractError, match="SCOPE_CONFLICT"):
            main.status(project, *other)
    with pytest.raises(ContractError, match="REQUEST_KEY_CONFLICT"):
        main.advance(project, SCOPE, 1, 2, "propose", original | {"force_N": 199})
    with pytest.raises(ContractError, match="ILLEGAL_STEP"):
        main.start(project, SCOPE, 1, 3, "restart")
    tasks = task_cards.view(project)["tasks"]
    assert {t["task_id"] for t in tasks} == {"T01","T02","T03","T04"}
    assert all(t["role_contract"]["session_status"] == "LOGICAL_STEP" for t in tasks)


def test_zero_budget_and_reserved_tasks(project):
    stopped = main.start(project, SCOPE, 0, 1, "start")
    assert (stopped["state"], stopped["runs_used"]) == ("BUDGET_EXHAUSTED", 0)
    with pytest.raises(ContractError, match="ILLEGAL_STEP"):
        main.advance(project, SCOPE, 0, 2, "impossible")
    request = {"project": project.research_project_id, "key":"external", "expected_revision":2,
               "data":{"task_id":"T04", "execution":"IN_PROGRESS", "evidence":[]}}
    with pytest.raises(ContractError, match="RESERVED_TASK_OR_OPERATION"):
        task_cards.record_scoped(project, SCOPE, request, "task-update")
    assert main.status(project, SCOPE, 0, "missing")["request_receipt"] is None


def sample():
    inputs = rules.inputs_for("rp_" + "a"*32, SCOPE, 1, dict(force_N=60, unit="N",
                                                             baseline_digest=rules.digest(BASELINE)))
    candidate = {"inputs":inputs, "input_digest":rules.digest(inputs), "request_key":inputs["request_key"]}
    receipt = dict(value="0.6", unit="mm", direction="downward-positive", selector="fixture-tip",
                   project=inputs["project"], scope=SCOPE, baseline_digest=rules.digest(BASELINE),
                   backend_kind="FIXTURE", real_solver_executed=False, input_digest=candidate["input_digest"],
                   request_key=inputs["request_key"])
    return dict(candidate, receipt=receipt, observed_mm=receipt["value"], evidence_digest=rules.digest(receipt))


def test_validator_bounds_and_prior_or_wrong_input_rejected():
    expected = {"0.8999":"OUTSIDE_TARGET", "0.9":"WITHIN_TARGET", "1.1":"WITHIN_TARGET",
                "1.1001":"OUTSIDE_TARGET"}
    for value, verdict in expected.items():
        candidate = sample()
        candidate["receipt"]["value"] = candidate["observed_mm"] = value
        candidate["evidence_digest"] = rules.digest(candidate["receipt"])
        assert rules.decision_for(candidate)["decision"] == verdict
    for key in ("input_digest", "request_key", "project", "scope", "baseline_digest", "unit", "selector"):
        candidate = sample()
        candidate["receipt"][key] = "old-record"
        candidate["evidence_digest"] = rules.digest(candidate["receipt"])
        with pytest.raises(ContractError, match="FIXTURE_EVIDENCE_BINDING"):
            rules.decision_for(candidate)
    candidate = sample()
    del candidate["receipt"]["value"]
    with pytest.raises(ContractError, match="FIXTURE_EVIDENCE_BINDING"):
        rules.decision_for(candidate)


def test_core_reopen_rejects_tampered_target_even_with_recomputed_row_hash(project):
    main.start(project, SCOPE, 0, 1, "intake")
    # Deliberately corrupt an isolated test project with a test-only raw writer.
    with sqlite3.connect(project._root / "research.sqlite3") as conn:
        body = json.loads(conn.execute("SELECT body FROM audit WHERE sequence=2").fetchone()[0])
        body["workflow"]["payload"]["goal"]["target_mm"] = "100"
        body["metadata_digest"] = digest_bytes(canonical_json(body["workflow"]))
        encoded = canonical_json(body)
        conn.execute("UPDATE audit SET body=?,digest=? WHERE sequence=2",(encoded, digest_bytes(encoded)))
    with pytest.raises(store.ProjectError, match="INTEGRITY_ERROR"):
        store.open_agreement_project(project._root)
