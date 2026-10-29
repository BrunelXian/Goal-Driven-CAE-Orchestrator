"""M03-B real AF IPC. Explicit opt-in, fresh isolated fixtures, no real solver."""

import copy
import json
import os
import subprocess
import sys
import time
from dataclasses import replace
from pathlib import Path

import pytest

from aegiscae.contracts.research_contracts import digest_bytes
from aegiscae.research.workflow_rules import SyntheticRequest
from m03b_support import (
    AFTestPort, advance_until, check, close, fresh_root, prepare, read, reopen,
    start, validate_facts, write_new,
)

LIVE = os.environ.get("GDCAE_M03B_LIVE") == "APPROVED_TEST_ONLY"
pytestmark = pytest.mark.skipif(not LIVE, reason="M03-B fresh TEST root and explicit live opt-in required")


@pytest.fixture(scope="session")
def live_root():
    check(os.name == "nt", "WINDOWS_REQUIRED")
    check(str(Path(sys.executable)).lower() == "d:\\xianlab\\envs\\langchainenv\\scripts\\python.exe",
          "INTERPRETER_MISMATCH")
    head = subprocess.check_output(["git", "-C", os.environ["GDCAE_AF_SOURCE"], "rev-parse", "HEAD"], text=True).strip()
    check(head == "7f4b8d8f3a2c862ed8b244d495295f5d51ea0d88", "AF_BASELINE_CHANGED")
    check(not subprocess.check_output(["git", "-C", os.environ["GDCAE_AF_SOURCE"], "status",
                                      "--porcelain", "--untracked-files=no"], text=True), "AF_DIRTY")
    return fresh_root(os.environ["GDCAE_M03B_ROOT"])


@pytest.fixture
def case(live_root, request):
    check(not (live_root / "cleanup-blocked.json").exists(), "PRIOR_CLEANUP_BLOCKED")
    root = live_root / request.node.name.replace("[", "_").replace("]", "")
    root.mkdir()
    value = prepare(root)
    try:
        start(value, **getattr(request, "param", {}))
        yield value
    finally:
        failures = []
        for child in value.coordinator_children:
            try:
                child_finish(child)
            except Exception as exc:
                failures.append(type(exc).__name__)
        try:
            if value.harness.children:
                close(value)
        except Exception as exc:
            failures.append(type(exc).__name__)
        if failures:
            write_new(live_root / "cleanup-blocked.json", {"case": root.name, "errors": failures})
            pytest.fail("CLEANUP_BLOCKED_NO_FURTHER_LIVE_CASES")


def until(case, predicate):
    return advance_until(case.coordinator, predicate)


def facts(case, step):
    files = list(case.fixture_root.glob(step + "-facts-*.json"))
    assert files
    return read(files[-1])


def child_start(case, label, stage="none"):
    from abqjobpilot.execution.process_handles import ProcessReference
    control = case.fixture_root / label
    control.mkdir()
    stdout, stderr = (control / "stdout.txt").open("wb"), (control / "stderr.txt").open("wb")
    process = subprocess.Popen([sys.executable, "-B", str(Path(__file__).with_name("m03b_child.py")),
        str(case.fixture_root), str(control), stage], stdin=subprocess.DEVNULL,
        stdout=stdout, stderr=stderr, creationflags=subprocess.CREATE_NO_WINDOW)
    child = {"process": process, "reference": None, "control": control,
             "stdout": stdout, "stderr": stderr, "finished": False}
    case.coordinator_children.append(child)  # Register original handle before any fallible handshake.
    write_new(control / "launch.json", {"launcher_pid": process.pid, "owned": True})
    deadline = time.monotonic() + 20
    while not (control / "identity.json").exists() and process.poll() is None and time.monotonic() < deadline:
        time.sleep(0.02)
    assert (control / "identity.json").exists(), "CHILD_HANDSHAKE_UNKNOWN"
    identity = read(control / "identity.json")
    assert identity["pid"] == process.pid or identity["parent_pid"] == process.pid
    reference = ProcessReference(identity["pid"], identity)
    child["reference"] = reference
    return child


def child_finish(child):
    if child["finished"]:
        return child["process"].returncode
    process, reference, control = child["process"], child["reference"], child["control"]
    code = process.wait(timeout=35)  # Child's own unbound handshake expires after 30s.
    check(reference is not None, "CHILD_HOST_IDENTITY_UNCONFIRMED")
    evidence = reference.exit_evidence()
    check(evidence is not None, "CHILD_HOST_EXIT_UNCONFIRMED")
    write_new(control / "exit.json", {"launcher_pid": process.pid, "launcher_exit": code,
        "actual_pid": reference.identity["pid"], "actual_exit": evidence["exit_code"],
        "original_handle_exit_observed": True})
    reference.close()  # Never discard an unresolved original handle on timeout.
    child["stdout"].close()
    child["stderr"].close()
    child["finished"] = True
    assert code in (0, 73, 74), (control / "stderr.txt").read_text()
    return code


def child_once(case, stage="none"):
    child = child_start(case, "child-" + stage, stage)
    write_new(child["control"] / "go.json", {"revision": case.writer.inspect()["project_revision"]})
    return child_finish(child)


def test_b01_b09_real_ab_lost_reply_independent_reader_and_competing_main(case):
    # Discard the actual successful submit reply, not an offline mocked acceptance.
    case.port.fault = "reply_lost"
    at_b = until(case, lambda s: s["state"] == "READY_B")
    assert at_b["decisions"][0]["verification"]["V3"] == "NOT_MET"
    assert at_b["decisions"][0]["evidence"]["metrics"][0]["quantity"]["value"] == "2"
    assert case.ledger.inspect_budget()["charged"] == 1
    original = facts(case, "A")
    independent = AFTestPort(case.fixture_root, case.writer, case.workspace)
    req = SyntheticRequest.from_dict(original["synthetic_request"])
    before_reader = case.harness.client().events()
    assert independent.collect(req)["raw"]["receipt"] == original["raw"]["receipt"]
    assert case.harness.client().events() == before_reader
    # AF idempotency is tested separately from coordinator's one-invocation gate.
    client = case.harness.client()
    replay = client.submit(case.harness.requests[0])
    assert replay["replayed"] and replay["receipt"] == original["raw"]["receipt"]
    wrong = {**case.harness.requests[0], "job_revision": 99}
    with pytest.raises(Exception) as error:
        client.submit(wrong)
    assert error.value.code == "IDEMPOTENCY_CONFLICT"
    claim = until(case, lambda s: s["next_action"] == "CLAIM_ONCE")
    children = [child_start(case, "competitor-" + str(i)) for i in range(2)]
    for child in children:
        write_new(child["control"] / "go.json", {"revision": claim["project_revision"]})
    assert [child_finish(c) for c in children] == [0, 0]
    outcomes = [read(c["control"] / "result.json") for c in children]
    assert sum("error" not in x and x["state"] == "CLAIMED" for x in outcomes) == 1
    case.coordinator = reopen(case.fixture_root)
    final = until(case, lambda s: s["state"] == "SYNTHETIC_TARGET_MET")
    assert final["decisions"][1]["evidence"]["metrics"][0]["quantity"]["value"] == "0.5"
    assert final["real_goal"] == "INCONCLUSIVE"
    totals = case.ledger.inspect_budget()
    assert (totals["held"], totals["charged"], totals["available"]) == (0, 2, 0)
    runs = client.project_view()["runs"]
    assert len(runs) == 2 and len({r["run_id"] for r in runs}) == 2
    mappings = []
    for step in ("A", "B"):
        item = facts(case, step)
        run, receipt = item["raw"]["run"], item["raw"]["receipt"]
        mappings.append({"step": step, "business_key": receipt["idempotency_key"],
            "candidate_id": item["synthetic_request"]["candidate_id"],
            "candidate_digest": item["synthetic_request"]["candidate_digest"],
            "project_id": run["project_id"], "project_instance_id": run["project_instance_id"],
            "run_id": run["run_id"], "request_id": receipt["request_id"],
            "plan_id": run["plan_id"], "plan_digest": run["plan_digest"],
            "phase_attempt_id": run["phase_attempt_id"], "input_equivalence": item["input_equivalence"]})
        assert len(list(case.fixture_root.glob(step + "-submit-ticket.json"))) == 1
    assert all(mappings[0][k] != mappings[1][k] for k in
               ("candidate_digest", "request_id", "plan_id", "plan_digest", "run_id", "phase_attempt_id"))
    before = client.events()
    for _ in range(2):
        final = case.coordinator.advance(final["project_revision"])
    assert client.events() == before
    write_new(case.fixture_root / "public-result.json", {"status": "AB_SCENARIO_PASS_PENDING_SUITE_AND_CLEANUP",
        "mapping": mappings, "budget": {k: totals[k] for k in ("held", "charged", "available")},
        "accept_events": sum(e["type"] == "REQUEST_ACCEPTED" for e in before),
        "events": [{k: e[k] for k in ("run_id", "type", "project_sequence")} for e in before],
        "race_outcomes": outcomes, "ABAQUS_EXECUTION_VERIFIED": False,
        "AF_PRODUCT_MULTI_PLAN_VERIFIED": False, "PHYSICAL_VALIDATION_AVAILABLE": False})


@pytest.mark.parametrize("stage,action,effects", [
    ("after_intent", "RECORD_INTENT", 0), ("before_effect", "CLAIM_ONCE", 0),
    ("exit_after_accept", "CLAIM_ONCE", 1), ("after_effect", "CLAIM_ONCE", 1),
    ("after_charge", "CHARGE_ONCE", 1),
    ("after_evidence", "READ_AND_DECIDE", 1), ("before_decision", "READ_AND_DECIDE", 1),
    ("after_decision", "READ_AND_DECIDE", 1), ("before_b_admission", "PREPARE_CANDIDATE", 1),
])
def test_b12_cross_store_hard_exit_reopen(case, stage, action, effects):
    if stage == "before_b_admission":
        until(case, lambda s: s["state"] == "READY_B")
    else:
        until(case, lambda s: s["next_action"] == action)
    assert child_once(case, stage) in (73, 74)
    assert len(case.harness.client().project_view()["runs"]) == effects
    case.coordinator = reopen(case.fixture_root)
    if stage == "before_effect":
        state = until(case, lambda s: s["state"] == "ACCEPTANCE_UNKNOWN")
        assert case.ledger.inspect_budget()["held"] == 1
        assert len(case.harness.client().project_view()["runs"]) == 0
        assert case.coordinator.advance(state["project_revision"])["state"] == "ACCEPTANCE_UNKNOWN"
    else:
        final = until(case, lambda s: s["state"] == "SYNTHETIC_TARGET_MET")
        assert len(final["decisions"]) == 2
        assert len(case.harness.client().project_view()["runs"]) == 2


def test_b10_unknown_receipt_holds_and_no_b(case):
    until(case, lambda s: s["state"] == "CLAIMED")
    case.port.fault = "query_unknown"
    state = until(case, lambda s: s["state"] == "ACCEPTANCE_UNKNOWN")
    for _ in range(2):
        assert case.coordinator.advance(state["project_revision"])["state"] == "ACCEPTANCE_UNKNOWN"
    assert case.ledger.inspect_budget()["held"] == 1
    assert len(case.harness.client().project_view()["runs"]) == 1
    assert not (case.fixture_root / "B-submit-ticket.json").exists()

def test_b13_b14_real_evidence_then_faulted_read_boundary(case):
    state = until(case, lambda s: s["next_action"] == "READ_AND_DECIDE")
    snapshot = facts(case, "A")
    mapping, _, owner = case.port._documents()
    original = snapshot["raw"]
    changes = [
        (("source", "project_id"), "p_" + "f" * 32),
        (("source", "project_instance_id"), "pi_" + "f" * 32),
        (("source", "context_digest"), digest_bytes(b"wrong")),
        (("source", "owner_id"), "owner_" + "f" * 32),
        (("run", "plan_digest"), digest_bytes(b"wrong")),
        (("run", "phase_attempt_id"), "phase_" + "f" * 32),
        (("run", "run_id"), "r_" + "f" * 32),
        (("run", "solver_conclusion"), "COMPLETED_TEXT_EVIDENCE"),
        (("run", "execution"), "START_INTENT"),
        (("receipt", "namespace"), '["wrong","other","submit"]'),
        (("receipt", "idempotency_key"), "fake_wrong"),
        (("health", "dispatch_enabled"), False),
        (("validations",), []), (("events",), original["events"][:-1]),
        (("events_complete",), False),
        (("validations", 0, "scope"), "fixed_standard_dat_only"),
        (("validations", 0, "verdict"), "FAIL"),
        (("diagnose", "body", "facts", "observations", 0, "digest"), digest_bytes(b"stale")),
        (("diagnose", "body", "facts", "validations", 0, "verdict"), "FAIL"),
        (("diagnose", "body", "facts", "receipt", "request_id"), "req_" + "f" * 32),
        (("diagnose", "body", "facts", "events", 0, "type"), "START_INTENT"),
        (("diagnose", "body", "facts", "plan", "plan_id"), "plan_" + "f" * 32),
        (("diagnose", "body", "facts", "receipt"), {}),
        (("diagnose", "body", "facts", "validations", 0), {}),
        (("diagnose", "body", "facts", "events", 0), {}),
        (("diagnose", "body", "facts", "dispatch_gate", "state"), "PAUSED"),
    ]
    rejected = []
    for path, value in changes:
        altered = copy.deepcopy(original)
        target = altered
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value
        with pytest.raises((ValueError, KeyError)):
            validate_facts(altered, mapping, owner, mapping["rows"][0])
        rejected.append(list(path))
    # Real bad credentials/stale endpoint checks, without changing the live owner.
    from aegiscae.adapters.abaqus.af_evidence import EvidenceBridge
    for field, value in (("project_id", "p_" + "f" * 32), ("owner_id", "owner_" + "f" * 32)):
        assert EvidenceBridge().capabilities(replace(case.port.binding(), **{field: value})).error
    connection = case.harness.root / "private" / "connection.json"
    saved = connection.read_bytes()
    try:
        invalid = json.loads(saved)
        invalid["credential"] = "M03B-invalid-test-credential"
        connection.write_bytes(json.dumps(invalid).encode())
        assert EvidenceBridge().capabilities(case.port.binding()).error.code == "AUTHENTICATION_FAILED"
    finally:
        connection.write_bytes(saved)
    # Missing AF evidence at the decisive read is terminal, never goal acceptance.
    case.port.fault = "missing_evidence"
    result = case.coordinator.advance(state["project_revision"])
    assert result["state"] == "BLOCKED" and result["reason"] == "EVIDENCE_INCONCLUSIVE"
    assert len(case.harness.client().project_view()["runs"]) == 1
    write_new(case.fixture_root / "negative-result.json", {"rejected_fields": rejected,
        "origin": "controlled corruption of actual authenticated Bridge responses", "final": result["state"]})


@pytest.mark.parametrize("target", ["oracle", "candidate", "mapping"])
def test_b13_oracle_candidate_mapping_tamper_blocks(case, target):
    state = until(case, lambda s: s["next_action"] == "READ_AND_DECIDE")
    if target == "oracle":
        path = case.fixture_root / "oracle.json"
        raw = read(path)
        raw["rows"][0]["candidate_id"] = "candidate_" + "f" * 32
        path.write_text(json.dumps(raw), encoding="utf-8")
    elif target == "mapping":
        path = case.fixture_root / "mapping.json"
        raw = read(path)
        raw["rows"][0]["candidate_digest"] = digest_bytes(b"wrong")
        path.write_text(json.dumps(raw), encoding="utf-8")
    else:
        case.output.write_bytes(case.output.read_bytes().replace(b"LOAD_N 20", b"LOAD_N 21"))
    result = case.coordinator.advance(state["project_revision"])
    assert result["state"] == "BLOCKED"
    assert len(case.harness.client().project_view()["runs"]) == 1


def test_b12_b17_owner_exit_and_journal_preserve_unknown(case):
    until(case, lambda s: s["next_action"] == "CLAIM_ONCE")
    owner = case.harness.children[0]
    write_new(owner.control / "stop.json", {})
    assert owner.process.wait(timeout=10) == 0
    state = until(case, lambda s: s["state"] == "ACCEPTANCE_UNKNOWN")
    assert case.ledger.inspect_budget()["held"] == 1
    journal = case.root / "research.sqlite3-journal"
    journal.write_bytes(b"M03B synthetic journal safety sentinel")
    before = journal.read_bytes()
    result = case.coordinator.advance(state["project_revision"])
    assert result["state"] == "JOURNAL_BLOCKED" and journal.read_bytes() == before
    # Retained deliberately; no stale-journal recovery or replacement owner.


@pytest.mark.parametrize("case", [{"faults": ["dispatch:after_claim"]}], indirect=True)
def test_b12_real_owner_paused_after_dispatch_exception(case):
    until(case, lambda s: s["state"] == "CLAIMED")
    deadline = time.monotonic() + 10
    while case.harness.client().health()["dispatch_enabled"]:
        assert time.monotonic() < deadline
        time.sleep(0.02)
    state = until(case, lambda s: s["state"] == "ACCEPTANCE_UNKNOWN")
    assert case.ledger.inspect_budget()["held"] == 1 and not state["decisions"]
    assert len(case.harness.client().project_view()["runs"]) == 1


@pytest.mark.parametrize("case", [{"barriers": ["dispatch:after_artifact"]}], indirect=True)
def test_b14_real_start_intent_then_invalid_fake_artifact(case):
    until(case, lambda s: s["state"] == "CLAIMED")
    owner = case.harness.children[0]
    owner.reached("dispatch:after_artifact")
    client = case.harness.client()
    rid = client.receipt(case.harness.requests[0]["idempotency_key"])["run_id"]
    assert client.run(rid)["execution"] == "START_INTENT"
    assert client.validations(rid) == []
    state = until(case, lambda s: s["state"] == "ACCEPTANCE_UNKNOWN")
    assert case.ledger.inspect_budget()["held"] == 1 and not state["decisions"]
    artifact = Path(case.harness.context.runtime_root) / "fake_runs" / rid / "result.json"
    assert artifact.resolve().is_relative_to(case.harness.root.resolve())
    artifact.write_bytes(b'{"simulation":false}')  # Controlled corruption of this test's Fake JSON only.
    owner.release("dispatch:after_artifact")
    case.harness.finished(rid)
    assert client.run(rid)["artifact_validation"] == "INVALID"
    assert client.validations(rid)[0]["verdict"] == "FAIL"
    assert case.coordinator.advance(state["project_revision"])["state"] == "ACCEPTANCE_UNKNOWN"
    assert len(client.project_view()["runs"]) == 1


def test_b11_budget_exhaustion_blocks_real_b(case):
    until(case, lambda s: s["state"] == "READY_B")
    a = facts(case, "A")["synthetic_request"]
    case.ledger.reserve_for_candidate(a["candidate_id"], a["candidate_digest"], 1,
        "outside-workflow", "fake_other", case.writer.inspect()["project_revision"])
    result = case.coordinator.advance(case.writer.inspect()["project_revision"])
    assert result["state"] == "BLOCKED" and result["reason"] == "BUDGET_BLOCKED"
    assert len(case.harness.client().project_view()["runs"]) == 1
    assert not (case.fixture_root / "B-submit-ticket.json").exists()
