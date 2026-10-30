"""Explicit public inert-Plan integration; no Owner or Solver in these cases."""

import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from aegiscae.contracts.research_contracts import digest_bytes
from aegiscae.research.rod_bridge import RodBridge
from aegiscae.research.rod_preview import create_preview
from aegiscae.research.rod_preview_rules import BASELINE, RodPreviewContract


@pytest.fixture
def public(monkeypatch):
    source = os.environ.get("GDCAE_G2_AF_SOURCE")
    if not source:
        pytest.skip("G2 public AF source not explicitly selected; no live process requested")
    root = Path(source)
    assert root.is_absolute() and (root / "abqjobpilot/product_rod.py").is_file()
    before = set(sys.modules)
    monkeypatch.syspath_prepend(str(root))
    monkeypatch.syspath_prepend(str(root / "tests"))
    try:
        yield SimpleNamespace(
            root=root,
            product=importlib.import_module("abqjobpilot.product_rod"),
            evidence=importlib.import_module("abqjobpilot.execution.rod_evidence"),
            review=importlib.import_module("abqjobpilot.execution.rod_review"),
            fixtures=importlib.import_module("g2_fake_rehearsal"),
            error=importlib.import_module("abqjobpilot.execution.models").ExecutionError,
        )
    finally:
        for name in tuple(set(sys.modules) - before):
            module = sys.modules[name]
            filename = getattr(module, "__file__", None)
            if (name == "abqjobpilot" or name.startswith("abqjobpilot.") or
                    filename and Path(filename).is_relative_to(root)):
                del sys.modules[name]


@pytest.fixture
def prepared(public, tmp_path):
    bridge = RodBridge(create_preview(tmp_path / "research", "Public bridge", RodPreviewContract()))
    bridge.admit(bridge.proposal("A", "1", "candidate_A"),
                 bridge.inspect()["project_revision"], "admit_A")
    port = public.product.RodProduct.create(tmp_path / "inert A", "Inert A")
    bridge.prepare_a(port, revision=bridge.inspect()["project_revision"],
                     key="plan_A", request_key="prepare_A", at_time=100, expires_at=200)
    yield bridge, port, bridge.numeric_reference("A")
    port.disconnect()


def test_actual_registered_public_plan_matches_candidate_and_reopens(public, prepared):
    bridge, port, reference = prepared
    assert reference["source"] == "INERT_ROD_PLAN"
    assert reference["authorization_state"] == "NOT_AUTHORIZED"
    assert Path(reference["input_path"]).read_bytes() == bridge.preview.candidate_input("A")
    assert reference["input_digest"] == digest_bytes(bridge.preview.candidate_input("A"))
    port.disconnect()
    reopened = public.product.RodProduct(port.directory)
    try:
        assert reopened.inspect(reference["plan_id"], reference["plan_digest"], at_time=100) == reference
    finally:
        reopened.disconnect()
    assert bridge.public_summary()["real_solver_calls"] == 0


def test_independent_python_reopens_public_plan_and_readonly_core(public, prepared, tmp_path):
    _bridge, port, reference = prepared
    code = """
import json,sys
from abqjobpilot.product_rod import RodProduct
from aegiscae.research.project import open_existing_readonly
from aegiscae.research.rod_preview import RealPreviewAdapter
from aegiscae.research.rod_bridge import RodBridge
p=RodProduct(sys.argv[1])
r=p.inspect(sys.argv[3],sys.argv[4],at_time=100)
b=RodBridge(RealPreviewAdapter(open_existing_readonly(sys.argv[2])))
assert b.numeric_reference('A')==r
assert r['authorization_state']=='NOT_AUTHORIZED'
p.disconnect()
print(json.dumps({'public_plan_equal':True,'readonly_reopen':True,'real_calls':0}))
"""
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([str(Path(__file__).resolve().parents[2] / "src"),
                                        str(public.root)])
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    child = subprocess.run([sys.executable, "-B", "-c", code, str(port.directory),
        str(tmp_path / "research"), reference["plan_id"], reference["plan_digest"]],
        env=env, capture_output=True, timeout=30)
    assert child.returncode == 0 and not child.stderr
    assert json.loads(child.stdout) == {"public_plan_equal": True,
                                       "readonly_reopen": True, "real_calls": 0}


def test_exact_prepare_replay_and_changed_expiry_refused(prepared):
    from aegiscae.contracts.research_contracts import ContractError

    bridge, port, _reference = prepared
    current = bridge.inspect()
    replay = bridge.prepare_a(port, revision=3, key="plan_A", request_key="prepare_A",
                              at_time=100, expires_at=200)
    assert replay["replayed"] is True
    assert {key: value for key, value in replay.items() if key != "replayed"} == current
    with pytest.raises(ContractError):
        bridge.prepare_a(port, revision=3, key="plan_A", request_key="prepare_A",
                         at_time=100, expires_at=201)
    assert bridge.inspect() == current


@pytest.mark.parametrize("mutation", ["digest", "project", "expired"])
def test_public_inspection_rejects_wrong_binding(public, prepared, tmp_path, mutation):
    _bridge, port, reference = prepared
    other = None
    if mutation == "project":
        other = public.product.RodProduct.create(tmp_path / "other inert", "Other inert")
    try:
        with pytest.raises(public.error):
            (other or port).inspect(reference["plan_id"],
                "sha256:" + "0" * 64 if mutation == "digest" else reference["plan_digest"],
                at_time=201 if mutation == "expired" else 100)
    finally:
        if other:
            other.disconnect()


def test_public_dat_read_and_independent_core_parser(public, prepared):
    from g2_rehearsal import synthetic_dat
    from aegiscae.research.rod_preview_dat import verify_dat

    bridge, port, reference = prepared
    data = synthetic_dat()
    output = public.fixtures.stage_synthetic_dat(port, reference, data,
        evidence_key="fixture_A", at_time=100)
    envelope = public.evidence.read_synthetic_dat(port, reference["plan_id"],
        reference["plan_digest"], expected_output_digest=output, evidence_key="fixture_A", at_time=100)
    af = public.evidence.verify_synthetic_dat(port, reference["plan_id"], reference["plan_digest"],
        expected_output_digest=output, evidence_key="fixture_A", at_time=100)
    core = verify_dat(envelope["dat_bytes"], "1", bridge.inspect()["contract"])
    assert af["numerical"] == "PASS" and af["V2"] == "NOT_VERIFIED"
    assert core["displacement_mm"] == af["metric"]["value"]
    assert envelope["real_solver_executed"] is False


@pytest.mark.parametrize("mutation", ["bytes", "metadata", "digest"])
def test_dat_source_substitution_is_refused(public, prepared, mutation):
    from g2_rehearsal import synthetic_dat

    _bridge, port, reference = prepared
    output = public.fixtures.stage_synthetic_dat(port, reference, synthetic_dat(),
        evidence_key="fixture_A", at_time=100)
    directory = Path(reference["output_path"])
    if mutation == "bytes":
        (directory / "synthetic.dat").write_bytes(b"old or replaced output")
    elif mutation == "metadata":
        metadata = json.loads((directory / "synthetic-evidence.json").read_text())
        metadata["source"] = "AF_REAL"
        (directory / "synthetic-evidence.json").write_text(json.dumps(metadata))
    else:
        output = "sha256:" + "0" * 64
    with pytest.raises(public.error):
        public.evidence.read_synthetic_dat(port, reference["plan_id"], reference["plan_digest"],
            expected_output_digest=output, evidence_key="fixture_A", at_time=100)


@pytest.mark.parametrize("bad_field", [None, "goal_digest", "model_digest"])
def test_approval_request_binds_frozen_core_and_model(public, prepared, bad_field):
    bridge, port, reference = prepared
    arguments = {"goal_digest": bridge.inspect()["contract_digest"], "model_digest": BASELINE,
                 "nonce": "review_A", "not_before": 100, "expires_at": 200,
                 "budget_remaining": 2, "at_time": 100}
    if bad_field:
        arguments[bad_field] = "sha256:" + "0" * 64
        with pytest.raises(public.error):
            public.review.request_approval(port, reference, **arguments)
    else:
        result = public.review.request_approval(port, reference, **arguments)
        assert result["real_execution_authorized"] is False
        assert result["plan_ref"] == reference and result["human_consent"] == "NOT_OBTAINED"
