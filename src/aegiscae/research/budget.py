"""Offline synthetic BudgetLedger. No external dispatch or real evidence acceptance."""

import copy
import hashlib
import hmac
import secrets
import uuid
from dataclasses import asdict, dataclass, field

from aegiscae.contracts.research_contracts import canonical_json, digest, require, strict_json
from aegiscae.research import project as store
from aegiscae.research.budget_rules import (
    BudgetScope, ReservationRequest, apply_event, business_key, counters, empty_ledger,
    make_event, validate_observation,
)


@dataclass(frozen=True)
class SyntheticObservation:
    _payload: bytes = field(repr=False)
    _seal: bytes = field(repr=False)


class SyntheticOracle:
    """Explicit test capability. Its HMAC is process-local, never real AF authentication."""

    def __init__(self):
        self._key = secrets.token_bytes(32)

    def issue(self, reservation_id, business_key, request_digest, outcome, evidence_id, reason):
        raw = {"schema_version": "budget-synthetic-oracle-v1", "evidence_id": evidence_id,
               "reservation_id": reservation_id, "business_key": business_key,
               "request_digest": request_digest, "outcome": outcome, "reason": reason,
               "solver_start_observed": False, "grant_consumed": False}
        validate_observation(raw)
        body = canonical_json(raw)
        return SyntheticObservation(body, hmac.digest(self._key, body, hashlib.sha256))

    def check(self, observation):
        require(type(observation) is SyntheticObservation and type(observation._payload) is bytes
                and len(observation._payload) <= 8192 and type(observation._seal) is bytes,
                "SYNTHETIC_ORACLE_REQUIRED")
        require(hmac.compare_digest(observation._seal,
                    hmac.digest(self._key, observation._payload, hashlib.sha256)), "EVIDENCE_SEAL_MISMATCH")
        raw = strict_json(observation._payload)
        validate_observation(raw)
        require(canonical_json(raw) == observation._payload, "INVALID_SYNTHETIC_EVIDENCE")
        return raw


def _fault(stage):
    """Trusted exception/process-exit injection seam; never a scheduler hook."""


def _revision(value):
    require(type(value) is int and 1 <= value <= 1024, "INVALID_REVISION")


def _load(meta, bundles, events, scope):
    require(meta["research_project_id"] == scope.research_project_id, "PROJECT_MISMATCH")
    bundle = next((b[0] for b in bundles if b[1] == scope.refs.bundle), None)
    require(bundle is not None and scope == BudgetScope.from_bundle(bundle), "CONTRACT_BINDING_MISMATCH")
    ledger, candidates, latest = empty_ledger(), {}, None
    by_digest = {b[1]: b[0] for b in bundles}
    for event in events:
        if event["kind"] == "BUNDLE_FROZEN":
            latest = event["bundle_digest"]
        elif event["kind"] == "CANDIDATE_PUBLICATION_OBSERVED":
            candidate = event["candidate"]
            candidates[candidate["request"]["candidate_id"]] = candidate
        elif event["kind"] == "BUDGET_RECORDED":
            apply_event(ledger, event["budget"], by_digest[event["bundle_digest"]], candidates,
                        event["project_revision"] - 1, latest)
    if ledger["limit"] is None:
        ledger["limit"] = bundle.goal.budget.max_solver_calls
    return bundle, ledger, candidates, latest


def _result(event, current_revision, replayed):
    data = event["budget"]
    return {key: data[key] for key in ("reservation_id", "state", "ledger_revision", "limit",
            "held", "charged", "available", "request_digest")} | {
        "project_revision": event["project_revision"], "current_project_revision": current_revision,
        "replayed": replayed, "audit_sequence": event["sequence"], "transaction_id": event["transaction_id"],
        "event_digest": event["event_digest"], "result_scope": "ORIGINAL_OPERATION_RESULT",
        "source_classification": "SYNTHETIC_ONLY", "execution_authorized": False,
        "real_acceptance_established": False, "grant_consumed": False, "solver_start_observed": False}


class BudgetLedger:
    def __init__(self, project, scope, oracle=None):
        require(type(project) is store.ResearchProject and type(scope) is BudgetScope, "INVALID_TYPE")
        require(oracle is None or type(oracle) is SyntheticOracle, "SYNTHETIC_ORACLE_REQUIRED")
        self.project = project
        self.scope = BudgetScope.from_dict(asdict(scope))
        self.oracle = oracle

    def inspect_budget(self):
        with self.project._snapshot() as (_, meta, bundles, events):
            _, ledger, _, latest = _load(meta, bundles, events, self.scope)
            require(ledger["scope"] in (None, asdict(self.scope)), "BUDGET_SCOPE_PINNED")
            require(ledger["scope"] is not None or latest == self.scope.refs.bundle, "STALE_CONTRACT")
            return {**counters(ledger), "ledger_revision": ledger["ledger_revision"],
                "project_revision": meta["project_revision"], "scope": asdict(self.scope),
                "source_classification": "SYNTHETIC_ONLY", "allocation_enforcement": "LOCAL_LEDGER_ONLY",
                "execution_authorized": False, "real_acceptance_established": False,
                "grant_consumed": False, "solver_start_observed": False,
                "reservations": tuple({"reservation_id": key, "state": value["state"],
                    "request": value["request"], "intent": value["intent"]}
                    for key, value in ledger["reservations"].items())}

    def _commit(self, connection, meta, bundle, ledger, candidates, latest, payload, expected_revision):
        require(type(expected_revision) is int and expected_revision == meta["project_revision"],
                "REVISION_CONFLICT")
        apply_event(copy.deepcopy(ledger), payload, bundle, candidates, meta["project_revision"], latest)
        event = store._commit_budget_event(connection, meta, payload)
        _fault("after_event")
        _fault("before_commit")
        connection.commit()
        _fault("after_commit")
        return _result(event, meta["project_revision"], False)

    def reserve_for_candidate(self, candidate_id, candidate_digest, cost, operation_key,
                              downstream_business_key, expected_revision, plan_digest=None):
        _revision(expected_revision)
        request = ReservationRequest.from_dict({"scope": asdict(self.scope), "candidate_id": candidate_id,
            "candidate_digest": candidate_digest, "cost": cost, "operation_key": operation_key,
            "downstream_business_key": downstream_business_key, "plan_digest": plan_digest})
        raw = asdict(request)
        _fault("before_begin")
        with self.project._snapshot(write=True) as (connection, meta, bundles, events):
            previous = next((e for e in events if e["kind"] == "BUDGET_RECORDED"
                             and e["budget"]["action"] == "RESERVE"
                             and e["budget"]["request"]["operation_key"] == operation_key), None)
            if previous:
                require(previous["budget"]["request"] == raw, "IDEMPOTENCY_CONFLICT")
                return _result(previous, meta["project_revision"], True)
            bundle, ledger, candidates, latest = _load(meta, bundles, events, self.scope)
            require(cost == 1, "INVALID_COST")
            require(ledger["scope"] in (None, asdict(self.scope)), "BUDGET_SCOPE_PINNED")
            require(downstream_business_key not in ledger["business_keys"], "BUSINESS_KEY_CONFLICT")
            payload = make_event(ledger, "RESERVE", "reservation_" + uuid.uuid4().hex, raw,
                                 meta["project_revision"])
            return self._commit(connection, meta, bundle, ledger, candidates, latest, payload, expected_revision)

    def record_submission_intent(self, reservation_id, downstream_business_key, request_digest,
                                  expected_revision):
        business_key(downstream_business_key)
        digest(request_digest)
        return self._transition(reservation_id, "INTENT", expected_revision,
                                intent={"business_key": downstream_business_key, "request_digest": request_digest})

    def release_before_external_intent(self, reservation_id, expected_revision):
        return self._transition(reservation_id, "RELEASE", expected_revision)

    def observe_synthetic_acceptance_or_unknown(self, reservation_id, observation, expected_revision):
        require(self.oracle is not None, "SYNTHETIC_ORACLE_REQUIRED")
        raw = self.oracle.check(observation)
        require(raw["reservation_id"] == reservation_id, "EVIDENCE_BINDING_MISMATCH")
        return self._transition(reservation_id, "UNKNOWN" if raw["outcome"] == "UNKNOWN" else "CHARGE",
                                expected_revision, observation=raw)

    def _transition(self, reservation_id, action, expected_revision, *, intent=None, observation=None):
        _revision(expected_revision)
        _fault("before_begin")
        with self.project._snapshot(write=True) as (connection, meta, bundles, events):
            bundle, ledger, candidates, latest = _load(meta, bundles, events, self.scope)
            require(ledger["scope"] == asdict(self.scope), "BUDGET_SCOPE_PINNED")
            require(type(reservation_id) is str and reservation_id in ledger["reservations"],
                    "RESERVATION_NOT_FOUND")
            previous = ledger["reservations"][reservation_id]
            for event in events:
                if event["kind"] != "BUDGET_RECORDED":
                    continue
                old = event["budget"]
                if observation is not None and old["observation"] is not None \
                        and old["observation"]["evidence_id"] == observation["evidence_id"]:
                    require(old["observation"] == observation and old["reservation_id"] == reservation_id,
                            "EVIDENCE_CONFLICT")
                    return _result(event, meta["project_revision"], True)
                if old["reservation_id"] == reservation_id and old["action"] == action and action != "UNKNOWN":
                    require((action != "INTENT" or old["intent"] == intent)
                            and (action != "CHARGE" or old["observation"] == observation),
                            "IDEMPOTENCY_CONFLICT")
                    return _result(event, meta["project_revision"], True)
            payload = make_event(ledger, action, reservation_id, previous["request"], meta["project_revision"],
                intent=intent if action == "INTENT" else previous["intent"], observation=observation)
            return self._commit(connection, meta, bundle, ledger, candidates, latest, payload, expected_revision)
