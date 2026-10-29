"""Single owned test-thread outbox; never a scheduler or research executor."""

from aegiscae.contracts.research_contracts import canonical_json, digest_bytes, require
from aegiscae.research import continuation_store as journal, mutation, project as store
from aegiscae.research.continuation_rules import (
    BINDING_KEYS, TERMINAL, CodexTurnPort, ContinuationEvent, check_port, check_turn,
    output_schema, positive_history, prompt, uuid_text, validate_policy,
)
from aegiscae.research.workflow import _load, historical_research_brief


def _fault(stage):
    """Trusted fault injection; no caller-supplied callback or model authority."""


def _binding(meta):
    return {key: meta[key] for key in BINDING_KEYS}


def _source(coordinator, meta, bundles, events):
    state, candidates, _ledger, latest = _load(bundles, events)
    require(state is not None and state["workflow_id"] == coordinator.workflow_id, "WORKFLOW_NOT_FOUND")
    brief = historical_research_brief(bundles, events, meta["project_revision"])
    require(latest == brief["frozen_refs"]["bundle"] and brief["V2"] == "NOT_RUN"
        and brief["V4"] == "NOT_ASSESSED" and brief["physical_evidence_eligible"] is False
        and not brief["af_fake_refs"] and brief["budget"]["unknown"] == 0, "EVENT_INELIGIBLE")
    source = events[-1]
    require(source["kind"] == "WORKFLOW_RECORDED" and source["workflow"]["action"] == "DECIDE"
        and source["workflow"]["workflow_id"] == coordinator.workflow_id
        and source["project_revision"] == meta["project_revision"], "SOURCE_NOT_DECISION")
    bundle = next(b[0] for b in bundles if b[1] == latest)
    candidate = candidates[brief["previous_candidate_id"]]
    mutation._recheck(coordinator.workspace, candidate, bundle,
                      current_revision=meta["project_revision"], bundles=bundles)
    payload = {"schema": "continuation-source-v1", "event_type": "SYNTHETIC_DECISION_RECORDED",
        "binding": _binding(meta), "workflow_id": coordinator.workflow_id, "step_id": "A",
        "sequence": source["sequence"], "source_event_digest": source["event_digest"],
        "source_transaction_id": source["transaction_id"], "source_at_utc": source["at_utc"],
        "project_revision": meta["project_revision"], "candidate_id": brief["previous_candidate_id"],
        "candidate_digest": candidate["manifest"]["output_digest"], "brief": brief}
    return ContinuationEvent(canonical_json(payload))


def observe(coordinator):
    """Read-only source projection. Unsourced arbitrary payloads are never accepted."""
    with coordinator.project._snapshot() as (_, meta, bundles, events):
        return _source(coordinator, meta, bundles, events)


def _reduce(events):
    first = events[0][0]
    require(first["kind"] == "ELIGIBLE", "CONTINUATION_INTEGRITY")
    config = first["data"]
    require(set(config) == {"schema", "binding", "sidecar_identity", "event", "event_key", "policy"}
        and config["schema"] == "continuation-outbox-v1", "CONTINUATION_INTEGRITY")
    event = ContinuationEvent(canonical_json(config["event"]))
    require(config["event_key"] == event.key and config["binding"] == event.value()["binding"],
            "CONTINUATION_INTEGRITY")
    p = config["policy"]
    validate_policy(p)
    require(p["issued_at_utc"] <= first["at_utc"] < p["expires_at_utc"], "POLICY_EXPIRED")
    state = {"phase": "ELIGIBLE", "config": config, "intent": None, "turn_id": None, "proof": None}
    for entry, _ in events[1:]:
        phase, data = entry["kind"], entry["data"]
        before = state["phase"]
        require(before not in TERMINAL, "CONTINUATION_INTEGRITY")
        if phase == "TURN_START_INTENT":
            require(before == "ELIGIBLE" and data == {
                "event_key": event.key, "thread_id": p["thread_id"],
                "input_digest": digest_bytes(prompt(event).encode()),
                "baseline_turn_ids": [p["seed_turn_id"]], "dispatch_attempt_limit": 1},
                "CONTINUATION_INTEGRITY")
            require(p["issued_at_utc"] <= entry["at_utc"] < p["expires_at_utc"], "POLICY_EXPIRED")
            state["intent"] = data
        elif phase == "TURN_STARTED":
            require(before == "TURN_START_INTENT" and set(data) == {"turn_id"}, "CONTINUATION_INTEGRITY")
            uuid_text(data["turn_id"])
            require(data["turn_id"] != p["seed_turn_id"], "CONTINUATION_INTEGRITY")
            state["turn_id"] = data["turn_id"]
        elif phase == "TURN_START_UNKNOWN":
            require(before in {"TURN_START_INTENT", "TURN_STARTED"}
                    and data == {"reason": "DISPATCH_OR_OBSERVATION_UNCERTAIN"}, "CONTINUATION_INTEGRITY")
        elif phase in TERMINAL:
            require(before in {"TURN_START_INTENT", "TURN_STARTED", "TURN_START_UNKNOWN"}
                and set(data) == {"turn", "history", "history_digest", "observation"}
                and data["observation"] in {"TERMINAL_AND_HISTORY", "READ_ONLY_RECONCILIATION"},
                "CONTINUATION_INTEGRITY")
            turn = data["turn"]
            check_turn(turn, event, p)
            require(phase == {"completed": "TURN_COMPLETED", "failed": "TURN_FAILED",
                "interrupted": "TURN_INTERRUPTED"}.get(turn["status"])
                and (state["turn_id"] is None or state["turn_id"] == turn["turn_id"]),
                "CONTINUATION_INTEGRITY")
            require(data["history_digest"] == digest_bytes(canonical_json(data["history"]))
                    and positive_history(data["history"], event, p, state["turn_id"]) == turn,
                    "CONTINUATION_INTEGRITY")
            state.update(turn_id=turn["turn_id"], proof=data)
        else:
            require(False, "CONTINUATION_INTEGRITY")
        state["phase"] = phase
    return state


def _receipt(state):
    config = state["config"]
    # A recovered intent is uncertain even if the process crashed before sending.
    phase = state["phase"]
    return {"schema": "continuation-receipt-v1", "event_key": config["event_key"],
        "target_thread_id": config["policy"]["thread_id"], "turn_id": state["turn_id"],
        "phase": "TURN_START_UNKNOWN" if phase == "TURN_START_INTENT" else phase,
        "persisted_phase": phase, "input_digest": state["intent"]["input_digest"] if state["intent"] else None,
        "cli_version": config["policy"]["cli_version"], "proof": state["proof"],
        "execution_authorized": False, "dispatch_retry_allowed": False,
        "qualification": "NOT_ABAQUS_QUALIFIED"}


def initialize_outbox(coordinator, event, policy):
    """Explicit trusted test setup; one fixed sidecar, no schema migration/replacement."""
    validate_policy(policy)
    with coordinator.project._snapshot() as (_, meta, bundles, events):
        require(type(event) is ContinuationEvent and event == _source(coordinator, meta, bundles, events),
                "EVENT_CONFLICT")
        at = store._utc()
        require(policy["issued_at_utc"] <= at < policy["expires_at_utc"], "POLICY_EXPIRED")
        root = coordinator.project._root
        journal.create_file(root)
        config = {"schema": "continuation-outbox-v1", "binding": _binding(meta),
            "sidecar_identity": journal.identity(root), "event": event.value(), "event_key": event.key,
            "policy": policy}
        with journal.connection_for(root, write=True, creating=True) as connection:
            journal.append(connection, [], "ELIGIBLE", config, at)


class ContinuationOutbox:
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self.root = coordinator.project._root

    def _read(self, connection, meta, bundles, events):
        journal_events = journal.read_events(connection)
        state = _reduce(journal_events)
        config = state["config"]
        require(config["binding"] == _binding(meta)
                and config["sidecar_identity"] == journal.identity(self.root), "OUTBOX_IDENTITY_MISMATCH")
        require(config["event"] == _source(self.coordinator, meta, bundles, events).value(), "STALE_SOURCE")
        return journal_events, state

    def inspect(self):
        with self.coordinator.project._snapshot() as (_, meta, bundles, events):
            with journal.connection_for(self.root) as connection:
                _, state = self._read(connection, meta, bundles, events)
                return _receipt(state)

    def handle(self, event: ContinuationEvent, port: CodexTurnPort):
        # Keep a source read transaction through dispatch. Project writers cannot commit
        # a conflicting revision during this bounded call. No research writes occur here.
        with self.coordinator.project._snapshot() as (_, meta, bundles, events):
            with journal.connection_for(self.root, write=True) as connection:
                history, state = self._read(connection, meta, bundles, events)
                require(type(event) is ContinuationEvent and event.value() == state["config"]["event"],
                        "EVENT_CONFLICT")
                if state["phase"] != "ELIGIBLE":
                    return _receipt(state)
                p = state["config"]["policy"]
                require(p["issued_at_utc"] <= store._utc() < p["expires_at_utc"], "POLICY_EXPIRED")
                check_port(p, port.preflight())
                baseline = port.history()
                require(type(baseline) is list and len(baseline) == 1
                    and baseline[0].get("thread_id") == p["thread_id"]
                    and baseline[0].get("turn_id") == p["seed_turn_id"]
                    and baseline[0].get("status") == "completed"
                    and baseline[0].get("tools_used") == 0, "BASELINE_NOT_SEED_ONLY")
                intent = {"event_key": event.key, "thread_id": p["thread_id"],
                    "input_digest": digest_bytes(prompt(event).encode()),
                    "baseline_turn_ids": [p["seed_turn_id"]], "dispatch_attempt_limit": 1}
                journal.append(connection, history, "TURN_START_INTENT", intent, store._utc())
            # Only this NEW successful commit call stack may send. Reopen never reaches here.
            _fault("intent_committed")
            try:
                check_port(p, port.preflight())
                require(store._utc() < p["expires_at_utc"], "POLICY_EXPIRED")
                turn_id = port.start_turn(prompt(event), output_schema(event))
                _fault("start_returned")
                uuid_text(turn_id)
                self._append("TURN_STARTED", {"turn_id": turn_id}, meta, bundles, events)
                terminal = port.terminal(turn_id)
                history = port.history()
                turn = positive_history(history, event, p, turn_id)
                require(terminal == {"thread_id": p["thread_id"], "turn_id": turn_id,
                                    "status": turn["status"]}, "TERMINAL_MISMATCH")
                self._finish(turn, history, "TERMINAL_AND_HISTORY", meta, bundles, events)
            except Exception:
                with journal.connection_for(self.root, write=True) as connection:
                    history, state = self._read(connection, meta, bundles, events)
                    if state["phase"] in {"TURN_START_INTENT", "TURN_STARTED"}:
                        journal.append(connection, history, "TURN_START_UNKNOWN",
                            {"reason": "DISPATCH_OR_OBSERVATION_UNCERTAIN"}, store._utc())
        return self.inspect()

    def _append(self, phase, data, meta, bundles, events):
        with journal.connection_for(self.root, write=True) as connection:
            history, state = self._read(connection, meta, bundles, events)
            require(state["phase"] not in TERMINAL, "CONTINUATION_ALREADY_TERMINAL")
            _reduce(history + [({"kind": phase, "data": data, "at_utc": store._utc()}, None)])
            journal.append(connection, history, phase, data, store._utc())

    def _finish(self, turn, history, observation, meta, bundles, events):
        phase = {"completed": "TURN_COMPLETED", "failed": "TURN_FAILED",
                 "interrupted": "TURN_INTERRUPTED"}.get(turn["status"])
        require(phase is not None, "TURN_NOT_TERMINAL")
        proof = {"turn": turn, "history": history, "history_digest": digest_bytes(canonical_json(history)),
                 "observation": observation}
        self._append(phase, proof, meta, bundles, events)

    def reconcile(self, port: CodexTurnPort):
        """Explicit read-only remote reconciliation. Never sends a turn or replaces a thread."""
        with self.coordinator.project._snapshot() as (_, meta, bundles, events):
            with journal.connection_for(self.root) as connection:
                _, state = self._read(connection, meta, bundles, events)
            if state["phase"] in TERMINAL or state["phase"] == "ELIGIBLE":
                return _receipt(state)
            event = ContinuationEvent(canonical_json(state["config"]["event"]))
            p = state["config"]["policy"]
            try:
                check_port(p, port.preflight(), idle=False)
                history = port.history()
                turn = positive_history(history, event, p, state["turn_id"])
                self._finish(turn, history, "READ_ONLY_RECONCILIATION", meta, bundles, events)
            except (ValueError, OSError, TimeoutError):
                return _receipt(state)
        return self.inspect()
