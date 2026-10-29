"""Pure research brief/admission rules, replayed by the existing workflow reducer."""

from dataclasses import asdict, dataclass, replace
from decimal import Decimal
from typing import Literal

from aegiscae.research.candidate_proposal import CandidateProposal
from aegiscae.contracts.research_contracts import (
    Quantity, _parse, canonical_json, digest_bytes, identifier, require, strict_json,
)
from aegiscae.research.budget_rules import BudgetScope, counters
from aegiscae.research.mutation_rules import MutationRequest, validate_parent


@dataclass(frozen=True)
class ProposalWorkflowDefinition:
    schema_version: Literal["proposal-workflow-v1"]
    workflow_id: str
    scope: BudgetScope
    source_id: str
    candidates: tuple[MutationRequest, ...]
    max_steps: Literal[2]
    budget_units: Literal[2]
    on_unknown: Literal["BLOCK"]
    challenge_id: str
    hypothesis: Literal["SYNTHETIC_PROPORTIONALITY_ONLY"]

    @classmethod
    def from_dict(cls, raw):
        value = _parse(cls, strict_json(canonical_json(raw)))
        for name, prefix in (("workflow_id", "workflow"), ("source_id", "syntheticport"),
                             ("challenge_id", "challenge")):
            identifier(vars(value)[name], prefix)
        BudgetScope.from_dict(asdict(value.scope))
        require(len(value.candidates) == 1, "ONLY_A_MAY_BE_PREDEFINED")
        candidate = MutationRequest.from_dict(asdict(value.candidates[0]))
        require(candidate.refs == value.scope.refs
                and candidate.research_project_id == value.scope.research_project_id,
                "CONTRACT_BINDING_MISMATCH")
        # This first proposal contract deliberately has one exact synthetic entity grammar.
        require((candidate.parameter, candidate.instance, candidate.entity_id, candidate.step,
                 candidate.entity_kind, candidate.frame, candidate.dof)
                == ("load_magnitude", "Beam", "Tip", "Load", "NODE_SET", 1, 1), "UNSUPPORTED_PROPOSAL_SCOPE")
        return value


def brief_content(state, bundle, ledger, revision):
    definition = ProposalWorkflowDefinition.from_dict(state["definition"])
    require(state["state"] == "READY_B" and state.get("proposal_admission") is None
            and len(state["decisions"]) == 1, "PROPOSAL_NOT_ELIGIBLE")
    previous = state["decisions"][0]
    verification, decision, evidence = (previous[k] for k in ("verification", "decision", "evidence"))
    require(decision["reason"] == "VALID_SYNTHETIC_TARGET_MISS"
            and verification["test_protocol"] == "PASS"
            and verification["hard_constraints_pass"] is True
            and verification["objective_met"] is False
            and evidence["receipt"]["request"]["step_id"] == "A", "A_EVIDENCE_INCONCLUSIVE")
    template = definition.candidates[0]
    totals = counters(ledger)
    unknown = sum(r["request"]["cost"] for r in ledger["reservations"].values()
                  if r["state"] == "ACCEPTANCE_UNKNOWN")
    refs = bundle.digests()
    require(len(evidence["metrics"]) == 1 and len(bundle.verification.required_evidence) == 1,
            "UNSUPPORTED_PROPOSAL_METRICS")
    content = {"brief_schema": "research-brief-v1", "challenge_id": definition.challenge_id,
        "research_project_id": bundle.research_project_id, "workflow_run_id": definition.workflow_id,
        "project_revision": revision, "frozen_refs": refs,
        "previous_candidate_id": template.candidate_id,
        "evidence_source_id": definition.source_id,
        "previous_decision_ref": decision["decision_id"], "evidence_refs": [evidence["evidence_id"]],
        "allowed_mutation": {"parameter": template.parameter, "unit": "N", "entity": "Beam.Tip",
            "step": template.step, "lower": template.lower.value, "upper": template.upper.value},
        "prohibited_edits": ["material", "boundary", "mesh", "contact", "geometry", "criteria"],
        "budget": {"available": totals["available"], "reserved": totals["held"],
                   "consumed": totals["charged"], "unknown": unknown},
        "observation_a": {"source": "TEST_ORACLE", "parameter_value": template.new_value.value,
            "parameter_unit": "N", "response": evidence["metrics"][0]["quantity"],
            "evidence_digest": verification["evidence_digest"]},
        "objective": {"comparator": bundle.goal.comparator, "target": asdict(bundle.goal.target),
                      "tolerance": asdict(bundle.goal.tolerance)},
        "hard_constraints": [{"constraint_id": c.constraint_id, "comparator": c.comparator,
                              "threshold": asdict(c.threshold), "tolerance": asdict(c.tolerance)}
                             for c in bundle.goal.hard_constraints],
        "hypothesis": definition.hypothesis,
        "hypothesis_limit": "Test assumption only. One datum does not establish physical proportionality.",
        "af_fake_refs": [], "af_dynamic_candidate": "NOT_AF_EXECUTED",
        "evidence_completeness": "COMPLETE_SYNTHETIC_ONLY", "V0": "SYNTHETIC_PASS",
        "V1": "SYNTHETIC_MUTATION_PASS", "V2": "NOT_RUN", "V3": "NOT_MET", "V4": "NOT_ASSESSED",
        "physical_evidence_eligible": False, "one_turn_proposal_budget": 1}
    content["brief_digest"] = digest_bytes(canonical_json(content))
    return content


def capture(raw):
    CandidateProposal.from_bytes(raw)
    text = raw.decode("utf-8")
    return {"source": "UNTRUSTED_AGENT_OUTPUT", "original_sha256": digest_bytes(raw),
            "chunks": [text[i:i + 512] for i in range(0, len(text), 512)]}


def admission_for(state, bundle, candidates, ledger, revision, captured):
    require(set(captured) == {"source", "original_sha256", "chunks"}
            and captured["source"] == "UNTRUSTED_AGENT_OUTPUT"
            and type(captured["chunks"]) is list and 1 <= len(captured["chunks"]) <= 16
            and all(type(s) is str and len(s) <= 512 for s in captured["chunks"]), "CAPTURE_INVALID")
    raw = "".join(captured["chunks"]).encode("utf-8")
    require(digest_bytes(raw) == captured["original_sha256"], "CAPTURE_DIGEST_MISMATCH")
    proposal = CandidateProposal.from_bytes(raw)
    brief = brief_content(state, bundle, ledger, revision)
    definition = ProposalWorkflowDefinition.from_dict(state["definition"])
    require(proposal.expected_project_revision == revision, "REVISION_CONFLICT")
    require(proposal.challenge_id == definition.challenge_id
            and proposal.research_project_id == bundle.research_project_id
            and proposal.workflow_run_id == definition.workflow_id
            and proposal.brief_digest == brief["brief_digest"]
            and proposal.goal_digest == brief["frozen_refs"]["goal"]
            and proposal.model_contract_digest == brief["frozen_refs"]["model"]
            and proposal.verification_contract_digest == brief["frozen_refs"]["verification"]
            and proposal.previous_candidate_id == brief["previous_candidate_id"]
            and proposal.previous_decision_ref == brief["previous_decision_ref"]
            and list(proposal.evidence_refs) == brief["evidence_refs"], "PROPOSAL_BINDING_MISMATCH")
    require(brief["budget"]["unknown"] == 0 and brief["budget"]["available"] >= 1, "BUDGET_BLOCKED")
    value = {"schema": "proposal-admission-v1", "capture": captured, "brief_digest": brief["brief_digest"],
             "at_project_revision": revision + 1, "decision": "STOPPED",
             "candidate_template": None, "real_goal": "INCONCLUSIVE",
             "execution_authorized": False, "physical_evidence_eligible": False,
             "af_dynamic_candidate": "NOT_AF_EXECUTED"}
    if proposal.action == "PROPOSE_CANDIDATE":
        template = definition.candidates[0]
        mutation = proposal.proposed_mutation
        require(Decimal(template.lower.value) <= Decimal(mutation.decimal_value) <= Decimal(template.upper.value),
                "OUT_OF_RANGE")
        token = digest_bytes((definition.challenge_id + captured["original_sha256"]).encode())[7:39]
        candidate = replace(template, candidate_id="candidate_" + token,
            output_identity="stage_" + token, idempotency_key="proposal_" + token,
            project_revision=revision + 1, new_value=Quantity(mutation.decimal_value, "force", "N"))
        MutationRequest.from_dict(asdict(candidate))
        validate_parent(bundle, candidate)
        require(candidate.candidate_id not in candidates, "CANDIDATE_IDENTITY_CONFLICT")
        value.update(decision="ADMITTED_SYNTHETIC_ONLY", candidate_template=asdict(candidate))
    return value
