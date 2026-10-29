"""One fixed challenge and untrusted proposal slot; no gate or execution imports."""

from datetime import datetime, timedelta
from pathlib import Path
import uuid

from aegiscae.contracts.research_contracts import (
    canonical_json, digest_bytes, identifier, require, strict_json,
)
from aegiscae.research import ingress_store as journal, project as store
from aegiscae.research.candidate_proposal import CandidateProposal
from aegiscae.research.workflow import historical_research_brief


_BINDING_KEYS = ("research_project_id", "storage_generation", "canonical_root_digest",
                 "root_file_identity", "database_file_identity")
POLICIES = {"AUTO_TEST_SYNTHETIC", "REQUIRE_HUMAN_REVIEW"}


def _binding(meta):
    return {key: meta[key] for key in _BINDING_KEYS}


def _check_proposal(raw, challenge):
    proposal = CandidateProposal.from_bytes(raw)
    brief = challenge["brief"]
    matches = {
        "challenge_id": "challenge_id", "research_project_id": "research_project_id",
        "workflow_run_id": "workflow_run_id", "expected_project_revision": "project_revision",
        "brief_digest": "brief_digest", "previous_candidate_id": "previous_candidate_id",
        "previous_decision_ref": "previous_decision_ref",
    }
    require(all(vars(proposal)[key] == brief[value] for key, value in matches.items())
            and proposal.goal_digest == brief["frozen_refs"]["goal"]
            and proposal.model_contract_digest == brief["frozen_refs"]["model"]
            and proposal.verification_contract_digest == brief["frozen_refs"]["verification"]
            and list(proposal.evidence_refs) == brief["evidence_refs"], "PROPOSAL_BINDING_MISMATCH")
    return proposal


def _receipt(challenge, raw):
    proposal = _check_proposal(raw, challenge)
    digest = digest_bytes(raw)
    record_state = {"PROPOSE_CANDIDATE": "PROPOSED_UNTRUSTED", "STOP": "STOP_REQUESTED",
                    "REQUEST_REVIEW": "REVIEW_REQUESTED"}[proposal.action]
    return {"schema": "proposal-receipt-v1", "receipt_id": "proposalreceipt_" + digest[7:39],
        "challenge_id": challenge["brief"]["challenge_id"], "proposal_key": challenge["proposal_key"],
        "proposal_digest": digest, "challenge_digest": digest_bytes(canonical_json(challenge)),
        "status": "RECORDED_PENDING_GATE", "record_state": record_state,
        "author_identity": "NOT_AUTHENTICATED", "execution_authorized": False,
        "candidate_created": False, "budget_reserved": False}


def _validate_challenge(challenge):
    require(set(challenge) == {"schema", "binding", "sidecar_identity", "brief", "policy",
                "proposal_key", "issued_at_utc", "expires_at_utc"}
            and challenge["schema"] == "proposal-challenge-v1", "INGRESS_INTEGRITY")
    require(set(challenge["binding"]) == set(_BINDING_KEYS), "INGRESS_INTEGRITY")
    identifier(challenge["proposal_key"], "proposalkey")
    brief = challenge["brief"]
    require(type(brief) is dict and "read_at_utc" not in brief, "INGRESS_INTEGRITY")
    content = {k: v for k, v in brief.items() if k != "brief_digest"}
    require(brief["brief_digest"] == digest_bytes(canonical_json(content))
            and brief["research_project_id"] == challenge["binding"]["research_project_id"],
            "INGRESS_INTEGRITY")
    policy = challenge["policy"]
    require(set(policy) == {"schema", "scope", "mode", "execution_authorized", "human_identity_verified"}
            and policy["schema"] == "proposal-review-policy-v1" and policy["scope"] == "TEST_SYNTHETIC"
            and policy["mode"] in POLICIES and policy["execution_authorized"] is False
            and policy["human_identity_verified"] is False, "POLICY_INVALID")
    for key in ("issued_at_utc", "expires_at_utc"):
        store._validate_time(challenge[key])
    start, end = (datetime.strptime(challenge[key], "%Y-%m-%dT%H:%M:%S.%fZ")
                  for key in ("issued_at_utc", "expires_at_utc"))
    require(timedelta(0) < end - start <= timedelta(hours=24), "CHALLENGE_WINDOW_INVALID")


def _state(events):
    first = events[0][0]
    require(first["kind"] == "CHALLENGE", "INGRESS_INTEGRITY")
    challenge = first["data"]
    _validate_challenge(challenge)
    require(first["at_utc"] == challenge["issued_at_utc"], "INGRESS_INTEGRITY")
    state = {"challenge": challenge, "record": None, "gate": None, "revoked": False}
    for event, _ in events[1:]:
        kind, data = event["kind"], event["data"]
        if kind == "RECORD":
            require(challenge["issued_at_utc"] <= event["at_utc"] < challenge["expires_at_utc"], "INGRESS_INTEGRITY")
            require(not state["revoked"] and state["record"] is None and state["gate"] is None
                    and set(data) == {"raw_chunks", "receipt"}, "INGRESS_INTEGRITY")
            require(type(data["raw_chunks"]) is list and 1 <= len(data["raw_chunks"]) <= 16
                    and all(type(s) is str and len(s) <= 512 for s in data["raw_chunks"]), "INGRESS_INTEGRITY")
            require(data["receipt"] == _receipt(challenge, "".join(data["raw_chunks"]).encode("utf-8")),
                    "INGRESS_INTEGRITY")
            state["record"] = data
        elif kind == "GATE":
            require(state["record"] is not None and state["gate"] is None, "INGRESS_INTEGRITY")
            _validate_gate(data, challenge, state["record"]["receipt"])
            if data["admission"]["reason"] in {"ELIGIBLE_SYNTHETIC", "POLICY_REQUIRES_HUMAN", "AGENT_REQUESTED_STOP"}:
                require(not state["revoked"] and challenge["issued_at_utc"] <= event["at_utc"]
                        < challenge["expires_at_utc"], "INGRESS_INTEGRITY")
            state["gate"] = data
        elif kind == "REVOKE":
            require(not state["revoked"] and data == {"reason": "TRUSTED_SETUP_REVOKED"}, "INGRESS_INTEGRITY")
            state["revoked"] = True
        else:
            require(False, "INGRESS_INTEGRITY")
    return state


def _validate_gate(value, challenge, receipt):
    require(set(value) == {"admission", "review"}, "INGRESS_INTEGRITY")
    admission, review = value["admission"], value["review"]
    require(set(admission) == {"schema", "decision_id", "receipt_id", "challenge_digest",
        "proposal_digest", "expected_revision", "checked_revision", "status", "reason", "evidence_refs",
        "execution_authorized"}, "INGRESS_INTEGRITY")
    require(admission["schema"] == "admission-decision-v1"
        and admission["receipt_id"] == receipt["receipt_id"]
        and admission["challenge_digest"] == receipt["challenge_digest"]
        and admission["proposal_digest"] == receipt["proposal_digest"]
        and admission["expected_revision"] == challenge["brief"]["project_revision"]
        and type(admission["checked_revision"]) is int and 1 <= admission["checked_revision"] <= 1024
        and admission["evidence_refs"] == challenge["brief"]["evidence_refs"]
        and admission["execution_authorized"] is False
        and admission["status"] in {"ADMISSIBLE_SYNTHETIC_ONLY", "REJECTED", "INCONCLUSIVE",
                                     "HUMAN_REVIEW_REQUIRED"}, "INGRESS_INTEGRITY")
    identifier(admission["decision_id"], "admissiondecision")
    require(type(admission["reason"]) is str and admission["reason"] in REASONS, "INGRESS_INTEGRITY")
    expected = {"ELIGIBLE_SYNTHETIC": "ADMISSIBLE_SYNTHETIC_ONLY", "MODEL_REJECTED": "REJECTED",
                "POLICY_REQUIRES_HUMAN": "HUMAN_REVIEW_REQUIRED", "AGENT_REQUESTED_STOP": "HUMAN_REVIEW_REQUIRED"}
    require(admission["status"] == expected.get(admission["reason"], "INCONCLUSIVE"), "INGRESS_INTEGRITY")
    if admission["status"] in {"ADMISSIBLE_SYNTHETIC_ONLY", "HUMAN_REVIEW_REQUIRED"}:
        require(admission["checked_revision"] == admission["expected_revision"], "INGRESS_INTEGRITY")
    if admission["status"] == "ADMISSIBLE_SYNTHETIC_ONLY":
        require(challenge["policy"]["mode"] == "AUTO_TEST_SYNTHETIC", "INGRESS_INTEGRITY")
    require(review == review_for(challenge, admission), "INGRESS_INTEGRITY")


REASONS = {"ELIGIBLE_SYNTHETIC", "MODEL_REJECTED", "AUTHORITATIVE_STATE_UNAVAILABLE",
           "CHALLENGE_EXPIRED", "CHALLENGE_REVOKED", "REVISION_CONFLICT", "BUDGET_BLOCKED",
           "POLICY_REQUIRES_HUMAN", "AGENT_REQUESTED_STOP", "STORE_BUSY"}


def review_for(challenge, admission):
    accepted = admission["status"] == "ADMISSIBLE_SYNTHETIC_ONLY" and \
        challenge["policy"]["mode"] == "AUTO_TEST_SYNTHETIC"
    return {"schema": "review-decision-v1", "admission_decision_id": admission["decision_id"],
        "policy_digest": digest_bytes(canonical_json(challenge["policy"])),
        "status": "POLICY_ACCEPTED_SYNTHETIC_ONLY" if accepted else "HUMAN_REVIEW_REQUIRED",
        "provenance": "PREEXISTING_FROZEN_TEST_POLICY", "human_approval": False,
        "execution_authorized": False, "grants_issued": 0}


def _active(state, at):
    require(not state["revoked"], "CHALLENGE_REVOKED")
    require(state["challenge"]["issued_at_utc"] <= at < state["challenge"]["expires_at_utc"],
            "CHALLENGE_EXPIRED")


def issue_challenge(coordinator, *, window_seconds=3600, policy_mode="AUTO_TEST_SYNTHETIC"):
    """Trusted explicit setup only. Fixed sidecar creation is not reachable over MCP."""
    require(type(window_seconds) is int and 1 <= window_seconds <= 86400
            and policy_mode in POLICIES, "POLICY_INVALID")
    brief = coordinator.research_brief()
    brief.pop("read_at_utc")
    project = coordinator.project
    with project._snapshot() as (_, meta, _bundles, _events):
        require(meta["project_revision"] == brief["project_revision"], "REVISION_CONFLICT")
        journal.create_file(project._root)
        at = store._utc()
        expiry = (datetime.strptime(at, "%Y-%m-%dT%H:%M:%S.%fZ") + timedelta(
            seconds=window_seconds)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        challenge = {"schema": "proposal-challenge-v1", "binding": _binding(meta),
            "sidecar_identity": journal.identity(project._root), "brief": brief,
            "policy": {"schema": "proposal-review-policy-v1", "scope": "TEST_SYNTHETIC",
                       "mode": policy_mode, "execution_authorized": False, "human_identity_verified": False},
            "proposal_key": "proposalkey_" + uuid.uuid4().hex, "issued_at_utc": at, "expires_at_utc": expiry}
        _validate_challenge(challenge)
        with journal.connection_for(project._root, write=True, creating=True) as connection:
            journal.append(connection, [], "CHALLENGE", challenge, at)
    return challenge


class ProposalIngress:
    """MCP facade exposes record/status only; all bindings are startup-selected."""

    def __init__(self, root, research_project_id, challenge_id):
        self._project = store.open_existing_readonly(Path(root))
        identifier(research_project_id, "rp")
        identifier(challenge_id, "challenge")
        self._project_id, self._challenge_id = research_project_id, challenge_id
        self.status()

    @classmethod
    def from_startup_file(cls, filename):
        path = store._path(Path(filename), directory=False, scope=False)
        with path.open("rb") as stream:
            raw = stream.read(8193)
        require(len(raw) <= 8192, "STARTUP_LIMIT")
        data = strict_json(raw)
        require(type(data) is dict and set(data) == {"schema", "test_only", "root",
                    "research_project_id", "challenge_id"}
                and data["schema"] == "proposal-mcp-startup-v1" and data["test_only"] is True,
                "STARTUP_INVALID")
        return cls(data["root"], data["research_project_id"], data["challenge_id"])

    def _read(self, connection, meta, bundles, audit):
        events = journal.read_events(connection)
        state = _state(events)
        challenge = state["challenge"]
        require(challenge["binding"] == _binding(meta)
                and meta["research_project_id"] == self._project_id
                and challenge["brief"]["challenge_id"] == self._challenge_id
                and challenge["sidecar_identity"] == journal.identity(self._project._root),
                "INGRESS_BINDING_MISMATCH")
        require(challenge["brief"] == historical_research_brief(bundles, audit,
            challenge["brief"]["project_revision"]), "BRIEF_HISTORY_MISMATCH")
        return state, events

    def status(self):
        with journal.connection_for(self._project._root) as connection:
            with self._project._snapshot() as (_, meta, bundles, audit):
                state, _ = self._read(connection, meta, bundles, audit)
        challenge = state["challenge"]
        validity = "CURRENT"
        if state["revoked"]:
            validity = "REVOKED"
        elif not challenge["issued_at_utc"] <= store._utc() < challenge["expires_at_utc"]:
            validity = "EXPIRED"
        elif meta["project_revision"] != challenge["brief"]["project_revision"]:
            validity = "STALE"
        return {"schema": "proposal-status-v1", "challenge_id": self._challenge_id,
            "proposal_key": challenge["proposal_key"], "brief": challenge["brief"],
            "expires_at_utc": challenge["expires_at_utc"], "policy": challenge["policy"],
            "validity": validity, "receipt": state["record"]["receipt"] if state["record"] else None,
            "decisions": state["gate"], "execution_authorized": False,
            "af_dynamic_execution_verified": False, "scientific_validation_available": False}

    def record(self, proposal_key, proposal_json):
        require(type(proposal_json) is str, "INVALID_PROPOSAL")
        raw = proposal_json.encode("utf-8")
        CandidateProposal.from_bytes(raw)
        with journal.connection_for(self._project._root, write=True) as connection:
            with self._project._snapshot() as (_, meta, bundles, audit):
                state, events = self._read(connection, meta, bundles, audit)
                challenge = state["challenge"]
                require(proposal_key == challenge["proposal_key"], "PROPOSAL_KEY_MISMATCH")
                at = store._utc()
                _active(state, at)
                require(meta["project_revision"] == challenge["brief"]["project_revision"], "REVISION_CONFLICT")
                if state["record"] is not None:
                    require("".join(state["record"]["raw_chunks"]).encode("utf-8") == raw, "PROPOSAL_CONTENT_CONFLICT")
                    return state["record"]["receipt"]
                receipt = _receipt(challenge, raw)
                journal.append(connection, events, "RECORD", {
                    "raw_chunks": [proposal_json[i:i + 512] for i in range(0, len(proposal_json), 512)],
                    "receipt": receipt}, at)
                return receipt


def revoke_challenge(ingress):
    """Trusted setup revocation only, absent from the MCP surface."""
    with journal.connection_for(ingress._project._root, write=True) as connection:
        with ingress._project._snapshot() as (_, meta, bundles, audit):
            state, events = ingress._read(connection, meta, bundles, audit)
            if not state["revoked"]:
                journal.append(connection, events, "REVOKE", {"reason": "TRUSTED_SETUP_REVOKED"}, store._utc())
