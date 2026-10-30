"""One explicit installed-snapshot Fake rehearsal; no Standard/real authorization.

This script is test support, not an Agent execution tool. Raw evidence stays in
the isolated ResearchProject; stdout is a fixed public projection only.
"""

import argparse
from decimal import Decimal
import importlib
import json
import os
from pathlib import Path
import sys
import time


def need(condition):
    if not condition:
        raise ValueError("REHEARSAL_BOUNDARY")


def synthetic_dat(load="1"):
    force = Decimal(load)
    return (
        "Abaqus 2024 Date 30-Oct-2026 Time 12:00:00\n"
        "R010 axial bar a19d17ea - N mm MPa STEP 1 INCREMENT 1\n"
        "S T E P 1 S T A T I C A N A L Y S I S\nINCREMENT 1 SUMMARY\n"
        "TIME INCREMENT COMPLETED 1 , FRACTION OF STEP COMPLETED 1\n"
        "STEP TIME COMPLETED 1 , TOTAL TIME COMPLETED 1\n"
        "THE FOLLOWING TABLE IS PRINTED AT THE INTEGRATION POINTS FOR ELEMENT TYPE T3D2 AND ELEMENT SET\n"
        f"BAR\nELEMENT PT FOOT- S11\nNOTE\n1 1 {force}\n\n"
        "THE FOLLOWING TABLE IS PRINTED FOR ALL NODES\nNODE FOOT- U1 U2 U3\nNOTE\n"
        f"1 0 0 0\n2 {force / 100} 0 0\n\n"
        "THE FOLLOWING TABLE IS PRINTED FOR ALL NODES\nNODE FOOT- RF1 RF2 RF3\nNOTE\n"
        f"1 {-force} 0 0\n2 0 0 0\n\n"
        "THE ANALYSIS HAS BEEN COMPLETED\nANALYSIS COMPLETE\nJOB TIME SUMMARY\n"
        "USER TIME (SEC) = 1\nSYSTEM TIME (SEC) = 0\nTOTAL CPU TIME (SEC) = 1\n"
        "WALLCLOCK TIME (SEC) = 1\n"
    ).encode("ascii")


def configure(task_root, site_packages, af_fixtures):
    for path in (task_root, site_packages, af_fixtures):
        need(path.is_absolute() and path.is_dir())
        need(not any(p.is_symlink() or p.is_junction() for p in (path, *path.parents)))
    need(task_root.name.startswith("gdcae-m03f1p1-g2long-"))
    need(site_packages.is_relative_to(task_root) and af_fixtures.is_relative_to(task_root))
    need(site_packages.name == "site-packages" and not os.environ.get("PYTHONPATH"))
    sys.path[:0] = [str(site_packages), str(af_fixtures)]
    origins = {}
    for name in ("aegiscae", "abqjobpilot"):
        module = importlib.import_module(name)
        origin = Path(module.__file__).resolve()
        need(origin.is_relative_to(site_packages))
        origins[name] = str(origin)
    return origins


def run(workspace, origins, *, fake_only):
    need(fake_only is True and workspace.is_dir())
    need((workspace / "gdcae-research-init.json").is_file()
         and not (workspace / "rehearsal.safe.json").exists())
    from aegiscae.contracts.research_contracts import canonical_json, digest_bytes
    from aegiscae.research.rod_bridge import RodBridge
    from aegiscae.research.project import open_existing_for_explicit_write
    from aegiscae.research.rod_preview import RealPreviewAdapter
    from aegiscae.research.rod_preview_rules import BASELINE
    from abqjobpilot.product_rod import RodProduct
    from abqjobpilot.execution.rod_evidence import read_synthetic_dat, verify_synthetic_dat
    from abqjobpilot.execution.rod_review import request_approval
    from g2_fake_rehearsal import FakeRehearsal, stage_synthetic_dat

    bridge = RodBridge(RealPreviewAdapter(open_existing_for_explicit_write(workspace / "research")))
    initial = bridge.inspect()
    init_receipt = json.loads((workspace / "gdcae-research-init.json").read_text(encoding="utf-8"))
    need(initial["project_revision"] == 2 and not initial["attempts"]
         and initial["contract_digest"] == init_receipt["contract_sha256"])
    bridge.admit(bridge.proposal("A", "1", "candidate_A"),
                 bridge.inspect()["project_revision"], "admit_A")
    port = RodProduct.create(workspace / "inert rod A", "Inert rod A")
    at_time = int(time.time())
    bridge.prepare_a(port, revision=bridge.inspect()["project_revision"], key="plan_A",
                     request_key="prepare_A", at_time=at_time, expires_at=at_time + 600)
    reference = bridge.numeric_reference("A")
    port.disconnect()
    port = RodProduct(workspace / "inert rod A")
    need(port.inspect(reference["plan_id"], reference["plan_digest"],
                      at_time=at_time) == reference)
    request = request_approval(port, reference, goal_digest=bridge.inspect()["contract_digest"],
        model_digest=BASELINE, nonce="review_A", not_before=at_time,
        expires_at=at_time + 600, budget_remaining=2, at_time=at_time)
    need(request["real_execution_authorized"] is False)
    (workspace / "approval-request.internal.json").write_text(
        json.dumps(request, indent=2), encoding="utf-8")
    fixture = FakeRehearsal(workspace / "separate fake A", test_root=workspace,
                            enabled=True, phase="A")
    bridge.fake_intent("A", fixture.plan_ref(), bridge.inspect()["project_revision"], "intent_A")
    try:
        fixture.start()
        fixture.submit()
        evidence = fixture.complete()
    finally:
        cleanup = fixture.close()
    need(cleanup["all_owned_processes_exited"] is True)
    evidence.update(cleanup)
    data = synthetic_dat()
    output_digest = stage_synthetic_dat(port, reference, data, evidence_key="numeric_A",
                                        at_time=at_time, execution_link=evidence["binding"])
    envelope = read_synthetic_dat(port, reference["plan_id"], reference["plan_digest"],
        expected_output_digest=output_digest, evidence_key="numeric_A", at_time=at_time)
    af_verdict = verify_synthetic_dat(port, reference["plan_id"], reference["plan_digest"],
        expected_output_digest=output_digest, evidence_key="numeric_A", at_time=at_time)
    need(af_verdict["numerical"] == "PASS" and af_verdict["V2"] == "NOT_VERIFIED")
    bridge.observe("A", evidence, envelope, bridge.inspect()["project_revision"], "observe_A")
    proposal = bridge.propose_b("candidate_B")
    state = bridge.inspect()
    need("B" not in state["attempts"] and state["real_solver_calls"] == 0)
    result = {"schema": "g2-installed-rehearsal-v1", "status": "PASS",
        "classification": "FAKE_IPC_PLUS_SEPARATE_SYNTHETIC_DAT",
        "dependency_environment": "DEPENDENCY_ENVIRONMENT_REUSED",
        "imports": origins, "summary": bridge.public_summary(),
        "input_digest": reference["input_digest"], "plan_digest": reference["plan_digest"],
        "plan_ref_digest": digest_bytes(canonical_json(reference)),
        "contract_digest": state["contract_digest"],
        "approval_request_digest": request["request_digest"],
        "approval_status": "REQUEST_ONLY_NOT_AUTHORIZED",
        "real_A": "NOT_RUN", "real_B": "NOT_RUN", "real_Grant": "NOT_ISSUED",
        "synthetic_A_displacement_mm": af_verdict["metric"]["value"],
        "synthetic_B_proposal_load_N": proposal["load_n"],
        "B_real_plan": "NOT_PREPARED", "B_approval": "NOT_REQUESTED",
        "B_next_action": "NON_EXECUTABLE_PROPOSAL_REVIEW_ONLY",
        "all_owned_processes_exited": True,
        "owned_process_count": cleanup["owned_process_count"],
        "HIL_ENFORCEMENT": "NOT_VERIFIED", "DESKTOP_AT_GDCAE": "NOT_TESTED"}
    port.disconnect()
    (workspace / "rehearsal.safe.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def reopen(workspace, origins):
    from aegiscae.research.project import open_existing_readonly
    from aegiscae.research.rod_preview import RealPreviewAdapter
    from aegiscae.research.rod_bridge import RodBridge

    previous = json.loads((workspace / "rehearsal.safe.json").read_text(encoding="utf-8"))
    current = RodBridge(RealPreviewAdapter(open_existing_readonly(workspace / "research")))
    need(current.public_summary() == previous["summary"])
    return {"schema": "g2-installed-reopen-v1", "status": "PASS",
            "summary_matches": True, "imports": origins, "read_only": True}


def admit_native_proposal(workspace, proposal_file, origins):
    """Consume one bounded untrusted suggestion; Core supplies/checks the bindings."""
    from aegiscae.contracts.research_contracts import canonical_json, digest_bytes
    from aegiscae.research.project import open_existing_for_explicit_write
    from aegiscae.research.rod_preview import RealPreviewAdapter
    from aegiscae.research.rod_bridge import RodBridge

    need(proposal_file.is_file() and proposal_file.stat().st_size <= 2048)
    need(not proposal_file.is_symlink() and not proposal_file.is_junction())
    packet = json.loads(proposal_file.read_text(encoding="utf-8"))
    need(type(packet) is dict and set(packet) == {
        "schema", "source", "marker", "summary_digest", "load_n", "native_response_digest"})
    need(packet["schema"] == "g2-native-suggestion-v1"
         and packet["source"] == "CURRENT_MAIN_CUSTOM_INVERSE"
         and packet["marker"] == "G2_INSTALLED_A_INVERSE_01")
    bridge = RodBridge(RealPreviewAdapter(open_existing_for_explicit_write(workspace / "research")))
    need(packet["summary_digest"] == digest_bytes(canonical_json(bridge.public_summary())))
    proposal = bridge.proposal("B", packet["load_n"], "candidate_B_native")
    result = bridge.admit(proposal, bridge.inspect()["project_revision"], "admit_native_B")
    need(result["attempts"]["B"]["inert_plan"] is None
         and result["attempts"]["B"]["binding"] is None)
    receipt = {"schema": "g2-native-admission-receipt-v1", "status": "PASS",
               "source": "CURRENT_MAIN_CUSTOM_INVERSE",
               "suggestion_digest": digest_bytes(canonical_json(packet)),
               "proposal_digest": digest_bytes(canonical_json(proposal)),
               "load_n": proposal["load_n"], "imports": origins,
               "summary": bridge.public_summary(), "real_B_plan": "NOT_PREPARED",
               "real_B_grant": "NOT_ISSUED", "real_A": "NOT_RUN", "real_B": "NOT_RUN"}
    with (workspace / "native-admission.safe.json").open("x", encoding="utf-8") as output:
        json.dump(receipt, output, indent=2)
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-root", type=Path, required=True)
    parser.add_argument("--site-packages", type=Path, required=True)
    parser.add_argument("--af-fixtures", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--fake-only", action="store_true")
    parser.add_argument("--reopen-only", action="store_true")
    parser.add_argument("--native-proposal", type=Path)
    args = parser.parse_args()
    try:
        need(args.workspace.is_absolute() and args.workspace.is_relative_to(args.task_root))
        origins = configure(args.task_root, args.site_packages, args.af_fixtures)
        need(not (args.native_proposal and (args.fake_only or args.reopen_only)))
        if args.native_proposal:
            need(args.native_proposal.is_absolute()
                 and args.native_proposal.is_relative_to(args.task_root))
            result = admit_native_proposal(args.workspace, args.native_proposal, origins)
        elif args.reopen_only:
            result = reopen(args.workspace, origins)
        else:
            result = run(args.workspace, origins, fake_only=args.fake_only)
        print(json.dumps(result))
    except Exception as error:
        code = getattr(error, "code", "UNEXPECTED_REHEARSAL_FAILURE")
        if not isinstance(code, str) or not code.isascii() or not code.replace("_", "").isalnum():
            code = "UNEXPECTED_REHEARSAL_FAILURE"
        print(json.dumps({"status": "BLOCKED", "code": code,
                          "exception_type": type(error).__name__}))
        raise SystemExit(2)
