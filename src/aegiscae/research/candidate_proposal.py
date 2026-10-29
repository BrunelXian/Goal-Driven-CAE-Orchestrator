"""Untrusted proposal DTO using existing contract primitives, never authority."""

import re
from dataclasses import dataclass
from typing import Literal

from aegiscae.contracts.research_contracts import (
    Quantity, _parse, canonical_json, digest, identifier, require, strict_json,
)


@dataclass(frozen=True)
class ProposedMutation:
    parameter: Literal["load_magnitude"]
    decimal_value: str
    unit: Literal["N"]
    entity: Literal["Beam.Tip"]
    step: Literal["Load"]


@dataclass(frozen=True)
class CandidateProposal:
    proposal_schema: Literal["candidate-proposal-v1"]
    challenge_id: str
    research_project_id: str
    workflow_run_id: str
    expected_project_revision: int
    brief_digest: str
    goal_digest: str
    model_contract_digest: str
    verification_contract_digest: str
    previous_candidate_id: str
    previous_decision_ref: str
    evidence_refs: tuple[str, ...]
    action: Literal["PROPOSE_CANDIDATE", "STOP", "REQUEST_REVIEW"]
    proposed_mutation: ProposedMutation | None
    rationale: str
    assumptions: tuple[str, ...]
    uncertainty: tuple[str, ...]
    reviewer_findings: tuple[str, ...]

    @classmethod
    def from_bytes(cls, raw):
        require(type(raw) is bytes and 0 < len(raw) <= 8192, "AGENT_PROPOSAL_UNAVAILABLE")
        value = _parse(cls, strict_json(raw))
        for field, prefix in (("challenge_id", "challenge"), ("research_project_id", "rp"),
                              ("workflow_run_id", "workflow"), ("previous_candidate_id", "candidate"),
                              ("previous_decision_ref", "decision")):
            identifier(vars(value)[field], prefix)
        require(type(value.expected_project_revision) is int
                and 1 <= value.expected_project_revision <= 1024, "INVALID_REVISION")
        for item in (value.brief_digest, value.goal_digest, value.model_contract_digest,
                     value.verification_contract_digest):
            digest(item)
        require(len(value.evidence_refs) == 1, "EXACT_EVIDENCE_REQUIRED")
        identifier(value.evidence_refs[0], "syntheticevidence")
        require((value.action == "PROPOSE_CANDIDATE") == (value.proposed_mutation is not None),
                "ACTION_MUTATION_MISMATCH")
        if value.proposed_mutation:
            Quantity(value.proposed_mutation.decimal_value, "force", "N").validate()
        require(1 <= len(value.assumptions) <= 4 and 1 <= len(value.uncertainty) <= 4
                and len(value.reviewer_findings) <= 4, "BOUNDED_EXPLANATION_REQUIRED")
        for text in (value.rationale, *value.assumptions, *value.uncertainty, *value.reviewer_findings):
            require(re.fullmatch(r"[\w .,()\-]{1,512}", text) is not None, "UNSAFE_PROPOSAL_TEXT")
            require(not any(word in text.casefold() for word in (
                "ignore", "grant", "approved", "authorized", "af_", "v2 pass", "v4 pass",
                "system prompt", "powershell", "bash", "cmd", "delete", "http", "execute")),
                "UNSAFE_PROPOSAL_TEXT")
        canonical_json(strict_json(raw))
        return value
