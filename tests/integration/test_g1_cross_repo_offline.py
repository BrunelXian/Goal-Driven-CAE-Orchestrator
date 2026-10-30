"""Explicit AF source opt-in; public pure contracts only, no Store/server/solver.

All DAT bytes and authorization references are OFFLINE_AF_SUBSTITUTE fixtures.
Cross-parser agreement is not real output provenance or execution authorization.
"""

import copy
from decimal import Decimal
import importlib
import os
from pathlib import Path
import sys

import pytest

from aegiscae.contracts.research_contracts import ContractError, canonical_json, digest_bytes
from aegiscae.research.rod_preview import create_preview
from aegiscae.research.rod_preview_rules import RodPreviewContract, TEMPLATE, candidate_bytes


@pytest.fixture
def public(monkeypatch):
    configured = os.environ.get("GDCAE_G1_AF_SOURCE")
    if not configured:
        pytest.skip("Explicit offline AF source not selected")
    root = Path(configured)
    assert root.is_absolute() and (root / "abqjobpilot/execution/rod_profile.py").is_file()
    prior_modules = set(sys.modules)
    try:
        monkeypatch.syspath_prepend(str(root))
        profile = importlib.import_module("abqjobpilot.execution.rod_profile")
        dat = importlib.import_module("abqjobpilot.execution.rod_dat")
        # Fixture helpers generate new bytes only; no original DAT/history is read.
        monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "unit"))
        helpers = importlib.import_module("test_real_rod_preview")
        yield profile, dat, helpers
    finally:
        # These public AF imports are test-scoped, never a dependency of aegiscae.
        for name in tuple(set(sys.modules) - prior_modules):
            if name == "abqjobpilot" or name.startswith("abqjobpilot."):
                del sys.modules[name]


@pytest.mark.parametrize("load", ["0.5", "1", "1.0", "1.2500", "2.00", "2.5"])
def test_compilers_produce_identical_exact_input(public, load):
    profile, _dat, _helpers = public
    candidate = profile.compile_candidate(TEMPLATE, load)
    assert candidate.input_bytes == candidate_bytes(load, RodPreviewContract())
    assert candidate.to_dict()["input_digest"] == digest_bytes(candidate.input_bytes)


def stage(adapter, profile, helpers, root, step, load):
    raw = helpers.proposal(adapter, step, load)
    adapter.admit(raw, adapter.inspect()["project_revision"], "admit_" + step)
    candidate = profile.compile_candidate(TEMPLATE, load)
    workspace = profile.materialize_candidate(root, candidate)
    view = adapter.inspect()
    plan = profile.prepare_preview(candidate, test_root=root, workspace=workspace,
        project_id="af_project_" + step, project_instance_id="af_instance_" + step,
        research_project_id=view["research_project_id"],
        contract_digest=view["contract_digest"], expires_at=200, at_time=100)
    plan_body = plan.to_dict()
    assert plan_body["execution_authorized"] is False
    assert plan_body["dispatch_state"] == "LIVE_DISPATCH_UNREGISTERED"
    binding = helpers.binding(adapter, step)
    binding["plan_digest"] = plan_body["plan_digest"]
    binding["resources_digest"] = digest_bytes(canonical_json(plan_body["resources"]))
    binding["output_identity"] = "out_" + digest_bytes(
        canonical_json({"output_path": plan_body["output_path"]}))[7:67]
    adapter.record_intent(step, binding, view["project_revision"], "intent_" + step)
    raw_dat = helpers.synthetic_dat(load)
    evidence = {"project_id": binding["project_id"],
        "project_instance_id": binding["project_instance_id"],
        "plan_digest": plan_body["plan_digest"], "input_digest": binding["input_digest"],
        "run_id": "run_" + step, "attempt_id": "attempt_" + step,
        "output_digest": digest_bytes(raw_dat), "solver_exit_code": 0,
        "managed_scope": "EMPTY_CONFIRMED", "source": "OFFLINE_AF_SUBSTITUTE"}
    return candidate, raw_dat, evidence, workspace


def test_two_project_mapping_and_independent_parsers_offline(public, tmp_path):
    profile, dat, helpers = public
    adapter = create_preview(tmp_path / "research", "Cross repo offline", RodPreviewContract())
    candidate, body, source, workspace_a = stage(adapter, profile, helpers, tmp_path, "A", "1")
    first = dat.parse_bound_dat(body, candidate, source, copy.deepcopy(source))
    assert first["source"] == "OFFLINE_AF_SUBSTITUTE"
    a = adapter.observe("A", helpers.observation(adapter, "A", body),
                        adapter.inspect()["project_revision"], "observe_A")
    assert a["attempts"]["A"]["decision"]["V3"] == "NOT_SATISFIED"
    measured = Decimal(a["attempts"]["A"]["decision"]["displacement_mm"])
    target = (Decimal(a["contract"]["goal_min_mm"]) +
              Decimal(a["contract"]["goal_max_mm"])) / 2
    proposed = str(target / measured)
    candidate, body, source, workspace_b = stage(adapter, profile, helpers, tmp_path, "B", proposed)
    second = dat.parse_bound_dat(body, candidate, source, copy.deepcopy(source))
    assert second["source"] == "OFFLINE_AF_SUBSTITUTE"
    result = adapter.observe("B", helpers.observation(adapter, "B", body),
                             adapter.inspect()["project_revision"], "observe_B")
    assert workspace_a != workspace_b
    assert result["budget"]["available"] == 0
    assert result["attempts"]["B"]["decision"]["V3"] == "SATISFIED"
    assert result["real_goal"] == "INCONCLUSIVE"
    assert result["execution_authorized"] is False
    # Mapping and parsers are exercised; AF lifecycle/two real Projects are NOT proven.


@pytest.mark.parametrize("field,replacement", [
    ("source", "AF_REAL"), ("input_digest", "sha256:" + "0" * 64),
    ("run_id", "wrong_run"), ("project_id", "wrong_project"),
    ("managed_scope", "UNKNOWN"), ("solver_exit_code", True),
])
def test_public_dat_binding_rejects_relabeling_and_substitution(public, tmp_path,
                                                              field, replacement):
    from abqjobpilot.execution.models import ExecutionError

    profile, dat, helpers = public
    adapter = create_preview(tmp_path / "research", "Cross repo negative", RodPreviewContract())
    candidate, body, expected, _workspace = stage(adapter, profile, helpers, tmp_path, "A", "1")
    supplied = copy.deepcopy(expected)
    supplied[field] = replacement
    with pytest.raises(ExecutionError) as error:
        dat.parse_bound_dat(body, candidate, supplied, expected)
    assert error.value.code in {"DAT_SOURCE_MISMATCH", "DAT_EXECUTION_UNKNOWN"}


def test_live_dispatch_rejected_even_with_exact_preview(public, tmp_path):
    from abqjobpilot.execution.models import ExecutionError

    profile, _dat, helpers = public
    adapter = create_preview(tmp_path / "research", "No live dispatch", RodPreviewContract())
    candidate, _body, _source, workspace = stage(adapter, profile, helpers, tmp_path, "A", "1")
    view = adapter.inspect()
    plan = profile.prepare_preview(candidate, test_root=tmp_path, workspace=workspace,
        project_id="af_project_A", project_instance_id="af_instance_A",
        research_project_id=view["research_project_id"],
        contract_digest=view["contract_digest"], expires_at=200, at_time=100)
    profile.check_preview(plan, expected_digest=plan.to_dict()["plan_digest"],
                          project_id="af_project_A", project_instance_id="af_instance_A",
                          at_time=100)
    with pytest.raises(ExecutionError) as error:
        profile.require_live_dispatch(plan)
    assert getattr(error.value, "code", None) == "LIVE_DISPATCH_UNREGISTERED"


def test_matching_real_labels_do_not_authenticate_live_source(public, tmp_path):
    from abqjobpilot.execution.models import ExecutionError

    profile, dat, helpers = public
    adapter = create_preview(tmp_path / "research", "No label authority", RodPreviewContract())
    candidate, body, source, _workspace = stage(adapter, profile, helpers, tmp_path, "A", "1")
    source["source"] = "AF_REAL"
    with pytest.raises(ExecutionError) as error:
        dat.parse_bound_dat(body, candidate, source, copy.deepcopy(source))
    assert error.value.code == "LIVE_AF_SOURCE_UNQUALIFIED"


@pytest.mark.parametrize("field,value", [
    ("resources_digest", "sha256:" + "0" * 64),
    ("output_identity", "substituted_output"),
    ("plan_digest", "sha256:" + "0" * 64),
])
def test_observation_cannot_substitute_pinned_plan_resource_or_output(public, tmp_path, field, value):
    profile, _dat, helpers = public
    adapter = create_preview(tmp_path / "research", "Bound Plan projection", RodPreviewContract())
    _candidate, body, _source, _workspace = stage(adapter, profile, helpers, tmp_path, "A", "1")
    supplied = helpers.observation(adapter, "A", body)
    supplied["binding"][field] = value
    with pytest.raises(ContractError, match="EVIDENCE_BINDING_MISMATCH"):
        adapter.observe("A", supplied, adapter.inspect()["project_revision"], "substitution")
    assert adapter.inspect()["budget"]["held_or_charged"] == 1
    assert adapter.inspect()["pending_or_unknown"] is True
