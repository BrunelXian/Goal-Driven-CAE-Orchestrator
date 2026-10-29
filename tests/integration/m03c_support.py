"""Explicit TEST_ONLY challenge builder/ingress. No model call, no AF authority."""

import json
import sys
import uuid
from dataclasses import replace
from decimal import Decimal, localcontext
from pathlib import Path

from aegiscae.contracts.research_contracts import Quantity, canonical_json, digest_bytes, require
from aegiscae.research.candidate_proposal import CandidateProposal
from aegiscae.research import budget, mutation, project, workflow
from aegiscae.research.budget_rules import BudgetScope
from aegiscae.research.mutation_rules import parse_fixture
from aegiscae.research.proposal_rules import ProposalWorkflowDefinition
from aegiscae.research.workflow_rules import plain

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "fixtures"))
from synthetic_workflow_port import DurableSyntheticPort  # noqa: E402


def save(path, value):
    with path.open("xb") as stream:
        stream.write(canonical_json(value))


def read(path):
    project._path(path, directory=False, scope=False)
    return json.loads(path.read_bytes())


class ProportionalPort(DurableSyntheticPort):
    """Reuse existing durable effect/receipt engine; override metric policy only."""
    def _metric_value(self, request):
        rule = read(self.root / "proportional-rule.json")
        require(self.source_id == "syntheticport_" + digest_bytes(canonical_json(rule))[7:39],
                "TEST_ORACLE_CHANGED")
        research = project.open_existing_readonly(Path(rule["project_root"]))
        workspace = mutation.SyntheticWorkspace(Path(rule["workspace_root"]), rule["workspace_id"])
        candidate = mutation.inspect_candidate(research, workspace, request.candidate_id)
        require(candidate["admissibility"] == "PERMITTED"
                and candidate["candidate"]["manifest"]["output_digest"] == request.candidate_digest,
                "ORACLE_CANDIDATE_MISMATCH")
        template = candidate["candidate"]["request"]
        path = workspace._root / "staging" / template["output_identity"] / "candidate.txt"
        content = mutation._read_bytes(path)
        require(digest_bytes(content) == request.candidate_digest, "ORACLE_INPUT_CHANGED")
        scalar = parse_fixture(content)[0]
        with localcontext() as context:
            context.prec = 256
            result = Decimal(scalar) * Decimal(rule["a_response"]) / Decimal(rule["a_parameter"])
            text = format(result, "f")
        return text.rstrip("0").rstrip(".") if "." in text else text


def prepare(root, *, target="0.5", observation="2", narrative=None):
    root = mutation._test_root(Path(root), exists=False)
    root.mkdir()
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "unit"))
    from test_model_mutation import SOURCE, make_case

    def policy(raw):
        raw["goal"]["budget"]["max_solver_calls"] = 2
        raw["goal"]["target"]["value"] = target
        raw["goal"]["hard_constraints"][0]["threshold"]["value"] = "10"
        raw["verification"]["hard_constraint_checks"][0]["rule"]["threshold"]["value"] = "10"
        if narrative is not None:
            raw["model"]["assumptions"] = [narrative]
    case = make_case(root, body=SOURCE.replace(b"LOAD_N 10", b"LOAD_N 0"), change_contract=policy)
    a = replace(case.request, old_value=Quantity("0", "force", "N"), new_value=Quantity("40", "force", "N"))
    base = DurableSyntheticPort.create(root / "synthetic-port", case.bundle.verification.required_evidence)
    rule = {"schema": "synthetic-proportional-oracle-v1", "metric_source": "TEST_ORACLE",
        "physical_evidence_eligible": False, "project_root": str(case.root),
        "workspace_root": str(case.workspace._root), "workspace_id": case.workspace.workspace_id,
        "a_parameter": a.new_value.value, "a_response": observation}
    save(base.root / "proportional-rule.json", rule)
    config = read(base.root / "fixture.json")
    config["source_id"] = "syntheticport_" + digest_bytes(canonical_json(rule))[7:39]
    (base.root / "fixture.json").write_bytes(canonical_json(config))  # Owned setup, before any workflow/effect.
    case.port = ProportionalPort(base.root)
    case.scope = BudgetScope.from_bundle(case.bundle)
    case.definition = ProposalWorkflowDefinition("proposal-workflow-v1", "workflow_" + uuid.uuid4().hex,
        case.scope, case.port.source_id, (a,), 2, 2, "BLOCK", "challenge_" + uuid.uuid4().hex,
        "SYNTHETIC_PROPORTIONALITY_ONLY")
    workflow.create_workflow(case.writer, case.definition, 2)
    save(root / "definition.json", plain(case.definition))
    case.coordinator = workflow.WorkflowCoordinator(case.writer, case.workspace,
        case.definition.workflow_id, case.port, case.port)
    case.ledger = budget.BudgetLedger(case.writer, case.scope)
    case.fixture_root = root
    return case


def reopen(root):
    root = Path(root)
    definition = ProposalWorkflowDefinition.from_dict(read(root / "definition.json"))
    writer = project.open_existing_for_explicit_write(root / "research")
    workspace = mutation.SyntheticWorkspace(root / "synthetic", definition.candidates[0].workspace_id)
    port = ProportionalPort(root / "synthetic-port")
    return workflow.WorkflowCoordinator(writer, workspace, definition.workflow_id, port, port)


def until(coordinator, predicate):
    for _ in range(40):
        state = coordinator.inspect()
        if predicate(state):
            return state
        require(state["state"] not in {"BLOCKED", "SYNTHETIC_TARGET_MET", "SYNTHETIC_TARGET_UNMET"},
                "TEST_UNEXPECTED_STOP")
        coordinator.advance(state["project_revision"])
    raise AssertionError("TEST_ADVANCE_BOUND")


def checkpoint(case):
    return {"revision": case.writer.inspect()["project_revision"],
        "budget": case.ledger.inspect_budget(), "effects": case.port.oracle()["effects"],
        "candidate_directories": len(list((case.workspace._root / "staging").iterdir())),
        "admission": case.coordinator.inspect().get("proposal_admission")}


def ingest_exact(root, capture_path, *, available=True):
    """Trusted explicit test call. Never initiates a Codex turn or computes a B answer."""
    coordinator = reopen(root)
    if not available:
        return {"status": "AGENT_PROPOSAL_UNAVAILABLE", "execution_authorized": False}
    path = Path(capture_path)
    require(path.parent == Path(root), "CAPTURE_SCOPE_MISMATCH")
    try:
        project._path(path, directory=False, scope=False)
        require(path.stat().st_size <= 8192, "CAPTURE_LIMIT")
        with path.open("rb") as stream:
            raw = stream.read(8193)
    except (ValueError, OSError) as exc:
        return {"status": "AGENT_PROPOSAL_UNAVAILABLE", "reason": getattr(exc, "code", "CAPTURE_UNREADABLE"),
                "execution_authorized": False}
    try:
        CandidateProposal.from_bytes(raw)
    except ValueError as exc:
        return {"status": "AGENT_PROPOSAL_UNAVAILABLE", "reason": getattr(exc, "code", "MALFORMED_OUTPUT"),
                "original_sha256": digest_bytes(raw), "execution_authorized": False}
    try:
        state = coordinator.admit_proposal(raw)
        return {"status": state["proposal_admission"]["decision"],
                "original_sha256": digest_bytes(raw), "state": state}
    except (ValueError, OSError) as exc:
        return {"status": "REJECTED", "reason": getattr(exc, "code", type(exc).__name__),
                "original_sha256": digest_bytes(raw), "execution_authorized": False}
