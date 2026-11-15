"""Reviewed role contracts. A recommendation never dispatches a session."""
from dataclasses import asdict, dataclass

from aegiscae.contracts.research_contracts import canonical_json, digest_bytes, require


@dataclass(frozen=True)
class RoleDefinition:
    role: str
    task_type: str
    inputs: str
    deliverable: str
    tools: tuple
    evidence: str


DEFINITIONS = (
    RoleDefinition("CAE", "model-qualification", "model version and intended use",
                   "model inspection and unresolved assumptions", ("model-read",), "asset digest and selectors"),
    RoleDefinition("Diagnostics", "capability-discovery", "operator-specified installation",
                   "installation, interface, project and permission observations", ("metadata-read",), "metadata digest"),
    RoleDefinition("ODB", "result-extraction", "authorized result asset",
                   "selected result series with units", ("result-read",), "result digest and selectors"),
    RoleDefinition("Independent Validation", "independent-review", "frozen criterion and independent reference",
                   "independent assessment for Main", ("evidence-read",), "independent provenance and criterion"),
    RoleDefinition("Optimization", "candidate-design", "frozen bounds and baseline",
                   "candidate proposal", ("contract-read",), "baseline and proposal digest"),
    RoleDefinition("Research", "research-review", "question and public reference",
                   "research evidence summary", ("reference-read",), "source and citation"),
)


def match(task_type, definitions=DEFINITIONS):
    matches = [item for item in definitions if item.task_type == task_type]
    require(len(matches) == 1, "ROLE_MATCH_UNRESOLVED")
    contract = asdict(matches[0])
    contract["tools"] = list(contract["tools"])
    return {**contract, "definition_sha256": digest_bytes(canonical_json(contract)),
            "session_status": "BLOCKED_HOST_ROLE_BINDING", "execution_authorized": False}
