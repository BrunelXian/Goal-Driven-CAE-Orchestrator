"""Trusted isolated TEST setup and post-MCP gate; no model launcher or execution."""

from aegiscae.research.proposal_ingress import ProposalIngress, issue_challenge
from aegiscae.research.proposal_review import evaluate_recorded
from aegiscae.research.budget import BudgetLedger
from aegiscae.research.budget_rules import BudgetScope
from aegiscae.contracts.research_contracts import canonical_json
from m03c_support import checkpoint, prepare, read, reopen, save, until


def prepare_ingress(root, *, target="0.5", policy_mode="AUTO_TEST_SYNTHETIC"):
    case = prepare(root, target=target)
    until(case.coordinator, lambda s: s["next_action"] == "PROPOSAL_REQUIRED")
    challenge = issue_challenge(case.coordinator, policy_mode=policy_mode)
    save(root / "proposal-startup.json", {"schema": "proposal-mcp-startup-v1", "test_only": True,
        "root": str(case.root), "research_project_id": case.bundle.research_project_id,
        "challenge_id": case.definition.challenge_id})
    save(root / "before-ingress.json", checkpoint(case))
    save(root / "challenge.json", challenge)
    return case


def evaluate_after_mcp(root):
    coordinator = reopen(root)
    ingress = ProposalIngress.from_startup_file(root / "proposal-startup.json")
    before = ingress.status()
    save(root / "recorded-before-gate.json", before)
    result = evaluate_recorded(ingress, coordinator.workspace)
    save(root / "gate-result.json", result)
    after = ingress.status()
    save(root / "status-after-gate.json", after)
    assert before["receipt"] == after["receipt"] and before["decisions"] is None
    assert result == evaluate_recorded(ingress, coordinator.workspace)
    expected = read(root / "before-ingress.json")
    current = coordinator.inspect()
    assert current["project_revision"] == expected["revision"] and current.get("proposal_admission") is None
    assert coordinator.execution_port.oracle()["effects"] == expected["effects"]
    scope = BudgetScope.from_dict(current["definition"]["scope"])
    assert canonical_json(BudgetLedger(coordinator.project, scope).inspect_budget()) == canonical_json(expected["budget"])
    assert len(list((coordinator.workspace._root / "staging").iterdir())) == expected["candidate_directories"]
    save(root / "after-gate-invariants.json", {"revision": current["project_revision"],
        "budget": expected["budget"], "effects": expected["effects"],
        "candidate_directories": expected["candidate_directories"], "admission": None})
    return result
