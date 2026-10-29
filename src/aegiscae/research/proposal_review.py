"""Explicit trusted snapshot evaluation. Never called by the proposal MCP handler."""

import uuid

from aegiscae.contracts.research_contracts import ContractError, require
from aegiscae.research import ingress_store as journal, project as store
from aegiscae.research.candidate_proposal import CandidateProposal
from aegiscae.research.proposal_ingress import _active, _validate_gate, review_for
from aegiscae.research.proposal_rules import capture
from aegiscae.research.workflow import WorkflowCoordinator


def evaluate_recorded(ingress, workspace):
    """Gate and frozen-policy disposition commit together, separately from receipt.

    No Candidate, ledger write, Workflow admission or continuation. Snapshot decisions
    are historical evidence; a later real admission must repeat the existing CAS checks.
    """
    with journal.connection_for(ingress._project._root, write=True) as connection:
        with ingress._project._snapshot() as (_, meta, bundles, events):
            state, history = ingress._read(connection, meta, bundles, events)
            require(state["record"] is not None, "PROPOSAL_NOT_RECORDED")
            if state["gate"] is not None:
                return state["gate"]  # Exact historical decision, never new authority.
            challenge, record = state["challenge"], state["record"]
            status, reason = "INCONCLUSIVE", "AUTHORITATIVE_STATE_UNAVAILABLE"
            at = store._utc()
            try:
                _active(state, at)
                require(meta["project_revision"] == challenge["brief"]["project_revision"], "REVISION_CONFLICT")
                raw = "".join(record["raw_chunks"]).encode("utf-8")
                coordinator = WorkflowCoordinator(ingress._project, workspace,
                                                  challenge["brief"]["workflow_run_id"])
                coordinator._evaluate_snapshot(meta, bundles, events, capture(raw))
                proposal = CandidateProposal.from_bytes(raw)
                if proposal.action != "PROPOSE_CANDIDATE":
                    status, reason = "HUMAN_REVIEW_REQUIRED", "AGENT_REQUESTED_STOP"
                elif challenge["policy"]["mode"] == "REQUIRE_HUMAN_REVIEW":
                    status, reason = "HUMAN_REVIEW_REQUIRED", "POLICY_REQUIRES_HUMAN"
                else:
                    status, reason = "ADMISSIBLE_SYNTHETIC_ONLY", "ELIGIBLE_SYNTHETIC"
            except (ContractError, store.ProjectError) as exc:
                if exc.code in {"CHALLENGE_EXPIRED", "CHALLENGE_REVOKED", "REVISION_CONFLICT", "BUDGET_BLOCKED", "STORE_BUSY"}:
                    reason = exc.code
                elif exc.code in {"OUT_OF_RANGE", "NO_CHANGE", "MODEL_REJECTED", "FORBIDDEN_DIFF"}:
                    status, reason = "REJECTED", "MODEL_REJECTED"
            except OSError:
                pass
            receipt = record["receipt"]
            admission = {"schema": "admission-decision-v1", "decision_id": "admissiondecision_" + uuid.uuid4().hex,
                "receipt_id": receipt["receipt_id"], "challenge_digest": receipt["challenge_digest"],
                "proposal_digest": receipt["proposal_digest"],
                "expected_revision": challenge["brief"]["project_revision"],
                "checked_revision": meta["project_revision"], "status": status, "reason": reason,
                "evidence_refs": challenge["brief"]["evidence_refs"], "execution_authorized": False}
            result = {"admission": admission, "review": review_for(challenge, admission)}
            _validate_gate(result, challenge, receipt)
            journal.append(connection, history, "GATE", result, at)
            return result
