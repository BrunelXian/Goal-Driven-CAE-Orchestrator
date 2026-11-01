"""Actual AF public API, original synthetic records, no IPC/Owner/process/Solver."""

import copy
import importlib
import os
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

from aegiscae.contracts.research_contracts import ContractError, digest_bytes
from aegiscae.research.rod_bridge import RodBridge
from aegiscae.research.rod_preview import create_preview
from aegiscae.research.rod_preview_rules import RodPreviewContract
from aegiscae.research.rod_real_evidence import RealRodEvidence, bundle_digest


@pytest.fixture
def public_real(monkeypatch):
    source = os.environ.get("GDCAE_G2_AF_SOURCE")
    if not source:
        pytest.skip("Explicit AF Develop source not selected; no live acquisition")
    root = Path(source)
    assert root.is_absolute() and (root / "abqjobpilot/execution/rod_real_source.py").is_file()
    before = set(sys.modules)
    monkeypatch.syspath_prepend(str(root))
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "unit"))
    try:
        yield SimpleNamespace(
            product=importlib.import_module("abqjobpilot.product_rod"),
            lifecycle=importlib.import_module("abqjobpilot.execution.rod_lifecycle"),
            real=importlib.import_module("abqjobpilot.execution.rod_real_source"),
            errors=importlib.import_module("abqjobpilot.execution.models"),
            fixtures=importlib.import_module("test_d3_real_evidence"))
    finally:
        for name in tuple(set(sys.modules) - before):
            if name == "abqjobpilot" or name.startswith("abqjobpilot."):
                del sys.modules[name]


@pytest.fixture
def joined(public_real, tmp_path):
    preview = create_preview(tmp_path / "research", "D3 public offline", RodPreviewContract())
    bridge = RodBridge(preview)
    bridge.admit(bridge.proposal("A", "1", "candidate_A"), 2, "admit_A")
    product = public_real.product.RodProduct.create(tmp_path / "inert-af", "D3 inert only")
    try:
        bridge.prepare_a(product, revision=3, key="prepare_A", request_key="inert_plan_A",
                         at_time=100, expires_at=200)
        ref = bridge.numeric_reference("A")
        public_real.lifecycle.prepare_request(product, ref, request_key="prospective_A",
            not_before=100, expires_at=180, budget_reservation="fixture_reservation_only", at_time=100)
        qualified = public_real.real.qualify_real_plan(product, ref, "prospective_A", at_time=100)
        bundle = public_real.fixtures.fixture_bundle(preview)
        bundle["receipt"]["idempotency_key"] = qualified["request_key"]
        bundle["plan"] = qualified["plan"]
        plan = bundle["plan"]
        for record in (bundle["run"], bundle["receipt"]):
            record.update({key: plan[key] for key in
                           ("project_id", "project_instance_id", "plan_id", "plan_digest")})
        for record in (bundle["run"], bundle["artifact"]):
            record.update({key: plan[key] for key in ("input_digest", "output_identity")})
        bundle["bindings_digest"] = bundle_digest(bundle)
        yield preview, product, ref, qualified, bundle
    finally:
        product.disconnect()


def test_persisted_inert_plan_typed_records_and_independent_gd_verifier(public_real, joined):
    preview, product, ref, qualified, bundle = joined
    before = preview.inspect()
    assert qualified["execution_authorized"] is False and qualified["activation"] == "DISABLED"
    assert product.inspect(ref["plan_id"], ref["plan_digest"], at_time=100) == ref
    typed = public_real.real.validate_real_bundle(bundle, expected_plan=qualified["plan"])
    result = RealRodEvidence(preview).verify_declaration(bundle, expected_plan=qualified["plan"],
        expected_link=public_real.fixtures.fixture_link(bundle),
        expected_revision=before["project_revision"])
    assert public_real.real.bundle_digest(bundle) == bundle_digest(bundle) == typed.bindings_digest
    assert typed.source_authentication == result["source_authentication"] == "NOT_VERIFIED"
    assert typed.V2 == result["V2"] == "NOT_VERIFIED"
    assert result["numerical_fixture_checks"] == "PASS" and result["committed_inert_plan_link"]
    assert preview.inspect() == before


def test_af_schema_success_does_not_hide_bad_numerics(public_real, joined):
    preview, _product, _ref, qualified, bundle = joined
    artifact = bundle["artifact"]
    artifact["dat_bytes"] = artifact["dat_bytes"].replace(b"2 0.01 0 0", b"2 0.02 0 0")
    artifact["sha256"] = digest_bytes(artifact["dat_bytes"])
    artifact["size"] = len(artifact["dat_bytes"])
    bundle["bindings_digest"] = bundle_digest(bundle)
    assert public_real.real.validate_real_bundle(bundle,
        expected_plan=qualified["plan"]).source_authentication == "NOT_VERIFIED"
    with pytest.raises(ContractError, match="DAT_NUMERICAL_MISMATCH"):
        RealRodEvidence(preview).verify_declaration(bundle, expected_plan=qualified["plan"],
            expected_link=public_real.fixtures.fixture_link(bundle),
            expected_revision=preview.inspect()["project_revision"])


def test_no_authenticated_acquisition_or_b_plan_from_schema_fixture(public_real, joined):
    preview, _product, _ref, qualified, _bundle = joined
    with pytest.raises(public_real.errors.ExecutionError):
        public_real.real.acquire_authenticated_real_dat(plan=qualified["plan"], request_id="fixture_request")
    with pytest.raises(ContractError, match="A_NOT_OBSERVED"):
        RealRodEvidence(preview).require_real_b_admission(expected_revision=preview.inspect()["project_revision"])


def test_wrong_persisted_plan_rejected_even_with_consistent_schema(public_real, joined):
    preview, _product, _ref, qualified, bundle = joined
    substituted = copy.deepcopy(bundle)
    substituted["plan"]["resources_digest"] = digest_bytes(b"changed-resources")
    substituted["bindings_digest"] = bundle_digest(substituted)
    public_real.real.validate_real_bundle(substituted, expected_plan=substituted["plan"])
    with pytest.raises(ContractError, match="REAL_COMMITTED_PLAN_MISMATCH"):
        RealRodEvidence(preview).verify_declaration(substituted, expected_plan=substituted["plan"],
            expected_link=public_real.fixtures.fixture_link(bundle),
            expected_revision=preview.inspect()["project_revision"])
    assert qualified["plan"] != substituted["plan"]
