"""Explicit one-shot M03-E1 smoke. Not pytest-collected; no automatic CLI entrypoint."""

import json
import uuid
from pathlib import Path

from aegiscae.contracts.research_contracts import canonical_json, digest_bytes, strict_json
from aegiscae.research.continuation_rules import policy_for
from m03c_support import checkpoint
from m03e1_protocol import OwnedAppServer, VERSION, write_new
from m03e1_support import prepare_continuation


class OwnedTurnPort:
    """Only the retained server's explicitly registered seed thread; no arbitrary RPC surface."""
    def __init__(self, server, owner):
        assert server.thread_id == owner["thread_id"]
        self.server, self.owner = server, owner
        self.calls, self.terminals = 0, []

    def preflight(self):
        s, owner = self.server, self.owner
        thread = s.read()["thread"]
        assert thread["id"] == owner["thread_id"] and Path(thread["cwd"]) == s.work
        assert thread["ephemeral"] is False and thread["cliVersion"] == VERSION
        return {"owner_id": owner["owner_id"], "thread_id": s.thread_id, "cli_version": VERSION,
            "config_digest": owner["config_digest"], "authenticated": s.preflight["auth_confirmed"],
            "sandbox": "read-only", "network_access": False, "approval": "never",
            "tools_enabled": False, "owned": True, "status": thread["status"]["type"]}

    def history(self):
        result = []
        for turn in self.server.history():
            users = [item for item in turn["items"] if item["type"] == "userMessage"]
            finals = [item for item in turn["items"] if item["type"] == "agentMessage"
                      and item.get("phase") == "final_answer"]
            assert len(users) == 1 and len(finals) <= 1
            content = users[0]["content"]
            assert len(content) == 1 and content[0]["type"] == "text"
            result.append({"thread_id": self.server.thread_id, "turn_id": turn["id"],
                "status": turn["status"], "input_digest": digest_bytes(content[0]["text"].encode()),
                "output": strict_json(finals[0]["text"]) if finals else None,
                "tools_used": sum(item["type"] not in {"userMessage", "agentMessage", "reasoning"}
                                  for item in turn["items"])})
        return result

    def start_turn(self, text, schema):
        assert self.calls == 0
        self.calls += 1  # No retry even if the following transport send fails.
        write_new(self.server.root / "event-dispatch-attempt.json", {"thread_id": self.server.thread_id,
            "input_digest": digest_bytes(text.encode()), "attempt": 1})
        response = self.server.start(text, schema)
        write_new(self.server.root / "event-start-response.json", response)
        return response["turn"]["id"]

    def terminal(self, turn_id):
        notification = self.server.wait_terminal(turn_id)
        write_new(self.server.root / "event-terminal.json", notification)
        self.terminals.append(notification)
        return {"thread_id": notification["params"]["threadId"],
            "turn_id": notification["params"]["turn"]["id"],
            "status": notification["params"]["turn"]["status"]}


def run_owned_smoke(root, executable):
    root = Path(root)
    seed = json.loads((root / "seed-evidence.json").read_text())
    registration = json.loads((root / "persistent-owned-thread.json").read_text())
    assert seed["thread_id"] == registration["thread_id"]
    assert seed["terminal"]["params"]["turn"]["status"] == "completed"
    write_new(root / "smoke-launch-once.json", {"thread_id": seed["thread_id"], "max_event_turns": 1})
    s = OwnedAppServer(executable, root, "event-server", thread_id=seed["thread_id"])
    try:
        resumed = s.resume()
        assert resumed["model"] == registration["model"]
        owner = {"owner_id": str(uuid.uuid4()), "thread_id": s.thread_id,
            "seed_turn_id": seed["seed_turn_id"],
            "config_digest": digest_bytes(canonical_json({"preflight": s.preflight,
                "cwd": str(s.work), "model": resumed["model"], "sandbox": resumed["sandbox"],
                "approval": resumed["approvalPolicy"]}))}
        write_new(root / "continuation-owner.json", owner)
        port = OwnedTurnPort(s, owner)
        baseline = port.history()
        assert len(baseline) == 1 and baseline[0]["turn_id"] == owner["seed_turn_id"]
        policy = policy_for(owner["owner_id"], owner["thread_id"], owner["config_digest"], owner["seed_turn_id"])
        case = prepare_continuation(root / "event-case", policy=policy)
        before = checkpoint(case)
        source_digest = digest_bytes((case.root / "research.sqlite3").read_bytes())
        write_new(root / "event-source.json", {"event": case.event.value(), "event_key": case.event.key,
            "policy": policy, "before": before, "source_database_digest": source_digest})
        result = case.outbox.handle(case.event, port)
        write_new(root / "event-receipt.json", result)
        assert result["phase"] == "TURN_COMPLETED", "STOP_NO_RETRY"
        assert case.outbox.handle(case.event, port) == result
        assert case.outbox.handle(case.event, port) == result
        after = checkpoint(case)
        assert before == after and source_digest == digest_bytes((case.root / "research.sqlite3").read_bytes())
        history = port.history()
        assert len(history) == 2 and port.calls == 1
        write_new(root / "smoke-evidence.json", {"receipt": result, "history": history,
            "dispatch_count": port.calls, "redelivery_count": 2, "before": before, "after": after,
            "source_database_unchanged": True, "preflight": s.preflight, "trace": s.trace})
        return {"thread_id": s.thread_id, "turn_id": result["turn_id"], "status": result["phase"],
                "dispatch_count": port.calls, "history_count": len(history)}
    finally:
        s.close()
