"""Offline doubles and fresh synthetic A-only test preparation; never starts Codex."""

import copy
import sys
import uuid
from pathlib import Path

from aegiscae.contracts.research_contracts import digest_bytes
from aegiscae.research import continuation, project, workflow
from aegiscae.research.continuation_rules import policy_for

sys.path.insert(0, str(Path(__file__).parent))
from m03c_support import prepare, until  # noqa: E402


def prepare_continuation(root, *, policy=None, narrative=None):
    case = prepare(root, narrative=narrative)
    until(case.coordinator, lambda s: s["state"] == "READY_B")
    # Explicit fixture preparation ends here. Subsequent continuation owns no writer/ports.
    case.reader = workflow.WorkflowCoordinator(project.open_existing_readonly(case.root),
        case.workspace, case.definition.workflow_id)
    case.event = continuation.observe(case.reader)
    case.policy = policy or policy_for(str(uuid.uuid4()), str(uuid.uuid4()),
                                      digest_bytes(b"offline_test_config"), str(uuid.uuid4()))
    continuation.initialize_outbox(case.reader, case.event, case.policy)
    case.outbox = continuation.ContinuationOutbox(case.reader)
    case.fake = FakePort(case.policy, case.event)
    return case


class FakePort:
    def __init__(self, policy, event, *, fault=None):
        self.policy, self.event, self.fault = policy, event, fault
        self.calls, self.observed = 0, None
        self.turns = [{"thread_id": policy["thread_id"], "turn_id": policy["seed_turn_id"],
            "status": "completed", "input_digest": digest_bytes(b"seed"),
            "output": {"status": "SEED_ACK", "qualification": "NOT_ABAQUS_QUALIFIED"}, "tools_used": 0}]

    def preflight(self):
        p = self.policy
        result = {"owner_id": p["owner_id"], "thread_id": p["thread_id"], "cli_version": p["cli_version"],
            "config_digest": p["config_digest"], "authenticated": True, "sandbox": "read-only",
            "network_access": False, "approval": "never", "tools_enabled": False,
            "owned": True, "status": "idle"}
        if self.fault in result:
            result[self.fault] = "wrong"
        return result

    def history(self):
        return copy.deepcopy(self.turns)

    def start_turn(self, text, schema):
        self.calls += 1
        if self.observed:
            self.observed()
        if self.fault == "capacity":
            raise RuntimeError("Selected model is at capacity")
        turn = {"thread_id": self.policy["thread_id"], "turn_id": str(uuid.uuid4()),
            "status": "completed", "input_digest": digest_bytes(text.encode()), "tools_used": 0,
            "output": {"status": "CONTINUATION_ACK", "event_key": self.event.key,
                "evidence_refs": self.event.value()["brief"]["evidence_refs"],
                "qualification": "NOT_ABAQUS_QUALIFIED"}}
        self.turns.append(turn)
        if self.fault == "lost_reply":
            raise TimeoutError("LOST_RESPONSE")
        return turn["turn_id"]

    def terminal(self, turn_id):
        if self.fault == "terminal_loss":
            raise TimeoutError("LOST_TERMINAL")
        return {"thread_id": self.policy["thread_id"], "turn_id": turn_id, "status": "completed"}


def reopen_reader(root):
    from m03c_support import read
    from aegiscae.research.mutation import SyntheticWorkspace
    definition = read(Path(root) / "definition.json")
    return workflow.WorkflowCoordinator(project.open_existing_readonly(Path(root) / "research"),
        SyntheticWorkspace(Path(root) / "synthetic", definition["candidates"][0]["workspace_id"]),
        definition["workflow_id"])
