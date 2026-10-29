"""Versioned, fixed A/B synthetic workflow records and independent rule replay."""

import copy
from dataclasses import asdict, dataclass, replace
from decimal import Decimal, localcontext
from typing import Literal, Protocol

from aegiscae.contracts.research_contracts import (
    EvidenceRequirement, Quantity, _parse, canonical_json, digest, digest_bytes,
    identifier, require, strict_json,
)
from aegiscae.research.budget_rules import BudgetScope, business_key
from aegiscae.research.mutation_rules import FrozenRefs, MutationRequest, validate_parent
from aegiscae.research.proposal_rules import ProposalWorkflowDefinition, admission_for


def plain(value):
    return strict_json(canonical_json(asdict(value)))


@dataclass(frozen=True)
class WorkflowDefinition:
    schema_version: Literal["synthetic-workflow-v1"]
    workflow_id: str
    scope: BudgetScope
    source_id: str
    candidates: tuple[MutationRequest, ...]
    max_steps: Literal[2]
    budget_units: Literal[2]
    on_unknown: Literal["BLOCK"]

    @classmethod
    def from_dict(cls, raw):
        value = _parse(cls, strict_json(canonical_json(raw)))
        identifier(value.workflow_id, "workflow")
        identifier(value.source_id, "syntheticport")
        BudgetScope.from_dict(asdict(value.scope))
        require(len(value.candidates) == 2, "FIXED_TWO_STEPS_REQUIRED")
        for candidate in value.candidates:
            MutationRequest.from_dict(asdict(candidate))
            require(candidate.refs == value.scope.refs
                    and candidate.research_project_id == value.scope.research_project_id,
                    "CONTRACT_BINDING_MISMATCH")
        for name in ("candidate_id", "idempotency_key", "output_identity"):
            require(len({vars(c)[name] for c in value.candidates}) == 2, "STEP_IDENTITY_CONFLICT")
        require(value.candidates[0].workspace_id == value.candidates[1].workspace_id,
                "WORKSPACE_IDENTITY_MISMATCH")
        return value


def parse_definition(raw):
    if raw.get("schema_version") == "proposal-workflow-v1":
        return ProposalWorkflowDefinition.from_dict(raw)
    return WorkflowDefinition.from_dict(raw)


def proposal_pending(state):
    return (state["definition"]["schema_version"] == "proposal-workflow-v1"
            and state["state"] == "READY_B" and state.get("proposal_admission") is None)


def template_for(state, definition, step):
    if step == "B" and type(definition) is ProposalWorkflowDefinition:
        admission = state.get("proposal_admission")
        require(admission is not None and admission["decision"] == "ADMITTED_SYNTHETIC_ONLY",
                "PROPOSAL_REQUIRED")
        return MutationRequest.from_dict(admission["candidate_template"])
    return definition.candidates[0 if step == "A" else 1]


@dataclass(frozen=True)
class SyntheticRequest:
    schema_version: Literal["synthetic-request-v1"]
    source_id: str
    workflow_id: str
    research_project_id: str
    refs: FrozenRefs
    step_id: Literal["A", "B"]
    candidate_id: str
    candidate_digest: str
    business_key: str
    attempt_id: str
    qualification: Literal["NOT_ABAQUS_QUALIFIED"]
    source_classification: Literal["SYNTHETIC_TEST_ONLY"]
    test_only: Literal[True]
    physical_evidence_eligible: Literal[False]

    @classmethod
    def from_dict(cls, raw):
        value = _parse(cls, strict_json(canonical_json(raw)))
        for name, prefix in (("source_id", "syntheticport"), ("workflow_id", "workflow"),
                             ("research_project_id", "rp"), ("candidate_id", "candidate"),
                             ("attempt_id", "syntheticattempt")):
            identifier(vars(value)[name], prefix)
        for item in (*asdict(value.refs).values(), value.candidate_digest):
            digest(item)
        business_key(value.business_key)
        return value

    def digest(self):
        return digest_bytes(canonical_json(plain(self)))


@dataclass(frozen=True)
class SyntheticReceipt:
    schema_version: Literal["synthetic-receipt-v1"]
    request: SyntheticRequest
    request_digest: str
    receipt_id: str
    accepted: Literal[True]

    @classmethod
    def from_dict(cls, raw):
        value = _parse(cls, strict_json(canonical_json(raw)))
        SyntheticRequest.from_dict(asdict(value.request))
        identifier(value.receipt_id, "syntheticreceipt")
        require(value.request_digest == value.request.digest(), "RECEIPT_DIGEST_MISMATCH")
        return value


@dataclass(frozen=True)
class SyntheticMetric:
    requirement: EvidenceRequirement
    quantity: Quantity


@dataclass(frozen=True)
class SyntheticEvidence:
    schema_version: Literal["synthetic-evidence-v1"]
    receipt: SyntheticReceipt
    evidence_id: str
    metrics: tuple[SyntheticMetric, ...]
    protocol_valid: bool

    @classmethod
    def from_dict(cls, raw):
        value = _parse(cls, strict_json(canonical_json(raw)))
        SyntheticReceipt.from_dict(asdict(value.receipt))
        identifier(value.evidence_id, "syntheticevidence")
        require(0 < len(value.metrics) <= 32, "METRIC_EVIDENCE_MISSING")
        for metric in value.metrics:
            metric.quantity.validate()
            require((metric.quantity.dimension, metric.quantity.unit)
                    == (metric.requirement.dimension, metric.requirement.unit), "UNIT_MISMATCH")
        require(len({canonical_json(asdict(m.requirement)) for m in value.metrics})
                == len(value.metrics), "DUPLICATE_METRIC")
        return value


class ExecutionPort(Protocol):
    """Trusted TEST infrastructure only; no production implementation is supplied."""
    source_id: str

    def accept(self, request: SyntheticRequest) -> SyntheticReceipt: ...

    def query(self, request: SyntheticRequest) -> SyntheticReceipt | None: ...


class EvidencePort(Protocol):
    source_id: str

    def read_evidence(self, request: SyntheticRequest,
                      receipt: SyntheticReceipt) -> SyntheticEvidence | None: ...


TERMINAL = {"SYNTHETIC_TARGET_MET", "SYNTHETIC_TARGET_UNMET", "BLOCKED"}
BLOCKS = {"MODEL_REJECTED", "BUDGET_BLOCKED", "EVIDENCE_INCONCLUSIVE", "CONTRACT_STALE",
          "HUMAN_REVIEW_REQUIRED"}


def key_for(definition, step):
    return "fake_" + definition.workflow_id.removeprefix("workflow_") + "_" + step


def operation_for(definition, step):
    return "wf_" + definition.workflow_id.removeprefix("workflow_") + "_" + step


def request_for(definition, step, record):
    return SyntheticRequest("synthetic-request-v1", definition.source_id, definition.workflow_id,
        definition.scope.research_project_id, definition.scope.refs, step,
        record["request"]["candidate_id"], record["manifest"]["output_digest"], key_for(definition, step),
        "syntheticattempt_" + digest_bytes(key_for(definition, step).encode())[7:39],
        "NOT_ABAQUS_QUALIFIED", "SYNTHETIC_TEST_ONLY", True, False)


def reservation_for(ledger, definition, step):
    matches = [(key, value) for key, value in ledger["reservations"].items()
               if value["request"]["operation_key"] == operation_for(definition, step)]
    require(len(matches) <= 1, "RESERVATION_MISMATCH")
    return matches[0] if matches else (None, None)


def compare(quantity, comparator, target, tolerance):
    # Input strings have at most 64 characters. Avoid the ambient 28-digit context.
    with localcontext() as context:
        context.prec = 256
        number, goal, delta = Decimal(quantity.value), Decimal(target.value), Decimal(tolerance.value)
        return {"LE": number <= goal + delta, "GE": number >= goal - delta,
                "EQ": abs(number - goal) <= delta}[comparator]


def verify(bundle, request, receipt, evidence):
    """Recompute every result from frozen rules, never consume an agent's PASS."""
    require(type(evidence) is SyntheticEvidence, "SYNTHETIC_EVIDENCE_REQUIRED")
    evidence = SyntheticEvidence.from_dict(asdict(evidence))
    require(evidence.receipt == receipt and receipt.request == request
            and request.refs == FrozenRefs(**bundle.digests())
            and request.research_project_id == bundle.research_project_id, "EVIDENCE_BINDING_MISMATCH")
    require(evidence.protocol_valid, "TEST_PROTOCOL_FAILED")
    metrics = {canonical_json(asdict(m.requirement)): m.quantity for m in evidence.metrics}
    required = {canonical_json(asdict(e)) for e in bundle.verification.required_evidence}
    require(set(metrics) == required, "REQUIRED_EVIDENCE_MISMATCH")
    objective = metrics[canonical_json(asdict(bundle.goal.objective))]
    objective_met = compare(objective, bundle.goal.comparator, bundle.goal.target, bundle.goal.tolerance)
    checks = {c.constraint_id: compare(metrics[canonical_json(asdict(c.evidence))],
                c.comparator, c.threshold, c.tolerance) for c in bundle.goal.hard_constraints}
    hard_pass = all(checks.values())
    return {"schema_version": "synthetic-verification-v1", "rule_version": "fixed-ab-v1",
        "rule_digest": digest_bytes(canonical_json({"goal": asdict(bundle.goal),
                                                    "verification": asdict(bundle.verification)})),
        "frozen_refs": bundle.digests(), "candidate_id": request.candidate_id,
        "request_digest": request.digest(), "receipt_id": receipt.receipt_id,
        "evidence_id": evidence.evidence_id, "evidence_digest": digest_bytes(canonical_json(plain(evidence))),
        "V0": "SYNTHETIC_PASS", "V1": "SYNTHETIC_MUTATION_PASS", "V2": "NOT_RUN",
        "test_protocol": "PASS", "V3": "MET" if objective_met and hard_pass else "NOT_MET",
        "objective_met": objective_met, "hard_constraint_checks": checks,
        "hard_constraints_pass": hard_pass, "V4": "NOT_ASSESSED",
        "missing_real_checks": ["V2"] + (["V4"] if bundle.verification.required_checks.V4 else []),
        "synthetic_continuation_eligible": hard_pass and not objective_met,
        "real_goal": "INCONCLUSIVE", "acceptance_eligibility": "SIMULATED_ONLY",
        "physical_evidence_eligible": False, "execution_authorized": False}


def decision_for(state, bundle, evidence, reservation_id, revision):
    request = SyntheticRequest.from_dict(state["request"])
    receipt = SyntheticReceipt.from_dict(state["receipt"])
    verification = verify(bundle, request, receipt, evidence)
    if not verification["hard_constraints_pass"]:
        reason, target = "HARD_CONSTRAINT_FAILED", "BLOCKED"
    elif verification["objective_met"]:
        reason, target = "SYNTHETIC_TARGET_MET", "SYNTHETIC_TARGET_MET"
    elif state["step_id"] == "A":
        reason, target = "VALID_SYNTHETIC_TARGET_MISS", "READY_B"
    else:
        reason, target = "TWO_STEP_LIMIT_REACHED", "SYNTHETIC_TARGET_UNMET"
    decision = {"schema_version": "synthetic-decision-v1", "author": "DETERMINISTIC_GDCAE_SYNTHETIC_V1",
        "workflow_id": state["workflow_id"], "step_id": state["step_id"],
        "original_project_revision": revision, "rule_version": "fixed-ab-v1",
        "rule_digest": verification["rule_digest"], "frozen_refs": bundle.digests(),
        "request_digest": request.digest(), "evidence_id": evidence.evidence_id,
        "evidence_digest": verification["evidence_digest"], "receipt_id": receipt.receipt_id,
        "reservation_id": reservation_id, "budget_effect": "ALREADY_CHARGED_ONCE",
        "reason": reason, "next_state": target, "source_classification": "SYNTHETIC_TEST_ONLY",
        "real_goal": "INCONCLUSIVE", "physical_evidence_eligible": False}
    decision["decision_id"] = "decision_" + digest_bytes(canonical_json(decision))[7:39]
    return verification, decision


def apply_workflow(state, payload, bundle, candidates, ledger, revision, latest):
    """Validate one event against same-transaction candidate/budget history."""
    require(type(payload) is dict and set(payload) == {
        "schema_version", "workflow_id", "before_project_revision", "action", "data"},
        "WORKFLOW_INTEGRITY_ERROR")
    require(payload["schema_version"] == "workflow-event-v1"
            and type(payload["before_project_revision"]) is int
            and payload["before_project_revision"] == revision, "WORKFLOW_REVISION_CONFLICT")
    identifier(payload["workflow_id"], "workflow")
    action, data = payload["action"], payload["data"]
    require(type(action) is str and type(data) is dict, "WORKFLOW_INTEGRITY_ERROR")
    if action == "CREATE":
        require(state is None, "WORKFLOW_ALREADY_EXISTS")
        definition = parse_definition(data)
        require(definition.workflow_id == payload["workflow_id"]
                and definition.scope == BudgetScope.from_bundle(bundle)
                and latest == definition.scope.refs.bundle, "CONTRACT_BINDING_MISMATCH")
        require(bundle.goal.budget.max_solver_calls == 2
                and bundle.goal.budget.max_candidate_proposals >= 2
                and not ledger["reservations"], "BUDGET_BLOCKED")
        for request in definition.candidates:
            validate_parent(bundle, request)
            require(request.project_revision == revision, "REVISION_CONFLICT")
            require(request.candidate_id not in candidates, "CANDIDATE_IDENTITY_CONFLICT")
        return {"workflow_id": definition.workflow_id, "definition": plain(definition),
                "state": "READY_A", "step_id": "A", "mutation_request": None,
                "request": None, "receipt": None, "decisions": [], "reason": None, "epoch": 1}
    require(state is not None and state["workflow_id"] == payload["workflow_id"]
            and state["state"] not in TERMINAL, "WORKFLOW_STATE_CONFLICT")
    state = copy.deepcopy(state)
    definition = parse_definition(state["definition"])
    require(definition.scope == BudgetScope.from_bundle(bundle), "CONTRACT_BINDING_MISMATCH")
    require(action == "BLOCK" or latest == definition.scope.refs.bundle, "STALE_CONTRACT")
    if action == "ADMIT_B":
        require(type(definition) is ProposalWorkflowDefinition and proposal_pending(state)
                and set(data) == {"capture", "admission"}, "PROPOSAL_NOT_ELIGIBLE")
        admission = admission_for(state, bundle, candidates, ledger, revision, data["capture"])
        require(data["admission"] == admission, "PROPOSAL_ADMISSION_INTEGRITY")
        state["proposal_admission"] = admission
        if admission["decision"] == "STOPPED":
            state.update(state="BLOCKED", reason="HUMAN_REVIEW_REQUIRED")
    elif action == "PREPARE":
        require(state["state"] in {"READY_A", "READY_B"}, "WORKFLOW_STATE_CONFLICT")
        step = "A" if state["state"] == "READY_A" else "B"
        if step == "B":
            require(len(state["decisions"]) == 1 and state["decisions"][0]["decision"]["reason"]
                    == "VALID_SYNTHETIC_TARGET_MISS", "B_NOT_ELIGIBLE")
        request = replace(template_for(state, definition, step), project_revision=revision + 1)
        require(data == plain(request), "MUTATION_BINDING_MISMATCH")
        state.update(state="PREPARED", step_id=step, mutation_request=data, request=None, receipt=None)
    elif action == "BLOCK":
        require(set(data) == {"reason"} and type(data["reason"]) is str
                and data["reason"] in BLOCKS, "INVALID_STOP_REASON")
        state.update(state="BLOCKED", reason=data["reason"])
    else:
        candidate = candidates.get(state["mutation_request"]["candidate_id"])
        require(candidate is not None and candidate["request"] == state["mutation_request"],
                "CANDIDATE_BINDING_MISMATCH")
        request = request_for(definition, state["step_id"], candidate)
        reservation_id, reservation = reservation_for(ledger, definition, state["step_id"])
        require(reservation is not None and reservation["request"]["scope"] == plain(definition.scope)
                and reservation["request"]["candidate_id"] == request.candidate_id
                and reservation["request"]["candidate_digest"] == request.candidate_digest
                and reservation["request"]["downstream_business_key"] == request.business_key
                and reservation["request"]["plan_digest"] == request.digest()
                and reservation["intent"] == {"business_key": request.business_key,
                                               "request_digest": request.digest()}, "INTENT_NOT_PROVEN")
        if action == "CLAIM":
            require(state["state"] == "PREPARED"
                    and reservation["state"] == "SUBMISSION_INTENT_RECORDED"
                    and data == plain(request), "CLAIM_CONFLICT")
            state.update(state="CLAIMED", request=data)
        elif action == "UNKNOWN":
            require(state["state"] in {"CLAIMED", "ACCEPTANCE_UNKNOWN"} and data == {}
                    and reservation["state"] == "ACCEPTANCE_UNKNOWN", "UNKNOWN_NOT_HELD")
            state.update(state="ACCEPTANCE_UNKNOWN", reason="ACCEPTANCE_UNKNOWN")
        elif action == "OBSERVE":
            receipt = SyntheticReceipt.from_dict(data)
            require(state["state"] in {"CLAIMED", "ACCEPTANCE_UNKNOWN"}
                    and receipt.request == request, "RECEIPT_BINDING_MISMATCH")
            state.update(state="OBSERVED", receipt=data, reason=None)
        elif action == "DECIDE":
            require(state["state"] == "OBSERVED" and reservation["state"] == "ACCEPTED_OR_CHARGED"
                    and set(data) == {"evidence", "verification", "decision"}, "DECISION_NOT_ELIGIBLE")
            evidence = SyntheticEvidence.from_dict(data["evidence"])
            verification, decision = decision_for(state, bundle, evidence, reservation_id, revision)
            require(data["verification"] == verification and data["decision"] == decision,
                    "DECISION_INTEGRITY_ERROR")
            state["decisions"].append(data)
            state.update(state=decision["next_state"], reason=("HUMAN_REVIEW_REQUIRED"
                         if decision["next_state"] == "BLOCKED" else decision["reason"]))
        else:
            require(False, "UNKNOWN_WORKFLOW_ACTION")
    state["epoch"] += 1
    return state
