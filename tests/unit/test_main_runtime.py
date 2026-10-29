"""F1 short transactions, exact lineage and UNKNOWN safety; no real server calls."""

import copy
import json
import os
from pathlib import Path
import sqlite3
import shutil
import subprocess
import sys
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import replace

import pytest

from aegiscae.contracts.research_contracts import canonical_json, digest_bytes
from aegiscae.research import main_runtime as core, main_runtime_rules as rules, main_runtime_store as journal
from aegiscae.research.continuation_rules import ContinuationEvent, policy_for

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "integration"))
from m03f1_support import (  # noqa: E402
    prepare_runtime, reopen_runtime, prepare_two_decision_runtime, logical_research_snapshot,
)
from m03c_support import checkpoint  # noqa: E402


@pytest.fixture
def case(tmp_path):
    return prepare_runtime(tmp_path / "case")


@pytest.fixture
def ab_case(tmp_path):
    return prepare_two_decision_runtime(tmp_path / "ab")


def test_r1_two_public_committed_decisions_and_logical_read_only(ab_case):
    case = ab_case
    before = logical_research_snapshot(case)
    decisions = case.coordinator.inspect()["decisions"]
    a, b = [e.value() for e in case.events]
    assert [a["step_id"], b["step_id"]] == ["A", "B"]
    assert b["sequence"] > a["sequence"] + 1
    assert a["source_transaction_id"] != b["source_transaction_id"]
    assert [a["decision_id"], b["decision_id"]] == [d["decision"]["decision_id"] for d in decisions]
    assert a["decision_digest"] != b["decision_digest"]
    assert case.port.oracle()["effects"] == 2 and case.ledger.inspect_budget()["charged"] == 2
    result = case.runtime.run_bounded(case.fake)
    assert [x["phase"] for x in result["items"]] == ["ACK_COMPLETED"] * 2
    assert case.fake.calls == 2 and len(case.fake.turns) == 3
    counts = (case.fake.calls, case.fake.preflights, case.fake.histories)
    assert reopen_runtime(case.fixture_root).run_bounded(case.fake) == result
    assert counts == (case.fake.calls, case.fake.preflights, case.fake.histories)
    assert logical_research_snapshot(case) == before
    assert case.port.oracle()["effects"] == 2 and case.ledger.inspect_budget()["charged"] == 2


def pause(case, *, command=None):
    state = case.runtime.status()
    return case.runtime.request_pause_after_current_turn(case.operator_id, command or str(uuid.uuid4()),
                                                       state["revision"], state["epoch"])


def resume(case):
    state = case.runtime.status()
    return case.runtime.resume_queue(case.operator_id, str(uuid.uuid4()), state["revision"], state["epoch"])


@pytest.mark.parametrize("point", ["before_claim", "intent_committed", "rpc_accepted"])
def test_r1_pause_linearization_and_no_owner_transfer(ab_case, monkeypatch, point):
    case = ab_case
    receipts = []
    if point == "before_claim":
        receipts.append(pause(case))
    else:
        def hook(stage):
            if stage == point:
                receipts.append(pause(case))
        monkeypatch.setattr(core, "_fault", hook)
    status = case.runtime.run_bounded(case.fake)
    assert status["pause_requested"] and status["items"][1]["persisted_phase"] == "QUEUED"
    assert case.fake.calls == (0 if point == "before_claim" else 1)
    receipt = receipts[0]
    assert receipt["active_turn_interrupted"] is False
    assert len(receipt["request"]["after_intents"]) == (0 if point == "before_claim" else 1)
    if point != "before_claim":
        assert status["items"][0]["phase"] == "ACK_COMPLETED"  # ACK did not overwrite pause.
    monkeypatch.setattr(core, "_fault", lambda stage: None)
    resume(case)
    assert case.runtime.run_bounded(case.fake)["items"][1]["phase"] == "ACK_COMPLETED"
    assert case.fake.calls == 2


def test_r1_pause_during_wait_other_process_and_unknown_precedence(ab_case):
    case = ab_case
    entered, release = threading.Event(), threading.Event()
    def waiting():
        entered.set()
        assert release.wait(45)
    case.fake.observed = waiting
    case.fake.fault = "capacity"
    with ThreadPoolExecutor(max_workers=2) as pool:
        future = pool.submit(case.runtime.run_bounded, case.fake)
        assert entered.wait(20)
        try:
            result = child(case, '''import sys,json,uuid
from m03f1_support import reopen_runtime
r=reopen_runtime(sys.argv[1]); s=r.status()
print(json.dumps(r.request_pause_after_current_turn(sys.argv[2],str(uuid.uuid4()),s['revision'],s['epoch'])))
''', case.operator_id)
            assert result.returncode == 0, result.stderr
            assert len(json.loads(result.stdout)["request"]["after_intents"]) == 1
            with pytest.raises(ValueError, match="OWNER_BUSY"):
                case.runtime.handle(case.events[1], case.fake)
        finally:
            release.set()
        status = future.result()
    assert status["paused"] and status["items"][0]["phase"] == "TURN_START_UNKNOWN"
    resume(case)
    assert case.runtime.run_bounded(case.fake)["items"][0]["phase"] == "TURN_START_UNKNOWN"
    assert case.fake.calls == 1


def test_r1_pause_idempotency_epoch_identity_and_resume_freshness(ab_case):
    case = ab_case
    command = str(uuid.uuid4())
    receipt = pause(case, command=command)
    assert case.runtime.request_pause_after_current_turn(case.operator_id, command, 1, 0) == receipt
    for operator, revision, epoch in ((str(uuid.uuid4()), 2, 0), (case.operator_id, 2, 1),
                                      (case.operator_id, True, 0), (case.operator_id, 2, False)):
        with pytest.raises(ValueError):
            case.runtime.request_pause_after_current_turn(operator, str(uuid.uuid4()), revision, epoch)
    with pytest.raises(ValueError):
        case.runtime.resume_queue(case.operator_id, command, 2, 0)
    with pytest.raises(ValueError, match="USE_EXPLICIT_R1_CONTROL"):
        case.runtime.control(case.operator_id, str(uuid.uuid4()), False, 2)
    case.writer.freeze_contract_bundle(replace(case.bundle, version=2),
                                      case.writer.inspect()["project_revision"], "r1-new-contract")
    with pytest.raises(ValueError, match="STALE_SOURCE"):
        resume(case)
    assert case.runtime.status()["paused"] and case.fake.calls == 0


@pytest.mark.parametrize("fault", ["lost_reply", "capacity", "wrong_marker"])
def test_r1_unknown_and_positive_only_reconciliation(ab_case, fault):
    test_unknown_never_retries_or_releases_second(ab_case, fault)


def test_r1_independent_process_history_and_status(ab_case):
    test_fresh_process_status_is_read_only(ab_case)
    test_new_process_resumes_same_history_for_event_two(ab_case)


def test_r1_two_independent_dispatchers_have_one_effect(ab_case):
    test_two_independent_coordinators_have_one_sender(ab_case)


@pytest.mark.parametrize("stage", ["initialized_before_commit", "initialized_after_commit"])
def test_r1_initialization_hard_exit_is_atomic(tmp_path, stage):
    case = prepare_two_decision_runtime(tmp_path / "initialize", initialize=False)
    config = case.fixture_root / "initialization.json"
    config.write_text(json.dumps({"policy": case.policy, "seed": case.fake.turns[0],
                                 "operator": case.operator_id}), encoding="utf-8")
    before = logical_research_snapshot(case)
    result = child(case, '''import sys,json,os
from m03f1_support import reopen_runtime
from aegiscae.research import main_runtime as core,main_runtime_store as j
r=reopen_runtime(sys.argv[1])
with open(sys.argv[2],encoding='utf-8') as f: data=json.load(f)
def crash(point):
 if point==sys.argv[3]: os._exit(23)
j._fault=crash
core.initialize_runtime(r.coordinator,data['policy'],data['seed'],data['operator'])
''', str(config), stage)
    assert result.returncode == 23, result.stderr
    if stage.endswith("before_commit"):
        with pytest.raises(ValueError, match="STORE_BUSY"):
            case.runtime.status()
    else:
        status = case.runtime.status()
        assert status["revision"] == 1 and len(status["items"]) == 2
        assert all(i["persisted_phase"] == "QUEUED" for i in status["items"])
    assert logical_research_snapshot(case) == before and case.fake.calls == 0


def test_r1_all_port_boundaries_have_no_database_lock(ab_case):
    test_intent_is_durable_and_no_sqlite_lock_during_any_port_method(ab_case)


@pytest.mark.parametrize("stage", ["turn_start_intent_before_commit", "turn_start_intent_after_commit",
    "rpc_accepted", "terminal_observed", "ack_completed_before_commit", "ack_completed_after_commit"])
def test_r1_hard_crash_and_fresh_process_no_duplicate(ab_case, stage):
    case = ab_case
    before = logical_research_snapshot(case)
    script = '''import os,sys
from m03f1_support import reopen_runtime,FakeCodexTurnPort
from aegiscae.research import main_runtime as core,main_runtime_store as j
from aegiscae.research.continuation_rules import ContinuationEvent
from aegiscae.contracts.research_contracts import canonical_json
r=reopen_runtime(sys.argv[1])
with j.connection_for(r.root) as c: _,s=r._read(c)
p=FakeCodexTurnPort(s['config']['policy'])
def crash(point):
 if point==sys.argv[2]: os._exit(23)
j._fault=core._fault=crash
r.handle(ContinuationEvent(canonical_json(s['config']['events'][0])),p)
'''
    result = child(case, script, stage)
    assert result.returncode == 23, result.stderr
    if "before_commit" in stage:
        with pytest.raises(ValueError, match="STORE_BUSY"):
            case.runtime.run_bounded(case.fake)
    else:
        status = reopen_runtime(case.fixture_root).handle(case.events[0], case.fake)
        assert status["items"][0]["phase"] in {"TURN_START_UNKNOWN", "TURN_STARTED", "ACK_COMPLETED"}
    assert case.fake.calls == 0 and logical_research_snapshot(case) == before


@pytest.mark.parametrize("point", ["pause_requested_before_commit", "pause_requested_after_commit"])
def test_r1_pause_commit_failure_preserves_owner_and_intent(ab_case, monkeypatch, point):
    case = ab_case
    def crash(stage):
        if stage == point:
            raise KeyboardInterrupt()
    monkeypatch.setattr(journal, "_fault", crash)
    with pytest.raises(KeyboardInterrupt):
        pause(case)
    assert case.runtime.status()["paused"] == (point == "pause_requested_after_commit")
    assert case.runtime.status()["epoch"] == 0 and case.fake.calls == 0


def test_r1_pause_wins_after_preflight_before_claim(ab_case):
    case = ab_case
    history = case.fake.history
    def paused_history():
        pause(case)
        return history()
    case.fake.history = paused_history
    status = case.runtime.handle(case.events[0], case.fake)
    assert status["paused"] and status["epoch"] == 0 and case.fake.calls == 0


def test_r1_source_advances_after_intent_before_dispatch(ab_case, monkeypatch):
    case = ab_case
    def change(stage):
        if stage == "intent_committed":
            case.writer.freeze_contract_bundle(replace(case.bundle, version=2),
                case.writer.inspect()["project_revision"], "r1-drift-before-rpc")
    monkeypatch.setattr(core, "_fault", change)
    state = case.runtime.handle(case.events[0], case.fake)
    assert state["items"][0]["phase"] == "TURN_START_UNKNOWN" and case.fake.calls == 0
    with pytest.raises(ValueError, match="STALE_SOURCE"):
        resume(case)


@pytest.mark.parametrize("fault", ["missing", "gap", "foreign", "changed", "reorder"])
def test_r1_read_adapter_rejects_broken_source_without_research_write(ab_case, monkeypatch, fault):
    # Fault the trusted read boundary after disk validation; never fabricate Project SQL records.
    case = ab_case
    project_type = type(case.reader.project)
    original = project_type._snapshot
    @contextmanager
    def injected(self, *args, **kwargs):
        with original(self, *args, **kwargs) as (connection, meta, bundles, events):
            events = copy.deepcopy(events)
            last = next(e for e in reversed(events) if e["kind"] == "WORKFLOW_RECORDED"
                        and e["workflow"]["action"] == "DECIDE")
            if fault == "missing":
                events.remove(last)
            elif fault == "gap":
                last["sequence"] += 1
            elif fault == "foreign":
                last["workflow"]["workflow_id"] = "workflow_" + "f" * 32
            elif fault == "changed":
                last["event_digest"] = digest_bytes(b"changed")
            else:
                events.reverse()
            yield connection, meta, bundles, events
    before = logical_research_snapshot(case)
    monkeypatch.setattr(project_type, "_snapshot", injected)
    with pytest.raises(ValueError):
        case.runtime.handle(case.events[0], case.fake)
    assert case.fake.calls == 0 and logical_research_snapshot(case) == before


def test_r1_pending_or_stop_source_cannot_gain_two_decision_policy(tmp_path):
    legacy = prepare_runtime(tmp_path / "legacy")
    with pytest.raises(ValueError, match="SOURCE_DECISION_SCOPE"):
        rules.sources(legacy.reader, two_decisions=True)
    with pytest.raises(ValueError):
        legacy.runtime.request_pause_after_current_turn(legacy.operator_id, str(uuid.uuid4()), 1, 0)


def test_r1_reordered_or_foreign_event_and_candidate_file(ab_case):
    case = ab_case
    assert case.runtime.handle(case.events[1], case.fake)["items"][1]["phase"] == "WAITING_PREDECESSOR"
    value = case.events[0].value()
    value["decision_digest"] = digest_bytes(b"other decision")
    with pytest.raises(ValueError, match="EVENT_CONFLICT"):
        case.runtime.handle(ContinuationEvent(canonical_json(value)), case.fake)
    path = case.workspace._root / "staging" / case.definition.candidates[1].output_identity / "candidate.txt"
    path.write_bytes(path.read_bytes() + b"tamper")
    with pytest.raises(ValueError):
        case.runtime.handle(case.events[0], case.fake)
    assert case.fake.calls == 0


def test_two_distinct_commits_and_two_ack_preserve_research(case):
    before = checkpoint(case)
    preserved = {name: (case.root / name).read_bytes() for name in
                 ("research.sqlite3", "continuation-outbox-v1.sqlite3")}
    a, b = [e.value() for e in case.events]
    assert b["sequence"] == a["sequence"] + 1
    assert b["source_transaction_id"] != a["source_transaction_id"]
    assert b["event_type"] == "WORKFLOW_STOP_RECORDED"
    assert len(case.coordinator.inspect()["decisions"]) == 1  # Never invent another science decision.
    assert case.runtime.handle(case.events[1], case.fake)["items"][1]["phase"] == "WAITING_PREDECESSOR"
    assert case.fake.calls == case.fake.preflights == 0
    result = case.runtime.run_bounded(case.fake)
    assert [x["phase"] for x in result["items"]] == ["ACK_COMPLETED"] * 2
    assert result["epoch"] == 2 and len(case.fake.turns) == 3 and case.fake.calls == 2
    observed = (case.fake.calls, case.fake.preflights, case.fake.histories)
    assert reopen_runtime(case.fixture_root).run_bounded(case.fake) == result
    assert observed == (case.fake.calls, case.fake.preflights, case.fake.histories)
    assert checkpoint(case) == before
    assert all((case.root / name).read_bytes() == body for name, body in preserved.items())


def test_intent_is_durable_and_no_sqlite_lock_during_any_port_method(case):
    # A second writer can enter both stores while every external method is running.
    base = case.fake
    class Port:
        def free(self):
            for name in ("research.sqlite3", journal.FILENAME):
                with sqlite3.connect(case.root / name, timeout=0) as connection:
                    connection.execute("BEGIN IMMEDIATE")
                    connection.rollback()
        def preflight(self):
            self.free()
            return base.preflight()
        def history(self):
            self.free()
            return base.history()
        def start_turn(self, text, schema):
            self.free()
            status = reopen_runtime(case.fixture_root).status()
            assert status["items"][base.calls]["persisted_phase"] == "TURN_START_INTENT"
            return base.start_turn(text, schema)
        def terminal(self, turn_id):
            self.free()
            return base.terminal(turn_id)
    assert case.runtime.run_bounded(Port())["items"][1]["phase"] == "ACK_COMPLETED"


@pytest.mark.parametrize("fault", ["lost_reply", "terminal_loss", "capacity", "server_exit", "wrong_marker", "failed"])
def test_unknown_never_retries_or_releases_second(case, fault):
    case.fake.fault = fault
    first = case.runtime.run_bounded(case.fake)
    assert first["items"][0]["phase"] == "TURN_START_UNKNOWN"
    assert first["items"][1]["phase"] == "WAITING_PREDECESSOR"
    assert case.fake.calls == 1
    assert reopen_runtime(case.fixture_root).run_bounded(case.fake) == first
    result = case.runtime.reconcile(case.fake)
    assert result["items"][0]["phase"] == ("ACK_COMPLETED" if fault in
        {"lost_reply", "terminal_loss", "server_exit"} else "TURN_START_UNKNOWN")
    assert case.fake.calls == 1


@pytest.mark.parametrize("field", ["thread_id", "owner_id", "config_digest", "authenticated", "status",
    "tools_enabled", "network_access", "native_goal", "automatic_sources_disabled", "previous_owner_exited"])
def test_preflight_refuses_unsafe_or_dual_owner_before_intent(case, field):
    case.fake.fault = field
    with pytest.raises(ValueError):
        case.runtime.handle(case.events[0], case.fake)
    assert case.fake.calls == 0 and case.runtime.status()["epoch"] == 0


@pytest.mark.parametrize("field", ["sequence", "source_event_digest", "project_revision", "event_type", "extra"])
def test_altered_event_never_gets_a_second_key(case, field):
    value = case.events[0].value()
    value[field] = "injected"
    with pytest.raises(ValueError, match="EVENT_CONFLICT"):
        case.runtime.handle(ContinuationEvent(canonical_json(value)), case.fake)
    assert case.fake.calls == 0


@pytest.mark.parametrize("fault", ["wrong_thread", "duplicate", "missing", "tools", "seed", "input"])
def test_incomplete_conflicting_history_stays_unknown(case, fault):
    case.fake.fault = "lost_reply"
    case.runtime.handle(case.events[0], case.fake)
    if fault == "duplicate":
        case.fake.turns.append(copy.deepcopy(case.fake.turns[-1]))
    elif fault == "missing":
        case.fake.turns.pop()
    elif fault == "tools":
        case.fake.turns[-1]["tools_used"] = 1
    elif fault == "seed":
        case.fake.turns[0]["input_digest"] = digest_bytes(b"changed")
    elif fault == "input":
        case.fake.turns[-1]["input_digest"] = digest_bytes(b"changed")
    else:
        case.fake.turns[-1]["thread_id"] = str(uuid.uuid4())
    assert case.runtime.reconcile(case.fake)["items"][0]["phase"] == "TURN_START_UNKNOWN"
    assert case.fake.calls == 1


def test_concurrent_sender_and_pause_fail_busy_not_takeover(case):
    entered, release = threading.Event(), threading.Event()
    def observed():
        entered.set()
        assert release.wait(20)
    case.fake.observed = observed
    with ThreadPoolExecutor(max_workers=2) as pool:
        future = pool.submit(case.runtime.handle, case.events[0], case.fake)
        assert entered.wait(20)
        try:
            with pytest.raises(ValueError, match="OWNER_BUSY"):
                reopen_runtime(case.fixture_root).handle(case.events[0], case.fake)
            with pytest.raises(ValueError, match="OWNER_BUSY"):
                case.runtime.control(case.operator_id, str(uuid.uuid4()), True, 2)
        finally:
            release.set()
        assert future.result()["items"][0]["phase"] == "ACK_COMPLETED"
    assert case.fake.calls == 1


def test_pause_control_identity_revision_and_idempotency(case):
    command = str(uuid.uuid4())
    with pytest.raises(ValueError):
        case.runtime.control(str(uuid.uuid4()), command, True, 1)
    with pytest.raises(ValueError):
        case.runtime.control(case.operator_id, command, True, 2)
    with pytest.raises(ValueError):
        case.runtime.control(case.operator_id, command, True, True)
    paused = case.runtime.control(case.operator_id, command, True, 1)
    assert paused["paused"]
    assert case.runtime.control(case.operator_id, command, True, 1) == paused
    assert case.runtime.run_bounded(case.fake) == paused and case.fake.calls == 0
    with pytest.raises(ValueError, match="CONTROL_CONFLICT"):
        case.runtime.control(case.operator_id, command, False, 1)
    case.runtime.control(case.operator_id, str(uuid.uuid4()), False, paused["revision"])
    assert case.runtime.run_bounded(case.fake)["items"][1]["phase"] == "ACK_COMPLETED"


@pytest.mark.parametrize("stage", ["intent_committed", "rpc_accepted", "terminal_observed"])
def test_interrupted_call_stack_cannot_dispatch_again(case, monkeypatch, stage):
    def crash(point):
        if point == stage:
            raise KeyboardInterrupt()
    monkeypatch.setattr(core, "_fault", crash)
    with pytest.raises(KeyboardInterrupt):
        case.runtime.run_bounded(case.fake)
    assert reopen_runtime(case.fixture_root).run_bounded(case.fake)["items"][1]["phase"] == "WAITING_PREDECESSOR"
    assert case.fake.calls == (0 if stage == "intent_committed" else 1)


@pytest.mark.parametrize("stage", ["turn_start_intent_before_commit", "turn_start_intent_after_commit",
                                  "ack_completed_before_commit", "ack_completed_after_commit"])
def test_transaction_interrupts(case, monkeypatch, stage):
    def crash(point):
        if point == stage:
            raise KeyboardInterrupt()
    monkeypatch.setattr(journal, "_fault", crash)
    with pytest.raises(KeyboardInterrupt):
        case.runtime.handle(case.events[0], case.fake)
    status = reopen_runtime(case.fixture_root).status()
    expected = {"turn_start_intent_before_commit": "QUEUED", "turn_start_intent_after_commit": "TURN_START_UNKNOWN",
                "ack_completed_before_commit": "TURN_STARTED", "ack_completed_after_commit": "ACK_COMPLETED"}
    assert status["items"][0]["phase"] == expected[stage]


def child(case, script, *args):
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": os.pathsep.join([
        str(Path(__file__).resolve().parents[2] / "src"), str(Path(__file__).resolve().parents[1] / "integration")])}
    return subprocess.run([sys.executable, "-B", "-c", script, str(case.fixture_root), *args],
                          env=env, capture_output=True, text=True, timeout=60)


def test_fresh_process_status_is_read_only(case):
    before = (case.root / journal.FILENAME).read_bytes()
    result = child(case, "import json,sys; from m03f1_support import reopen_runtime; "
                   "print(json.dumps(reopen_runtime(sys.argv[1]).status()))")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == case.runtime.status()
    assert (case.root / journal.FILENAME).read_bytes() == before


@pytest.mark.parametrize("stage", ["turn_start_intent_before_commit", "turn_start_intent_after_commit",
                                  "ack_completed_before_commit", "ack_completed_after_commit"])
def test_hard_exit_never_repairs_or_resubmits(case, stage):
    script = '''import os,sys
from m03f1_support import reopen_runtime,FakeCodexTurnPort
from aegiscae.research import main_runtime_store as j
from aegiscae.research.main_runtime_rules import sources
r=reopen_runtime(sys.argv[1])
with j.connection_for(r.root) as c: _,s=r._read(c)
p=FakeCodexTurnPort(s['config']['policy'])
def crash(point):
 if point==sys.argv[2]: os._exit(23)
j._fault=crash
r.handle(sources(r.coordinator)[0][0],p)
'''
    result = child(case, script, stage)
    assert result.returncode == 23, result.stderr
    if "before_commit" in stage:
        assert Path(str(case.root / journal.FILENAME) + "-journal").exists()
        with pytest.raises(ValueError, match="STORE_BUSY"):
            case.runtime.run_bounded(case.fake)
    else:
        status = case.runtime.handle(case.events[0], case.fake)
        assert status["items"][0]["phase"] in {"TURN_START_UNKNOWN", "ACK_COMPLETED"}
    assert case.fake.calls == 0


@pytest.mark.parametrize("database", ["research.sqlite3", journal.FILENAME])
@pytest.mark.parametrize("suffix", ["-journal", "-wal", "-shm"])
def test_old_journal_blocks_without_cleanup(case, database, suffix):
    path = case.root / (database + suffix)
    path.write_bytes(b"retained")
    with pytest.raises(ValueError, match="STORE_BUSY"):
        case.runtime.run_bounded(case.fake)
    assert path.read_bytes() == b"retained" and case.fake.calls == 0


def test_revision_advancement_preserves_old_receipt_but_blocks_new_dispatch(case):
    case.runtime.handle(case.events[0], case.fake)
    rev = case.writer.inspect()["project_revision"]
    case.writer.freeze_contract_bundle(replace(case.bundle, version=2), rev, "new_version")
    assert case.runtime.status()["items"][0]["phase"] == "ACK_COMPLETED"
    with pytest.raises(ValueError, match="STALE_SOURCE"):
        case.runtime.handle(case.events[1], case.fake)
    assert case.fake.calls == 1


def test_e1_policy_cannot_authorize_two_events(case):
    p = case.policy
    old = policy_for(p["owner_id"], p["thread_id"], p["config_digest"], p["seed_turn_id"])
    with pytest.raises(ValueError, match="RUNTIME_POLICY_INVALID"):
        rules.validate_runtime_policy(old)


def test_stale_before_initialization_rejected(case):
    case.writer.freeze_contract_bundle(replace(case.bundle, version=2),
                                      case.writer.inspect()["project_revision"], "next")
    with pytest.raises(ValueError, match="RUNTIME_CONFIG"):
        core.initialize_runtime(case.reader, case.policy, case.fake.turns[0], case.operator_id)
    assert case.fake.calls == 0


def test_seed_id_cannot_be_accepted_as_event_turn(case):
    class Port:
        preflight = case.fake.preflight
        history = case.fake.history
        def start_turn(self, text, schema):
            case.fake.start_turn(text, schema)
            return case.policy["seed_turn_id"]
        terminal = case.fake.terminal
    status = case.runtime.handle(case.events[0], Port())
    assert status["items"][0]["phase"] == "TURN_START_UNKNOWN"
    assert status["items"][0]["turn_id"] is None


@pytest.mark.parametrize("field", ["source_revision", "max_events", "native_goals", "missing_time"])
def test_rehashed_metadata_corruption_detected(case, field):
    path = case.root / journal.FILENAME
    with sqlite3.connect(path) as connection:
        raw = json.loads(connection.execute("SELECT body FROM events WHERE sequence=1").fetchone()[0])
        if field == "native_goals":
            raw["data"]["policy"]["native_goals_allowed"] = True
        elif field == "missing_time":
            del raw["at_utc"]
        else:
            raw["data"][field] = 999
        body = canonical_json(raw)
        connection.execute("UPDATE events SET body=?,digest=? WHERE sequence=1", (body, digest_bytes(body)))
    with pytest.raises((ValueError, KeyError)):
        case.runtime.run_bounded(case.fake)
    assert case.fake.calls == 0


def test_extra_schema_is_not_silently_accepted(case):
    with sqlite3.connect(case.root / journal.FILENAME) as connection:
        connection.execute("CREATE TABLE unexpected (value TEXT)")
    with pytest.raises(ValueError, match="UNSUPPORTED_RUNTIME_SCHEMA"):
        case.runtime.status()


def test_clock_regression_blocks_before_send(case, monkeypatch):
    from aegiscae.research import project
    monkeypatch.setattr(project, "_utc", lambda: "2000-01-01T00:00:00.000000Z")
    with pytest.raises(ValueError, match="POLICY_EXPIRED"):
        case.runtime.handle(case.events[0], case.fake)
    assert case.fake.calls == 0


@pytest.mark.parametrize("stage", ["initialized_before_commit", "initialized_after_commit"])
def test_initialization_hard_exit_preserves_incomplete_store(case, stage):
    script = '''import os,sys
from pathlib import Path
from m03f1_support import prepare_runtime
from aegiscae.research import main_runtime_store as j
def crash(point):
 if point==sys.argv[2]: os._exit(23)
j._fault=crash
prepare_runtime(Path(sys.argv[1])/'init-child')
'''
    result = child(case, script, stage)
    assert result.returncode == 23, result.stderr
    root = case.fixture_root / "init-child"
    path = root / "research" / journal.FILENAME
    assert path.exists()
    before = path.read_bytes()
    if "before" in stage:
        with pytest.raises(ValueError, match="STORE_BUSY"):
            reopen_runtime(root).status()
    else:
        assert reopen_runtime(root).status()["items"][0]["phase"] == "QUEUED"
    assert path.read_bytes() == before


def test_unknown_reconciliation_survives_project_revision_change(case):
    case.fake.fault = "lost_reply"
    case.runtime.handle(case.events[0], case.fake)
    case.writer.freeze_contract_bundle(replace(case.bundle, version=2),
                                      case.writer.inspect()["project_revision"], "next")
    assert case.runtime.reconcile(case.fake)["items"][0]["phase"] == "ACK_COMPLETED"
    with pytest.raises(ValueError, match="STALE_SOURCE"):
        case.runtime.handle(case.events[1], case.fake)


def test_new_process_resumes_same_history_for_event_two(case):
    case.runtime.handle(case.events[0], case.fake)
    capture = case.fixture_root / "offline-history.json"
    capture.write_text(json.dumps(case.fake.turns), encoding="utf-8")
    result = child(case, '''import json,sys
from m03f1_support import reopen_runtime,FakeCodexTurnPort
from aegiscae.research import main_runtime_store as j
r=reopen_runtime(sys.argv[1])
with j.connection_for(r.root) as c: _,s=r._read(c)
p=FakeCodexTurnPort(s['config']['policy'])
with open(sys.argv[2],encoding='utf-8') as f: p.turns=json.load(f)
result=r.run_bounded(p)
print(json.dumps({'phases':[i['phase'] for i in result['items']],'starts':p.calls,'history':len(p.turns)}))
''', str(capture))
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {"phases": ["ACK_COMPLETED"] * 2, "starts": 1, "history": 3}


def test_two_independent_coordinators_have_one_sender(case):
    script = '''import json,sys,time
from pathlib import Path
from m03f1_support import reopen_runtime,FakeCodexTurnPort
from aegiscae.research import main_runtime_store as j
from aegiscae.research.main_runtime_rules import sources
r=reopen_runtime(sys.argv[1])
with j.connection_for(r.root) as c: _,s=r._read(c)
p=FakeCodexTurnPort(s['config']['policy'])
def observed():
 with (Path(sys.argv[1])/('effect-'+sys.argv[2])).open('x') as f: f.write('one start')
 time.sleep(1)
p.observed=observed
try: r.handle(sources(r.coordinator,two_decisions=s['config']['schema']=='bounded-ack-runtime-r1')[0][0],p)
except ValueError as e:
 if str(e) not in {'OWNER_BUSY','STORE_BUSY'}: raise
print(json.dumps({'starts':p.calls}))
'''
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda tag: child(case, script, tag), ["first", "second"]))
    assert all(r.returncode == 0 for r in results), [r.stderr for r in results]
    assert sum(json.loads(r.stdout)["starts"] for r in results) == 1
    assert len(list(case.fixture_root.glob("effect-*"))) == 1


def test_no_overwrite_or_implicit_initialization(case):
    before = (case.root / journal.FILENAME).read_bytes()
    with pytest.raises(ValueError, match="RUNTIME_ALREADY_EXISTS"):
        core.initialize_runtime(case.reader, case.policy, case.fake.turns[0], case.operator_id)
    assert (case.root / journal.FILENAME).read_bytes() == before


def test_read_only_status_cannot_initialize(tmp_path):
    empty = prepare_runtime(tmp_path / "no-runtime", initialize=False)
    with pytest.raises(ValueError):
        empty.runtime.status()
    assert not (empty.root / journal.FILENAME).exists()
    assert not (empty.root / journal.LOCKFILE).exists()


def test_replaced_sidecar_and_hardlink_refused(case):
    path = case.root / journal.FILENAME
    saved = case.root / "original-store-retained"
    path.rename(saved)
    shutil.copyfile(saved, path)
    with pytest.raises(ValueError, match="RUNTIME_IDENTITY_MISMATCH"):
        case.runtime.status()
    os.link(path, case.root / "linked-store")
    with pytest.raises(ValueError, match="FILE_IDENTITY_UNSAFE"):
        case.runtime.status()


def test_payload_limits_and_corrupt_owner_fail_closed(case):
    with pytest.raises(ValueError):
        case.runtime.run_bounded(case.fake, max_events=3)
    with pytest.raises(ValueError):
        case.runtime.run_bounded(case.fake, max_events=True)
    (case.root / journal.LOCKFILE).write_bytes(b"contaminated")
    with pytest.raises(ValueError, match="OWNER_INTEGRITY"):
        case.runtime.handle(case.events[0], case.fake)
    assert case.fake.calls == 0


def test_input_and_candidate_tamper_rejected(case):
    path = next((case.workspace._root / "staging").glob("*/candidate.txt"))
    path.write_bytes(path.read_bytes().replace(b"40", b"41"))
    with pytest.raises(ValueError):
        case.runtime.handle(case.events[0], case.fake)
    assert case.fake.calls == 0
