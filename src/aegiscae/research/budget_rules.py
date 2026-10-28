"""Bounded synthetic attempt accounting; pure event validation and deterministic replay."""

import re
from dataclasses import asdict, dataclass

from aegiscae.contracts.research_contracts import (
    _parse, canonical_json, digest, digest_bytes, identifier, require, strict_json,
)
from aegiscae.research.mutation_rules import FrozenRefs


@dataclass(frozen=True)
class BudgetScope:
    research_project_id: str
    bundle_id: str
    bundle_version: int
    goal_id: str
    goal_version: int
    refs: FrozenRefs

    @classmethod
    def from_bundle(cls, bundle):
        bundle.canonical_bytes()
        return cls(bundle.research_project_id, bundle.bundle_id, bundle.version,
                   bundle.goal.goal_id, bundle.goal.version, FrozenRefs(**bundle.digests()))

    @classmethod
    def from_dict(cls, data):
        value = _parse(cls, strict_json(canonical_json(data)))
        identifier(value.research_project_id, "rp")
        identifier(value.bundle_id, "bundle")
        identifier(value.goal_id, "goal")
        require(1 <= value.bundle_version <= 1000000 and 1 <= value.goal_version <= 1000000,
                "INVALID_VERSION")
        for item in asdict(value.refs).values():
            digest(item)
        return value


def business_key(value):
    require(type(value) is str and re.fullmatch(r"fake_[A-Za-z0-9_-]{1,59}", value) is not None,
            "SYNTHETIC_BUSINESS_KEY_REQUIRED")


@dataclass(frozen=True)
class ReservationRequest:
    scope: BudgetScope
    candidate_id: str
    candidate_digest: str
    cost: int
    operation_key: str
    downstream_business_key: str
    plan_digest: str | None

    @classmethod
    def from_dict(cls, data):
        value = _parse(cls, strict_json(canonical_json(data)))
        BudgetScope.from_dict(asdict(value.scope))
        identifier(value.candidate_id, "candidate")
        digest(value.candidate_digest)
        require(0 <= value.cost <= 1000000, "INVALID_COST")
        require(re.fullmatch(r"[A-Za-z0-9_-]{1,64}", value.operation_key) is not None, "INVALID_KEY")
        business_key(value.downstream_business_key)
        if value.plan_digest is not None:
            digest(value.plan_digest)
        return value


STATES = {
    "RESERVE": "RESERVED", "INTENT": "SUBMISSION_INTENT_RECORDED",
    "UNKNOWN": "ACCEPTANCE_UNKNOWN", "CHARGE": "ACCEPTED_OR_CHARGED",
    "RELEASE": "RELEASED_PROVEN_NO_ACCEPTANCE",
}
HELD = {"RESERVED", "SUBMISSION_INTENT_RECORDED", "ACCEPTANCE_UNKNOWN"}
UNKNOWN_REASONS = {"TIMEOUT", "RESPONSE_LOST", "RECEIPT_MISSING", "EXPIRED", "PROCESS_DIED"}


def validate_observation(value):
    require(type(value) is dict and set(value) == {
        "schema_version", "evidence_id", "reservation_id", "business_key", "request_digest",
        "outcome", "reason", "solver_start_observed", "grant_consumed"}, "INVALID_SYNTHETIC_EVIDENCE")
    require(value["schema_version"] == "budget-synthetic-oracle-v1"
            and value["solver_start_observed"] is False and value["grant_consumed"] is False,
            "SYNTHETIC_ONLY")
    identifier(value["evidence_id"], "fixture")
    identifier(value["reservation_id"], "reservation")
    business_key(value["business_key"])
    digest(value["request_digest"])
    require((value["outcome"] == "UNKNOWN" and type(value["reason"]) is str
             and value["reason"] in UNKNOWN_REASONS)
            or (value["outcome"] == "ACCEPTED" and value["reason"] == "ACCEPTED_FIXTURE"),
            "INVALID_SYNTHETIC_EVIDENCE")


def empty_ledger():
    return {"scope": None, "limit": None, "ledger_revision": 0, "reservations": {},
            "operations": {}, "business_keys": {}, "evidence": {}, "payloads": []}


def counters(ledger):
    values = ledger["reservations"].values()
    held = sum(r["request"]["cost"] for r in values if r["state"] in HELD)
    charged = sum(r["request"]["cost"] for r in values if r["state"] == "ACCEPTED_OR_CHARGED")
    available = ledger["limit"] - held - charged
    require(available >= 0, "BUDGET_INTEGRITY_ERROR")
    return {"limit": ledger["limit"], "held": held, "charged": charged, "available": available}


def apply_event(ledger, payload, bundle, candidates, previous_revision, latest_bundle_digest):
    """Apply one already bounded journal payload. Never trust its stored counter totals."""
    require(type(payload) is dict and set(payload) == {
        "schema_version", "source_classification", "action", "reservation_id", "request",
        "request_digest", "intent", "observation", "release_reason", "before_project_revision",
        "ledger_revision", "state", "limit", "held", "charged", "available"}, "BUDGET_INTEGRITY_ERROR")
    require(payload["schema_version"] == "budget-event-v1"
            and payload["source_classification"] == "SYNTHETIC_ONLY", "SYNTHETIC_ONLY")
    for key in ("before_project_revision", "ledger_revision", "limit", "held", "charged", "available"):
        require(type(payload[key]) is int and 0 <= payload[key] <= 1000000, "BUDGET_INTEGRITY_ERROR")
    require(payload["before_project_revision"] == previous_revision
            and payload["ledger_revision"] == ledger["ledger_revision"] + 1, "BUDGET_REVISION_CONFLICT")
    request = ReservationRequest.from_dict(payload["request"])
    require(request.cost == 1, "INVALID_COST")
    require(request.scope == BudgetScope.from_bundle(bundle), "CONTRACT_BINDING_MISMATCH")
    raw_request = asdict(request)
    require(payload["request_digest"] == digest_bytes(canonical_json(raw_request)), "BUDGET_INTEGRITY_ERROR")
    reservation_id = payload["reservation_id"]
    identifier(reservation_id, "reservation")
    action = payload["action"]
    require(type(action) is str and action in STATES and payload["state"] == STATES[action],
            "BUDGET_STATE_CONFLICT")
    if ledger["scope"] is None:
        require(action == "RESERVE", "BUDGET_INTEGRITY_ERROR")
        ledger["scope"] = asdict(request.scope)
        ledger["limit"] = bundle.goal.budget.max_solver_calls
    require(ledger["scope"] == asdict(request.scope), "BUDGET_SCOPE_PINNED")
    prior = ledger["reservations"].get(reservation_id)
    if action == "RESERVE":
        require(request.scope.refs.bundle == latest_bundle_digest, "STALE_CONTRACT")
        require(prior is None and request.operation_key not in ledger["operations"]
                and request.downstream_business_key not in ledger["business_keys"], "DUPLICATE_RESERVATION")
        require(len(ledger["reservations"]) < 128, "INPUT_LIMIT")
        candidate = candidates.get(request.candidate_id)
        require(candidate is not None
                and candidate["request"]["research_project_id"] == request.scope.research_project_id
                and candidate["request"]["refs"] == asdict(request.scope.refs)
                and candidate["manifest"]["output_digest"] == request.candidate_digest
                and candidate["manifest"]["qualification"] == "NOT_ABAQUS_QUALIFIED",
                "CANDIDATE_BINDING_MISMATCH")
        require(counters(ledger)["available"] >= 1, "BUDGET_EXHAUSTED")
        require(payload["intent"] is None, "INVALID_INTENT")
        ledger["operations"][request.operation_key] = reservation_id
        ledger["business_keys"][request.downstream_business_key] = reservation_id
    else:
        require(prior is not None and prior["request"] == raw_request, "RESERVATION_MISMATCH")
        if action == "INTENT":
            require(prior["state"] == "RESERVED" and payload["intent"] is not None,
                    "BUDGET_STATE_CONFLICT")
        elif action == "RELEASE":
            require(prior["state"] == "RESERVED" and prior["intent"] is None,
                    "POST_INTENT_RELEASE_FORBIDDEN")
        else:
            require(prior["state"] in {"SUBMISSION_INTENT_RECORDED", "ACCEPTANCE_UNKNOWN"},
                    "BUDGET_STATE_CONFLICT")
        if action != "INTENT":
            require(payload["intent"] == prior["intent"], "INTENT_CONFLICT")
    if payload["intent"] is not None:
        intent = payload["intent"]
        require(type(intent) is dict and set(intent) == {"business_key", "request_digest"}
                and intent["business_key"] == request.downstream_business_key, "INTENT_CONFLICT")
        digest(intent["request_digest"])
    if action in {"UNKNOWN", "CHARGE"}:
        observation = payload["observation"]
        validate_observation(observation)
        require(observation["reservation_id"] == reservation_id
                and observation["business_key"] == request.downstream_business_key
                and payload["intent"] is not None
                and observation["request_digest"] == payload["intent"]["request_digest"]
                and observation["outcome"] == ("UNKNOWN" if action == "UNKNOWN" else "ACCEPTED"),
                "EVIDENCE_BINDING_MISMATCH")
        require(observation["evidence_id"] not in ledger["evidence"], "EVIDENCE_CONFLICT")
        ledger["evidence"][observation["evidence_id"]] = payload
    else:
        require(payload["observation"] is None, "UNEXPECTED_EVIDENCE")
    require(payload["release_reason"] == ("UNUSED_PRE_INTENT" if action == "RELEASE" else None),
            "INVALID_RELEASE_REASON")
    ledger["reservations"][reservation_id] = payload
    ledger["ledger_revision"] += 1
    require(all(payload[key] == value for key, value in counters(ledger).items()), "BUDGET_SUM_MISMATCH")
    ledger["payloads"].append(payload)


def make_event(ledger, action, reservation_id, request, previous_revision, *,
               intent=None, observation=None):
    """Compute proposed totals; apply_event independently validates the transition."""
    old = ledger["reservations"].get(reservation_id)
    totals = counters(ledger)
    if old and old["state"] in HELD:
        totals["held"] -= old["request"]["cost"]
    if STATES[action] in HELD:
        totals["held"] += request["cost"]
    elif action == "CHARGE":
        totals["charged"] += request["cost"]
    totals["available"] = totals["limit"] - totals["held"] - totals["charged"]
    require(totals["available"] >= 0, "BUDGET_EXHAUSTED")
    return {"schema_version": "budget-event-v1", "source_classification": "SYNTHETIC_ONLY",
            "action": action, "reservation_id": reservation_id, "request": request,
            "request_digest": digest_bytes(canonical_json(request)), "intent": intent,
            "observation": observation, "release_reason": "UNUSED_PRE_INTENT" if action == "RELEASE" else None,
            "before_project_revision": previous_revision, "ledger_revision": ledger["ledger_revision"] + 1,
            "state": STATES[action], **totals}
