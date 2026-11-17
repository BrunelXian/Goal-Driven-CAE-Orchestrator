"""Standard SDK client checks for agent proposals, durable receipts and unconfigured backends."""

import asyncio
import json
import sys
from pathlib import Path

from aegiscae.interfaces.research_scope import authorize

REPO = Path(__file__).resolve().parents[2]
EXAMPLE = REPO / "examples" / "cae_agent"
sys.path.insert(0, str(EXAMPLE))
from scenario import event, proposal, stdio_connect


def open_scope(root, contract, budget=3):
    binding = root / "scope.json"
    grant = authorize(binding, root / "research", contract=contract, max_executions=budget)
    return ({"project_id": grant["project_id"]},
            stdio_connect(binding, grant["binding_sha256"], source=REPO / "src"))


def test_proposals_require_scope_explicit_typed_input_and_evidence(tmp_path):
    contract = json.loads((EXAMPLE / "contract.json").read_text(encoding="utf-8"))
    pid, connect = open_scope(tmp_path, contract)

    async def run():
        async with connect() as call:
            opened = (await call("gdcae_project_open", {}))["data"]
            started = (await call("gdcae_workflow_start", event(pid["project_id"], opened, "start")))["data"]
            assert started["contract"] == contract and started["next_action"] == "PROPOSE_CANDIDATE"
            key = event(pid["project_id"], started, "agent-proposal")
            good = proposal(contract, {"value": "19.5", "reason": "Protocol test candidate"}, [])
            assert (await call("gdcae_workflow_advance", key))["error"] == "AGENT_PROPOSAL_REQUIRED"
            for change, code in (
                ({"value": "201"}, "PARAMETER_OUT_OF_BOUNDS"), ({"unit": "m"}, "UNIT_MISMATCH"),
                ({"baseline_digest": "a" * 64}, "BASELINE_MISMATCH"),
                ({"evidence_refs": ["b" * 64]}, "PROPOSAL_EVIDENCE_MISMATCH"),
                ({"parameter": "unknown"}, "PARAMETER_MISMATCH"), ({"value": 1}, "INVALID_ARGUMENTS"),
            ):
                result = await call("gdcae_candidate_propose", dict(key, proposal={**good, **change}))
                assert result["error"] == code
            assert (await call("gdcae_workflow_status", pid))["data"] == started
            assert (await call("gdcae_candidate_propose", dict(key, proposal=good, approved=True)))["error"]
            assert (await call("gdcae_candidate_propose",
                               dict(key, proposal=good, project_id="rp_" + "0" * 32)))["error"] == "PROJECT_MISMATCH"
            assert (await call("gdcae_candidate_propose",
                               dict(key, proposal=good, expected_revision=opened["revision"])))["error"] == "REVISION_CONFLICT"
            requested = dict(key, proposal=good)
            proposed = await call("gdcae_candidate_propose", requested)
            assert proposed["data"]["runs_used"] == 0

        async with connect() as call:
            status = (await call("gdcae_workflow_status", {**pid, "request_key": key["key"]}))["data"]
            assert status["request_receipt"]["proposal"] == good
            assert await call("gdcae_candidate_propose", requested) == proposed
            changed = dict(key, proposal={**good, "reason": "Divergent key content"})
            assert (await call("gdcae_candidate_propose", changed))["error"] == "REQUEST_KEY_CONFLICT"
            assert (await call("gdcae_evidence_read", {**pid, "candidate": 1}))["error"] == "EVIDENCE_NOT_AVAILABLE"
            assert (await call("gdcae_evidence_read", {**pid, "candidate": 2}))["error"] == "CANDIDATE_NOT_FOUND"

    asyncio.run(run())


def test_unconfigured_contract_accepts_an_inert_candidate_without_measurement(tmp_path):
    contract = {"schema": "agent-research-contract-v1", "baseline_sha256": "a" * 64,
                "backend": {"kind": "UNCONFIGURED", "id": "operator-selected-service"},
                "parameter": {"name": "duration", "min": "0.2", "max": "3.7", "unit": "s"},
                "goal": {"metric": "reaction", "selector": "observation-a", "direction": "positive",
                         "unit": "N", "target": "20", "tolerance": "1"}}
    pid, connect = open_scope(tmp_path, contract)

    async def run():
        async with connect() as call:
            opened = (await call("gdcae_project_open", {}))["data"]
            started = (await call("gdcae_workflow_start", event(pid["project_id"], opened, "start")))["data"]
            assert started["model_qualification"] == "DECLARED_IDENTITY_ONLY"
            request = dict(event(pid["project_id"], started, "agent-input"),
                           proposal=proposal(contract, {"value": "1.8", "reason": "Inert proposed duration"}, []))
            proposed = (await call("gdcae_candidate_propose", request))["data"]
            assert proposed["state"] == "BACKEND_UNAVAILABLE"
            assert proposed["next_action"] == "STOP" and proposed["runs_used"] == 0
            assert proposed["real_solver_executed"] is False
            assert "decision" not in proposed["candidates"][0]
            assert (await call("gdcae_evidence_read", {**pid, "candidate": 1}))["error"] == "EVIDENCE_NOT_AVAILABLE"
            later = event(pid["project_id"], proposed, "next")
            assert (await call("gdcae_workflow_advance", later))["error"] == "ILLEGAL_STEP"
            assert (await call("gdcae_workflow_status", pid))["data"] == proposed

    asyncio.run(run())
