"""Installed G3 public evidence rehearsal. Explicit Fake only; no real dispatch."""

import argparse
import copy
import json
from pathlib import Path
import re
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from g2_rehearsal import configure, need, synthetic_dat  # noqa: E402


def confined_existing(path, root, *, kind):
    """Resolve an existing test path before access; deny lexical and link escapes."""
    need(kind in ("file", "directory") and path.is_absolute() and root.is_absolute())
    need(".." not in path.parts and ".." not in root.parts)
    need(root.is_dir() and all(not (p.is_symlink() or p.is_junction())
                              for p in (root, *root.parents, path, *path.parents)))
    resolved_root, resolved = root.resolve(strict=True), path.resolve(strict=True)
    need(resolved.is_relative_to(resolved_root))
    need(resolved.is_file() if kind == "file" else resolved.is_dir())
    return resolved


def _write(path, value):
    with path.open("x", encoding="utf-8") as output:
        json.dump(value, output, indent=2)


def _bridge(workspace, *, writable=False):
    from aegiscae.research.project import (
        open_existing_for_explicit_write, open_existing_readonly,
    )
    from aegiscae.research.rod_preview import RealPreviewAdapter
    from aegiscae.research.rod_bridge import RodBridge

    research = confined_existing(workspace / "research", workspace, kind="directory")
    opener = open_existing_for_explicit_write if writable else open_existing_readonly
    return RodBridge(RealPreviewAdapter(opener(research)))


def _verification_projection(record):
    return {key: record[key] for key in (
        "source", "bindings_digest", "public_fake_plan_digest", "output_digest",
        "acquisition_checks", "real_provenance", "V0", "V1", "V2", "V3", "V4", "ODB",
        "metrics", "raw_solver_logs", "real_goal", "real_solver_calls", "execution_authorized",
        "human_approval", "public_record_persisted")}


def run(workspace, origins, *, fake_only):
    confined_existing(workspace / "gdcae-source-receipt.json", workspace, kind="file")
    need(fake_only is True and workspace.is_dir()
         and (workspace / "gdcae-source-receipt.json").is_file()
         and not (workspace / "g3-rehearsal.safe.json").exists())
    from aegiscae.contracts.research_contracts import canonical_json, digest_bytes
    from aegiscae.research.rod_public_evidence import PublicRodEvidence
    from abqjobpilot.product_rod import RodProduct
    from abqjobpilot.execution.models import ExecutionError
    from abqjobpilot.execution.rod_lifecycle import (
        prepare_request, inspect_request, qualify_request, predispatch,
    )
    from abqjobpilot.execution.rod_evidence_port import read_test_evidence
    from g2_fake_rehearsal import FakeRehearsal, stage_synthetic_dat

    bridge = _bridge(workspace, writable=True)
    need(bridge.inspect()["project_revision"] == 2 and not bridge.inspect()["attempts"])
    bridge.admit(bridge.proposal("A", "1", "candidate_A"), 2, "admit_A")
    port = RodProduct.create(workspace / "inert rod A", "G3 inert rod A")
    at_time = int(time.time())
    bridge.prepare_a(port, revision=3, key="plan_A", request_key="prepare_A",
                     at_time=at_time, expires_at=at_time + 600)
    reference = bridge.numeric_reference("A")
    fake = FakeRehearsal(workspace / "separate fake A", test_root=workspace,
                         enabled=True, phase="A")
    bridge.fake_intent("A", fake.plan_ref(), 4, "intent_A")
    prospective = prepare_request(port, reference, request_key="prospective_A",
        not_before=at_time, expires_at=at_time + 600, budget_reservation="intent_A", at_time=at_time)
    port.disconnect()
    port = RodProduct(workspace / "inert rod A")
    need(inspect_request(port, reference, "prospective_A", at_time=at_time) == prospective)
    readiness = qualify_request(port, reference, "prospective_A", at_time=at_time)
    submitted = {k: reference[k] for k in
                 ("project_id", "project_instance_id", "plan_id", "plan_digest")}
    submitted.update(request_key="prospective_A", request_digest=prospective["request_digest"],
                     acceptance_state="NOT_SUBMITTED")
    refused = False
    try:
        predispatch(port, reference, "prospective_A", submitted=submitted, at_time=at_time)
    except ExecutionError as error:
        refused = error.code == "PENDING_PROTECTED_OPERATOR"
    need(refused)
    reader = PublicRodEvidence(bridge.preview)
    identity = reader.frozen_identity()
    need(identity["shared_bundle_freeze_revision"] == 2)
    try:
        fake.start()
        fake.submit()
        raw = fake.complete()
        data = synthetic_dat()
        output_digest = stage_synthetic_dat(port, reference, data, evidence_key="numeric_A",
                                            at_time=at_time, execution_link=raw["binding"])
        args = dict(rod_plan_ref=reference, fake_plan_ref=fake.plan_ref(),
            run_id=raw["binding"]["run_id"], receipt_id=raw["binding"]["receipt_id"],
            phase_attempt_id=raw["binding"]["phase_attempt_id"], evidence_key="numeric_A",
            output_digest=output_digest, goal_revision=2, model_revision=2, at_time=at_time)
        client = fake.harness.client()
        bundle = read_test_evidence(port, client, **args)
        need(read_test_evidence(port, client, **args) == bundle)
    finally:
        cleanup = fake.close()
    need(cleanup["all_owned_processes_exited"] is True and cleanup["normal_exit"] is True)
    raw.update(cleanup)
    revision = bridge.inspect()["project_revision"]
    verified = reader.verify(bundle, expected_revision=revision, fake_evidence=raw,
                             expected_identity=identity)
    observed = bridge.observe_public(bundle, raw, revision, "observe_public_A")
    budget = copy.deepcopy(bridge.inspect()["budget"])
    replay = bridge.observe_public(bundle, raw, revision, "observe_public_A")
    need(replay["workflow"] == observed["workflow"] and bridge.inspect()["budget"] == budget)
    need("B" not in bridge.inspect()["attempts"])
    private = copy.deepcopy(bundle)
    private["synthetic_envelope"]["dat_bytes"] = data.hex()
    _write(workspace / "public-proof.private.json", {
        "schema": "g3-local-rehearsal-proof-v1", "bundle_dat_encoding": "HEX",
        "bundle": private, "raw_fake_evidence": raw, "summary": bridge.public_summary(),
        "prospective_request": prospective})
    result = {"schema": "g3-installed-rehearsal-v1", "status": "PASS_LOCAL",
        "classification": "DEMO_SYNTHETIC_ONLY", "imports": origins,
        "dependency_environment": "DEPENDENCY_ENVIRONMENT_REUSED",
        "public_verification": _verification_projection(verified), "summary": bridge.public_summary(),
        "summary_digest": digest_bytes(canonical_json(bridge.public_summary())),
        "readiness": readiness, "predispatch_refused": refused,
        "read_replay_equal": True, "observation_replay_budget_unchanged": True,
        "shared_bundle_freeze_revision": identity["shared_bundle_freeze_revision"],
        "goal_component_digest": identity["goal_component_digest"],
        "model_component_digest": identity["model_component_digest"],
        "contract_digest": identity["contract_digest"], "input_digest": reference["input_digest"],
        "plan_digest": reference["plan_digest"], "all_owned_processes_exited": True,
        "owned_process_count": cleanup["owned_process_count"],
        "real_A": "NOT_RUN", "real_B": "NOT_RUN", "real_Grant": "NOT_ISSUED",
        "real_B_plan": "NOT_PREPARED", "HIL_OS_ENFORCEMENT": "BLOCKED_HIL_DEPLOYMENT",
        "DESKTOP_PLUGIN_ACTIVATION": "NOT_TESTED"}
    _write(workspace / "g3-rehearsal.safe.json", result)
    port.disconnect()
    return result


def reopen(workspace, origins, *, native=False):
    from aegiscae.research.rod_public_evidence import PublicRodEvidence

    path = confined_existing(workspace / "public-proof.private.json", workspace, kind="file")
    need(path.stat().st_size < 1048576)
    proof = json.loads(path.read_text(encoding="utf-8"))
    need(proof["schema"] == "g3-local-rehearsal-proof-v1" and proof["bundle_dat_encoding"] == "HEX")
    bundle = proof["bundle"]
    bundle["synthetic_envelope"]["dat_bytes"] = bytes.fromhex(bundle["synthetic_envelope"]["dat_bytes"])
    bridge = _bridge(workspace)
    expected = proof["summary"]
    if native:
        receipt_path = confined_existing(workspace / "g3-native-admission.safe.json", workspace, kind="file")
        need(receipt_path.stat().st_size < 65536)
        expected = json.loads(receipt_path.read_text(encoding="utf-8"))["summary"]
        need(bridge.inspect()["attempts"]["B"]["inert_plan"] is None
             and bridge.inspect()["attempts"]["B"]["binding"] is None)
    need(bridge.public_summary() == expected)
    verified = PublicRodEvidence(bridge.preview).verify(bundle,
        expected_revision=bridge.inspect()["project_revision"], fake_evidence=proof["raw_fake_evidence"])
    return {"schema": "g3-installed-reopen-v1", "status": "PASS_LOCAL", "read_only": True,
        "imports": origins, "summary_matches": True,
        "scope": "B_ADMITTED_NO_PLAN" if native else "A_OBSERVED",
        "public_verification": _verification_projection(verified)}


def admit_native(workspace, packet_path, origins):
    from aegiscae.contracts.research_contracts import canonical_json, digest_bytes

    need(packet_path.is_file() and packet_path.stat().st_size <= 2048 and not packet_path.is_symlink())
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    need(type(packet) is dict and set(packet) == {"schema", "marker", "summary_digest", "load_n"})
    need(packet["schema"] == "g3-untrusted-native-scalar-v1"
         and packet["marker"] == "G3_INSTALLED_A_INVERSE_01")
    bridge = _bridge(workspace, writable=True)
    need(packet["summary_digest"] == digest_bytes(canonical_json(bridge.public_summary())))
    result = bridge.admit(bridge.proposal("B", packet["load_n"], "candidate_B_native"),
                          bridge.inspect()["project_revision"], "admit_native_B")
    need(result["attempts"]["B"]["inert_plan"] is None and result["attempts"]["B"]["binding"] is None)
    receipt = {"schema": "g3-native-admission-v1", "status": "PASS_OFFLINE", "imports": origins,
        "source": "CURRENT_MAIN_CUSTOM_INVERSE_UNTRUSTED_SCALAR", "summary": bridge.public_summary(),
        "real_B_plan": "NOT_PREPARED", "real_Grant": "NOT_ISSUED", "real_A": "NOT_RUN", "real_B": "NOT_RUN"}
    _write(workspace / "g3-native-admission.safe.json", receipt)
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for argument in ("task-root", "site-packages", "af-fixtures", "workspace"):
        parser.add_argument("--" + argument, required=True, type=Path)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--fake-only", action="store_true")
    action.add_argument("--reopen-only", action="store_true")
    action.add_argument("--reopen-native", action="store_true")
    action.add_argument("--native-proposal", type=Path)
    args = parser.parse_args()
    try:
        args.workspace = confined_existing(args.workspace, args.task_root, kind="directory")
        args.site_packages = confined_existing(args.site_packages, args.task_root, kind="directory")
        args.af_fixtures = confined_existing(args.af_fixtures, args.task_root, kind="directory")
        origins = configure(args.task_root, args.site_packages, args.af_fixtures)
        if args.native_proposal:
            args.native_proposal = confined_existing(args.native_proposal, args.task_root, kind="file")
            result = admit_native(args.workspace, args.native_proposal, origins)
        elif args.reopen_only:
            result = reopen(args.workspace, origins)
        elif args.reopen_native:
            result = reopen(args.workspace, origins, native=True)
        else:
            result = run(args.workspace, origins, fake_only=args.fake_only)
        print(json.dumps(result))
    except Exception as error:
        code = getattr(error, "code", "G3_REHEARSAL_FAILED")
        if not isinstance(code, str) or re.fullmatch(r"[A-Z][A-Z0-9_]{0,63}", code) is None:
            code = "G3_REHEARSAL_FAILED"
        print(json.dumps({"status": "BLOCKED", "code": code}))
        raise SystemExit(2)
