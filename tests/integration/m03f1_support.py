"""Synthetic preparation only. No Codex or AF server launch; STOP is not science."""

import copy
import sys
import uuid
from pathlib import Path

from aegiscae.contracts.research_contracts import digest_bytes
from aegiscae.research import main_runtime as core, main_runtime_rules as rules

sys.path.insert(0, str(Path(__file__).parent))
from m03e1_support import FakePort, prepare_continuation, reopen_reader  # noqa: E402


class FakeCodexTurnPort(FakePort):
    def __init__(self, policy, *, fault=None):
        super().__init__(policy, None, fault=fault)
        self.preflights, self.histories = 0, 0
        self.turns[0]["input_digest"] = digest_bytes(rules.SEED.encode())

    def preflight(self):
        self.preflights += 1
        result = {**super().preflight(), "native_goal": None, "automatic_sources_disabled": True,
                  "previous_owner_exited": True}
        if self.fault in {"native_goal", "automatic_sources_disabled", "previous_owner_exited"}:
            result[self.fault] = "unverified"
        return result

    def history(self):
        self.histories += 1
        return super().history()

    def start_turn(self, text, schema):
        self.calls += 1
        if self.observed:
            self.observed()
        if self.fault == "capacity":
            raise RuntimeError("CAPACITY")
        turn = {"thread_id": self.policy["thread_id"], "turn_id": str(uuid.uuid4()),
            "status": "completed", "input_digest": digest_bytes(text.encode()), "tools_used": 0,
            "output": {k: v["const"] for k, v in schema["properties"].items()}}
        self.turns.append(turn)
        if self.fault in {"lost_reply", "server_exit"}:
            raise TimeoutError("RESPONSE_UNKNOWN")
        if self.fault == "wrong_marker":
            turn["output"]["event_key"] = digest_bytes(b"wrong")
        if self.fault == "failed":
            turn["status"] = "failed"
        return turn["turn_id"]


def prepare_runtime(root, *, initialize=True):
    case = prepare_continuation(root)
    # A's scientific decision is committed by the existing test Workflow.
    # A separate trusted STOP control decision is committed BEFORE runtime setup.
    case.coordinator._block("HUMAN_REVIEW_REQUIRED", case.writer.inspect()["project_revision"])
    case.events, _ = rules.sources(case.reader)
    old = case.policy
    case.policy = rules.runtime_policy(old["owner_id"], old["thread_id"], old["config_digest"], old["seed_turn_id"])
    case.operator_id = str(uuid.uuid4())
    case.fake = FakeCodexTurnPort(case.policy)
    if initialize:
        core.initialize_runtime(case.reader, case.policy, copy.deepcopy(case.fake.turns[0]), case.operator_id)
    case.runtime = core.MainRuntime(case.reader)
    return case


def reopen_runtime(root):
    return core.MainRuntime(reopen_reader(Path(root)))


def prepare_two_decision_runtime(root, *, initialize=True):
    """R1 fixture writes end before Runtime starts; no model/server/AF calls."""
    from m03c_support import save
    from aegiscae.research import project, workflow
    from aegiscae.research.workflow_rules import plain
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "unit"))
    from test_synthetic_workflow import finish, workflow_case
    root = Path(root)
    root.mkdir()
    case = workflow_case(root)
    done = finish(case)  # Public advance validates and commits A and B separately.
    assert len(done["decisions"]) == 2 and case.port.oracle()["effects"] == 2
    save(root / "definition.json", plain(case.definition))
    case.fixture_root = root
    case.reader = workflow.WorkflowCoordinator(project.open_existing_readonly(case.root),
                                               case.workspace, case.definition.workflow_id)
    case.events, _ = rules.sources(case.reader, two_decisions=True)
    case.policy = rules.runtime_policy(str(uuid.uuid4()), str(uuid.uuid4()),
        digest_bytes(b"offline-r1-config"), str(uuid.uuid4()), two_decisions=True)
    case.operator_id = str(uuid.uuid4())
    case.fake = FakeCodexTurnPort(case.policy)
    if initialize:
        core.initialize_runtime(case.reader, case.policy, copy.deepcopy(case.fake.turns[0]), case.operator_id)
    case.runtime = core.MainRuntime(case.reader)
    return case


def logical_research_snapshot(case):
    """Read-only logical schema/table snapshot, independent of SQLite file layout."""
    import sqlite3
    with sqlite3.connect((case.root / "research.sqlite3").as_uri() + "?mode=ro", uri=True) as db:
        db.execute("PRAGMA query_only=ON")
        return tuple(db.iterdump())
