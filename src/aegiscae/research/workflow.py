"""Explicit bounded advancement of one durable synthetic A/B workflow. No AF calls."""

import copy
from dataclasses import asdict, replace

from aegiscae.contracts.research_contracts import ContractError, digest_bytes, identifier, require
from aegiscae.research import mutation, project as store
from aegiscae.research.budget import BudgetLedger, SyntheticOracle
from aegiscae.research.budget_rules import apply_event, empty_ledger
from aegiscae.research.mutation_rules import MutationRequest
from aegiscae.research.proposal_rules import ProposalWorkflowDefinition, admission_for, brief_content, capture
from aegiscae.research.workflow_rules import (
    TERMINAL, SyntheticEvidence, SyntheticReceipt, SyntheticRequest, WorkflowDefinition,
    apply_workflow, decision_for, operation_for, plain, request_for, reservation_for,
    parse_definition, proposal_pending, template_for,
)


def _fault(stage):
    """Trusted failure injection only, never a user callback or continuation service."""


def _revision(value):
    require(type(value) is int and 1 <= value <= 1024, "INVALID_REVISION")


def _load(bundles, events):
    state, candidates, ledger, latest = None, {}, empty_ledger(), None
    parents = {row[1]: row[0] for row in bundles}
    for event in events:
        kind = event["kind"]
        if kind == "BUNDLE_FROZEN":
            latest = event["bundle_digest"]
        elif kind == "CANDIDATE_PUBLICATION_OBSERVED":
            candidate = event["candidate"]
            candidates[candidate["request"]["candidate_id"]] = candidate
        elif kind == "BUDGET_RECORDED":
            apply_event(ledger, event["budget"], parents[event["bundle_digest"]], candidates,
                        event["project_revision"] - 1, latest)
        elif kind == "WORKFLOW_RECORDED":
            state = apply_workflow(state, event["workflow"], parents[event["bundle_digest"]],
                candidates, ledger, event["project_revision"] - 1, latest)
    return state, candidates, ledger, latest


def _view(state, meta, ledger, candidates, latest):
    require(state is not None, "WORKFLOW_NOT_FOUND")
    definition = parse_definition(state["definition"])
    reservation_id, reservation = reservation_for(ledger, definition, state["step_id"])
    action = "STOP"
    if latest != definition.scope.refs.bundle:
        action = "CONTRACT_STALE"
    elif state["state"] in {"READY_A", "READY_B"}:
        action = "PROPOSAL_REQUIRED" if proposal_pending(state) else "PREPARE_CANDIDATE"
    elif state["state"] == "PREPARED":
        if state["mutation_request"]["candidate_id"] not in candidates:
            action = "PUBLISH_CANDIDATE"
        elif reservation is None:
            action = "RESERVE_BUDGET"
        elif reservation["intent"] is None:
            action = "RECORD_INTENT"
        else:
            action = "CLAIM_ONCE"
    elif state["state"] in {"CLAIMED", "ACCEPTANCE_UNKNOWN"}:
        action = "QUERY_ORIGINAL_KEY_ONLY"
    elif state["state"] == "OBSERVED":
        action = "READ_AND_DECIDE" if reservation["state"] == "ACCEPTED_OR_CHARGED" else "CHARGE_ONCE"
    return {**copy.deepcopy(state), "project_revision": meta["project_revision"],
        "scope": "CURRENT_FROZEN_CONTRACT" if latest == definition.scope.refs.bundle
        else "HISTORICAL_WORKFLOW",
        "next_action": action, "reservation_id": reservation_id,
        "reservation_state": reservation["state"] if reservation else None,
        "source_classification": "SYNTHETIC_TEST_ONLY", "test_only": True,
        "qualification": "NOT_ABAQUS_QUALIFIED", "physical_evidence_eligible": False,
        "execution_authorized": False, "real_goal": "INCONCLUSIVE",
        "AF_WORKFLOW_COMPATIBILITY_VERIFIED": False, "SCIENTIFIC_VERIFICATION_AVAILABLE": False,
        "ABAQUS_PARAMETERIZED_EXECUTION_VERIFIED": False,
        "CODEX_AUTOMATIC_MAIN_CONTINUATION_VERIFIED": False}


def historical_research_brief(bundles, events, revision):
    """Pure bounded reconstruction from already validated authoritative history."""
    _revision(revision)
    history = [e for e in events if e["project_revision"] <= revision]
    require(history and max(e["project_revision"] for e in history) == revision, "REVISION_CONFLICT")
    state, _candidates, ledger, latest = _load(bundles, history)
    require(state is not None, "WORKFLOW_NOT_FOUND")
    bundle = next(b[0] for b in bundles if b[1] == latest)
    return brief_content(state, bundle, ledger, revision)


def create_workflow(project, definition, expected_revision):
    _revision(expected_revision)
    require(type(project) is store.ResearchProject
            and type(definition) in (WorkflowDefinition, ProposalWorkflowDefinition),
            "INVALID_TYPE")
    definition = parse_definition(asdict(definition))
    with project._snapshot(write=True) as (connection, meta, bundles, events):
        state, candidates, ledger, latest = _load(bundles, events)
        if state is not None:
            require(state["definition"] == plain(definition), "WORKFLOW_DEFINITION_CONFLICT")
            return _view(state, meta, ledger, candidates, latest)
        require(meta["project_revision"] == expected_revision, "REVISION_CONFLICT")
        parent = next((b[0] for b in bundles if b[1] == definition.scope.refs.bundle), None)
        require(parent is not None, "CONTRACT_BINDING_MISMATCH")
        payload = {"schema_version": "workflow-event-v1", "workflow_id": definition.workflow_id,
                   "before_project_revision": expected_revision, "action": "CREATE",
                   "data": plain(definition)}
        state = apply_workflow(state, payload, parent, candidates, ledger, expected_revision, latest)
        store._commit_workflow_event(connection, meta, definition.scope.refs.bundle, payload)
        _fault("workflow_event_before_commit")
        connection.commit()
        _fault("workflow_event_after_commit")
        return _view(state, meta, ledger, candidates, latest)


class WorkflowCoordinator:
    """Each call takes at most one logical boundary. No background retry or agent loop."""

    def __init__(self, project, workspace, workflow_id, execution_port=None, evidence_port=None):
        require(type(project) is store.ResearchProject, "INVALID_TYPE")
        identifier(workflow_id, "workflow")
        self.project, self.workspace, self.workflow_id = project, workspace, workflow_id
        self.execution_port, self.evidence_port = execution_port, evidence_port

    def inspect(self):
        with self.project._snapshot() as (_, meta, bundles, events):
            state, candidates, ledger, latest = _load(bundles, events)
            require(state is not None and state["workflow_id"] == self.workflow_id,
                    "WORKFLOW_NOT_FOUND")
            return _view(state, meta, ledger, candidates, latest)

    def _event(self, action, data, expected_revision):
        with self.project._snapshot(write=True) as (connection, meta, bundles, events):
            require(meta["project_revision"] == expected_revision, "REVISION_CONFLICT")
            state, candidates, ledger, latest = _load(bundles, events)
            require(state is not None and state["workflow_id"] == self.workflow_id, "WORKFLOW_NOT_FOUND")
            definition = parse_definition(state["definition"])
            bundle = next(b[0] for b in bundles if b[1] == definition.scope.refs.bundle)
            if action == "ADMIT_B":
                data = {"capture": data, "admission": self._evaluate_snapshot(
                    meta, bundles, events, data)}
            if action in {"CLAIM", "DECIDE"}:
                # Independent file/span recheck inside the owning Project transaction.
                record = candidates.get(state["mutation_request"]["candidate_id"])
                require(record is not None, "MODEL_REJECTED")
                mutation._recheck(self.workspace, record, bundle,
                                  current_revision=meta["project_revision"], bundles=bundles)
            payload = {"schema_version": "workflow-event-v1", "workflow_id": self.workflow_id,
                       "before_project_revision": expected_revision, "action": action, "data": data}
            state = apply_workflow(state, payload, bundle, candidates, ledger, expected_revision, latest)
            store._commit_workflow_event(connection, meta, definition.scope.refs.bundle, payload)
            _fault("workflow_event_before_commit")
            connection.commit()
            _fault("workflow_event_after_commit")
            return _view(state, meta, ledger, candidates, latest)

    def _block(self, reason, revision):
        return self._event("BLOCK", {"reason": reason}, revision)

    def research_brief(self):
        """Sanitized view of one validated read snapshot; contains no B answer or paths."""
        with self.project._snapshot() as (_, meta, bundles, events):
            state, candidates, ledger, latest = _load(bundles, events)
            require(state is not None and state["workflow_id"] == self.workflow_id, "WORKFLOW_NOT_FOUND")
            definition = parse_definition(state["definition"])
            require(latest == definition.scope.refs.bundle, "STALE_CONTRACT")
            bundle = next(b[0] for b in bundles if b[1] == latest)
            brief = brief_content(state, bundle, ledger, meta["project_revision"])
            record = candidates.get(definition.candidates[0].candidate_id)
            require(record is not None, "A_CANDIDATE_MISSING")
            mutation._recheck(self.workspace, record, bundle,
                current_revision=meta["project_revision"], bundles=bundles)
            return {**brief, "read_at_utc": store._utc()}

    def admit_proposal(self, raw):
        """Explicit trusted ingress only. Agent text has no machine verdict rights."""
        captured = capture(raw)
        current = self.inspect()
        previous = current.get("proposal_admission")
        if previous is not None:
            require(previous["capture"] == captured, "PROPOSAL_CONTENT_CONFLICT")
            return current
        return self._event("ADMIT_B", captured, current["project_revision"])

    def _evaluate_snapshot(self, meta, bundles, events, captured):
        """Shared deterministic dry-run and committing admission checks; no publication."""
        state, candidates, ledger, latest = _load(bundles, events)
        require(state is not None and state["workflow_id"] == self.workflow_id, "WORKFLOW_NOT_FOUND")
        definition = parse_definition(state["definition"])
        require(latest == definition.scope.refs.bundle, "STALE_CONTRACT")
        bundle = next(b[0] for b in bundles if b[1] == latest)
        result = admission_for(state, bundle, candidates, ledger, meta["project_revision"], captured)
        original = candidates.get(definition.candidates[0].candidate_id)
        require(original is not None, "A_CANDIDATE_MISSING")
        mutation._recheck(self.workspace, original, bundle,
            current_revision=meta["project_revision"], bundles=bundles)
        if result["candidate_template"] is not None:
            candidate = MutationRequest.from_dict(result["candidate_template"])
            before = mutation._read_bytes(self.workspace._root / candidate.source_filename)
            mutation.check_diff(before, mutation.edit_scalar(before, candidate), candidate, bundle)
        return result

    def evaluate_proposal(self, raw):
        """Snapshot eligibility only; not admission, approval, reservation or execution."""
        captured = capture(raw)
        with self.project._snapshot() as (_, meta, bundles, events):
            return self._evaluate_snapshot(meta, bundles, events, captured)

    def advance(self, expected_revision):
        _revision(expected_revision)
        require(self.project._write_enabled, "READ_ONLY")
        try:
            return self._advance(expected_revision)
        except store.ProjectError as exc:
            if exc.code != "STORE_BUSY":
                raise
            # No journal writes, clearing, refund or positive-state inference.
            return {"workflow_id": self.workflow_id, "state": "JOURNAL_BLOCKED",
                    "reason": "JOURNAL_BLOCKED", "persisted": False,
                    "source_classification": "SYNTHETIC_TEST_ONLY", "execution_authorized": False,
                    "physical_evidence_eligible": False, "next_action": "STOP"}

    def _advance(self, expected_revision):
        current = self.inspect()
        require(current["project_revision"] == expected_revision, "REVISION_CONFLICT")
        if current["state"] in TERMINAL:
            return current
        if current["next_action"] == "CONTRACT_STALE":
            return self._block("CONTRACT_STALE", expected_revision)
        if proposal_pending(current):
            return current  # No B template, publication, budget reservation or effect.
        definition = parse_definition(current["definition"])
        bundle = self.project.read_frozen_bundle(definition.scope.refs.bundle)["bundle"]
        oracle = SyntheticOracle()
        ledger = BudgetLedger(self.project, definition.scope, oracle)
        if current["state"] in {"READY_A", "READY_B"}:
            if ledger.inspect_budget()["available"] < 1:
                return self._block("BUDGET_BLOCKED", expected_revision)
            if current["state"] == "READY_B":
                _fault("before_b_admission")
            step = "A" if current["state"] == "READY_A" else "B"
            request = replace(template_for(current, definition, step), project_revision=expected_revision + 1)
            return self._event("PREPARE", plain(request), expected_revision)
        if current["state"] == "PREPARED":
            return self._prepare(current, definition, ledger, expected_revision)
        request = SyntheticRequest.from_dict(current["request"])
        if current["state"] in {"CLAIMED", "ACCEPTANCE_UNKNOWN"}:
            require(self.execution_port is not None
                    and self.execution_port.source_id == definition.source_id, "SYNTHETIC_PORT_REQUIRED")
            try:
                receipt = self.execution_port.query(request)
            except Exception:
                receipt = None  # Unknown query never means absence or safe resubmission.
            if receipt is None:
                return self._unknown(current, ledger, oracle, request, expected_revision)
            try:
                require(type(receipt) is SyntheticReceipt, "SYNTHETIC_RECEIPT_REQUIRED")
                receipt = SyntheticReceipt.from_dict(asdict(receipt))
                require(receipt.request == request, "RECEIPT_BINDING_MISMATCH")
            except ContractError:
                return self._block("EVIDENCE_INCONCLUSIVE", expected_revision)
            return self._event("OBSERVE", plain(receipt), expected_revision)
        receipt = SyntheticReceipt.from_dict(current["receipt"])
        if current["reservation_state"] != "ACCEPTED_OR_CHARGED":
            observation = oracle.issue(current["reservation_id"], request.business_key, request.digest(),
                "ACCEPTED", "fixture_" + receipt.request_digest[7:39], "ACCEPTED_FIXTURE")
            ledger.observe_synthetic_acceptance_or_unknown(current["reservation_id"], observation,
                                                          expected_revision)
            _fault("after_charge")
            return self.inspect()
        require(self.evidence_port is not None and self.evidence_port.source_id == definition.source_id,
                "SYNTHETIC_PORT_REQUIRED")
        try:
            evidence = self.evidence_port.read_evidence(request, receipt)
        except Exception:
            evidence = None
        _fault("after_evidence")
        try:
            require(type(evidence) is SyntheticEvidence, "SYNTHETIC_EVIDENCE_REQUIRED")
            evidence = SyntheticEvidence.from_dict(asdict(evidence))
            verification, decision = decision_for(current, bundle, evidence,
                                                  current["reservation_id"], expected_revision)
        except ContractError:
            return self._block("EVIDENCE_INCONCLUSIVE", expected_revision)
        _fault("before_decision")
        try:
            result = self._event("DECIDE", {"evidence": plain(evidence), "verification": verification,
                                          "decision": decision}, expected_revision)
        except (ContractError, store.ProjectError, OSError) as exc:
            if isinstance(exc, (ContractError, store.ProjectError)) and exc.code in {
                    "REVISION_CONFLICT", "STORE_BUSY"}:
                raise
            return self._block("MODEL_REJECTED", expected_revision)
        _fault("after_decision")
        return result

    def _prepare(self, current, definition, ledger, revision):
        mutation_request = MutationRequest.from_dict(current["mutation_request"])
        result = mutation.propose_mutation(self.project, self.workspace, mutation_request)
        if result["admissibility"] != "PERMITTED":
            if result["reason"] == "STORE_BUSY":
                raise store.ProjectError("STORE_BUSY")
            return self._block("MODEL_REJECTED", revision)
        record = result["candidate"]
        # Publication is its own durable boundary. Replaying it never writes another file.
        if not result["replayed"]:
            _fault("after_candidate")
            return self.inspect()
        request = request_for(definition, current["step_id"], record)
        if current["reservation_id"] is None:
            _fault("before_reserve")
            try:
                ledger.reserve_for_candidate(request.candidate_id, request.candidate_digest, 1,
                    operation_for(definition, current["step_id"]), request.business_key, revision,
                    plan_digest=request.digest())
            except ContractError as exc:
                if exc.code == "REVISION_CONFLICT":
                    raise
                return self._block("BUDGET_BLOCKED", revision)
            _fault("after_reserve")
            return self.inspect()
        if current["reservation_state"] == "RESERVED":
            _fault("before_intent")
            ledger.record_submission_intent(current["reservation_id"], request.business_key,
                                             request.digest(), revision)
            _fault("after_intent")
            return self.inspect()
        if current["reservation_state"] != "SUBMISSION_INTENT_RECORDED":
            return self._block("BUDGET_BLOCKED", revision)
        require(self.execution_port is not None and self.execution_port.source_id == definition.source_id,
                "SYNTHETIC_PORT_REQUIRED")
        try:
            self._event("CLAIM", plain(request), revision)
        except (ContractError, store.ProjectError, OSError) as exc:
            if isinstance(exc, (ContractError, store.ProjectError)) and exc.code in {
                    "REVISION_CONFLICT", "STORE_BUSY"}:
                raise
            return self._block("MODEL_REJECTED", revision)
        _fault("after_claim")
        _fault("before_effect")
        try:
            # Only the successful NEW claim reaches here. Response is not evidence:
            # a later explicit advance must query this original request identity.
            self.execution_port.accept(request)
        except Exception:
            pass
        _fault("after_effect")
        return self.inspect()

    def _unknown(self, current, ledger, oracle, request, revision):
        if current["reservation_state"] != "ACCEPTANCE_UNKNOWN":
            observation = oracle.issue(current["reservation_id"], request.business_key, request.digest(),
                "UNKNOWN", "fixture_" + digest_bytes((request.business_key + "unknown").encode())[7:39],
                "RESPONSE_LOST")
            ledger.observe_synthetic_acceptance_or_unknown(current["reservation_id"], observation, revision)
            return self.inspect()
        if current["state"] != "ACCEPTANCE_UNKNOWN":
            return self._event("UNKNOWN", {}, revision)
        return current
