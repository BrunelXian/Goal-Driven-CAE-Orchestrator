"""Finite two-event ACK coordinator; no scheduler, process launcher or research writer."""

from aegiscae.contracts.research_contracts import canonical_json, digest_bytes, require
from aegiscae.research import main_runtime_rules as rules, main_runtime_store as journal, project
from aegiscae.research.continuation_rules import ContinuationEvent


def _fault(stage):
    """Trusted fault injection only."""


def initialize_runtime(coordinator, policy, seed, operator_id):
    rules.validate_runtime_policy(policy)
    r1 = policy["schema"] == "bounded-ack-policy-r1"
    events, revision = rules.sources(coordinator, two_decisions=r1)
    config = {"schema": "bounded-ack-runtime-r1" if r1 else "bounded-ack-runtime-v1", "policy": policy,
        "events": [e.value() for e in events], "source_revision": revision,
        "max_events": 2, "seed": seed, "operator_id": operator_id, "sidecar_identity": []}
    rules.validate_config(config)
    rules.valid_time(policy)
    root = coordinator.project._root
    journal.create_files(root)
    config["sidecar_identity"] = journal.identities(root)
    with journal.connection_for(root, write=True, creating=True) as connection:
        journal.append(connection, [], "INITIALIZED", config)


class MainRuntime:
    def __init__(self, coordinator):
        require(type(coordinator.project) is project.ResearchProject, "INVALID_PROJECT")
        self.coordinator, self.root = coordinator, coordinator.project._root

    def _read(self, connection):
        rows = journal.read_events(connection)
        state = rules.reduce_events(rows)
        require(state["config"]["sidecar_identity"] == journal.identities(self.root),
                "RUNTIME_IDENTITY_MISMATCH")
        return rows, state

    def _source_check(self, config, *, fresh=False):
        events, revision = rules.sources(self.coordinator,
            two_decisions=config["schema"] == "bounded-ack-runtime-r1")
        require([e.value() for e in events] == config["events"], "SOURCE_CONFLICT")
        if fresh:
            require(revision == config["source_revision"], "STALE_SOURCE")

    def status(self):
        with journal.connection_for(self.root) as connection:
            rows, state = self._read(connection)
        self._source_check(state["config"])
        items = []
        for i, item in enumerate(state["items"]):
            phase = item["phase"]
            if phase == "TURN_START_INTENT":
                phase = "TURN_START_UNKNOWN"
            if i == 1 and phase == "QUEUED" and items[0]["phase"] != "ACK_COMPLETED":
                phase = "WAITING_PREDECESSOR"
            items.append({**item, "phase": phase, "persisted_phase": item["phase"],
                          "event_key": ContinuationEvent(canonical_json(state["config"]["events"][i])).key})
        return {"schema": "main-runtime-status-v1", "revision": len(rows), "epoch": state["epoch"],
            "paused": state["paused"], "items": items, "max_events": 2,
            "snapshot_authority": "OBSERVATION_ONLY", "execution_authorized": False,
            "dispatch_retry_allowed": False, "qualification": "NOT_ABAQUS_QUALIFIED",
            **({"pause_requested": state["paused"], "in_flight_intents": rules.pending_intents(state)}
               if state["config"]["schema"] == "bounded-ack-runtime-r1" else {})}

    def _append(self, kind, data):
        with journal.connection_for(self.root, write=True) as connection:
            rows, state = self._read(connection)
            if kind == "TURN_START_INTENT" and state["paused"]:
                return False
            rules.reduce_events(rows + [({"kind": kind, "data": data,
                "sequence": len(rows) + 1, "at_utc": project._utc()}, None)])
            journal.append(connection, rows, kind, data)
            return True

    def handle(self, event, port):
        # This OS mutex is sender ownership, not a SQLite/Project transaction.
        with journal.sender(self.root):
            with journal.connection_for(self.root) as connection:
                _, state = self._read(connection)
            require(type(event) is ContinuationEvent, "EVENT_CONFLICT")
            matches = [i for i, v in enumerate(state["config"]["events"]) if v == event.value()]
            require(len(matches) == 1, "EVENT_CONFLICT")
            index = matches[0]
            config, item = state["config"], state["items"][index]
            self._source_check(config)
            if item["phase"] != "QUEUED" or state["paused"] or (
                    index and state["items"][0]["phase"] != "ACK_COMPLETED"):
                return self.status()
            self._source_check(config, fresh=True)
            rules.valid_time(config["policy"])
            rules.preflight(config["policy"], port.preflight())
            baseline = [config["seed"]] + [x["proof"]["turn"] for x in state["items"][:index]]
            require(port.history() == baseline, "HISTORY_BASELINE_CONFLICT")
            intent = {"index": index, "epoch": state["epoch"] + 1, "event_key": event.key,
                "input_digest": digest_bytes(rules.prompt(event).encode()), "baseline": baseline,
                "attempt_limit": 1}
            if not self._append("TURN_START_INTENT", intent):
                return self.status()
            _fault("intent_committed")
            try:
                rules.valid_time(config["policy"])
                rules.preflight(config["policy"], port.preflight())
                self._source_check(config, fresh=True)
                # No Project/SQLite transaction survives to this boundary.
                turn_id = port.start_turn(rules.prompt(event), rules.output_schema(event))
                _fault("rpc_accepted")
                self._append("TURN_STARTED", {"index": index, "turn_id": turn_id})
                terminal = port.terminal(turn_id)
                _fault("terminal_observed")
                history = port.history()
                turn = rules.match_history(history, config, state["items"], index, turn_id)
                require(terminal == {"thread_id": config["policy"]["thread_id"],
                    "turn_id": turn_id, "status": "completed"}, "TERMINAL_CONFLICT")
                rules.preflight(config["policy"], port.preflight())
                self._append("ACK_COMPLETED", {"index": index, "history": history, "turn": turn,
                                             "observation": "TERMINAL_AND_HISTORY"})
            except Exception:
                with journal.connection_for(self.root) as connection:
                    _, current = self._read(connection)
                if current["items"][index]["phase"] in {"TURN_START_INTENT", "TURN_STARTED"}:
                    self._append("TURN_START_UNKNOWN", {"index": index})
            return self.status()

    def reconcile(self, port):
        with journal.sender(self.root):
            with journal.connection_for(self.root) as connection:
                _, state = self._read(connection)
            config = state["config"]
            self._source_check(config)
            for index, item in enumerate(state["items"]):
                if item["phase"] in {"TURN_START_INTENT", "TURN_STARTED", "TURN_START_UNKNOWN"}:
                    try:
                        rules.preflight(config["policy"], port.preflight(), idle=False)
                        history = port.history()
                        turn = rules.match_history(history, config, state["items"], index, item["turn_id"])
                        self._append("ACK_COMPLETED", {"index": index, "history": history, "turn": turn,
                            "observation": "READ_ONLY_RECONCILIATION"})
                    except (ValueError, OSError, TimeoutError):
                        pass
                    break
            return self.status()

    def control(self, operator_id, command_id, paused, expected_revision):
        with journal.sender(self.root):
            with journal.connection_for(self.root, write=True) as connection:
                rows, state = self._read(connection)
                require(state["config"]["schema"] == "bounded-ack-runtime-v1", "USE_EXPLICIT_R1_CONTROL")
                data = {"operator_id": operator_id, "command_id": command_id,
                        "paused": paused, "expected_revision": expected_revision}
                previous = state["control_keys"].get(command_id)
                if previous is not None:
                    require(previous == data, "CONTROL_CONFLICT")
                else:
                    rules.reduce_events(rows + [({"kind": "CONTROL", "data": data,
                        "sequence": len(rows) + 1, "at_utc": project._utc()}, None)])
                    journal.append(connection, rows, "CONTROL", data)
            return self.status()

    def _r1_control(self, kind, operator_id, command_id, expected_revision, expected_epoch):
        # A pause requests future work to stop; it does not acquire/replace the sender.
        with journal.connection_for(self.root, write=True) as connection:
            rows, state = self._read(connection)
            require(state["config"]["schema"] == "bounded-ack-runtime-r1", "R1_CONTROL_REQUIRED")
            require(type(expected_revision) is int and type(expected_epoch) is int
                    and expected_revision >= 1 and expected_epoch >= 0
                    and operator_id == state["config"]["operator_id"], "CONTROL_INVALID")
            rules.uuid_text(command_id)
            request = {"kind": kind, "operator_id": operator_id, "command_id": command_id,
                       "expected_revision": expected_revision, "expected_epoch": expected_epoch}
            previous = state["r1_controls"].get(command_id)
            if previous is not None:
                require({k: v for k, v in previous.items() if k != "after_intents"} == request,
                        "CONTROL_CONFLICT")
                data = previous
            else:
                data = {**request, "after_intents": rules.pending_intents(state)}
                rules.reduce_events(rows + [({"kind": kind, "data": data,
                    "sequence": len(rows) + 1, "at_utc": project._utc()}, None)])
                journal.append(connection, rows, kind, data)
        # Immutable acknowledgement of the pause linearization point, not current Turn state.
        return {"schema": "runtime-control-receipt-r1", "request": data, "accepted": True,
                "active_turn_interrupted": False, "unknown_cleared": False}

    def request_pause_after_current_turn(self, operator_id, command_id, expected_revision, expected_epoch):
        return self._r1_control("PAUSE_REQUESTED", operator_id, command_id, expected_revision, expected_epoch)

    def resume_queue(self, operator_id, command_id, expected_revision, expected_epoch):
        # Explicit operator-only queue release. No external port call and no UNKNOWN reset.
        with journal.sender(self.root):
            with journal.connection_for(self.root) as connection:
                _, state = self._read(connection)
            self._source_check(state["config"], fresh=True)
            return self._r1_control("QUEUE_RESUMED", operator_id, command_id, expected_revision, expected_epoch)

    def run_bounded(self, port, *, max_events=2):
        require(type(max_events) is int and max_events == 2, "RUNTIME_LIMIT")
        with journal.connection_for(self.root) as connection:
            _, state = self._read(connection)
        for value in state["config"]["events"]:
            status = self.handle(ContinuationEvent(canonical_json(value)), port)
            if status["paused"] or any(x["phase"] in {"TURN_START_UNKNOWN", "TURN_STARTED"}
                                      for x in status["items"]):
                return status
        return self.status()
