"""Pure offline schema fixtures. No real AF, processes, authentication or Solver."""

import copy
from concurrent.futures import ThreadPoolExecutor

import pytest

from aegiscae.contracts.research_contracts import ContractError, digest_bytes
from aegiscae.research.rod_evidence import SELECTOR, UNITS, af_digest, tolerances
from aegiscae.research.rod_preview import create_preview
from aegiscae.research.rod_preview_rules import RodPreviewContract
from aegiscae.research.rod_real_evidence import RealRodEvidence, bundle_digest
from test_real_rod_preview import advance_intent, observe, proposal, synthetic_dat


def fixture_bundle(preview):
    """New original in-memory fixture; no historical runs or source data."""
    state = preview.inspect()
    candidate = state["attempts"]["A"]["candidate"]
    contract = RodPreviewContract.from_dict(state["contract"])
    plan = {"schema": "af-rod-real-plan-projection-v1", "profile": contract.profile,
        "backend_id": "abaqus-standard-rod-preview-v1", "project_id": "d3_fixture_project",
        "project_instance_id": "d3_fixture_instance", "plan_id": "d3_fixture_plan",
        "plan_digest": digest_bytes(b"fixture-plan"), "candidate_id": candidate["candidate_id"],
        "input_digest": candidate["input_digest"], "input_size": len(preview.candidate_input("A")),
        "resources_digest": digest_bytes(b"fixture-resources"),
        "output_identity": digest_bytes(b"fixture-output"), "contract_digest": contract.digest(),
        "research_project_id": state["research_project_id"],
        "research_revision": state["project_revision"], "phase": "A", "load_n": "1",
        "verification_policy_digest": af_digest(tolerances(contract))}
    common = {key: plan[key] for key in ("project_id", "project_instance_id", "plan_id", "plan_digest")}
    receipt = {**common, "request_id": "d3_fixture_receipt", "idempotency_key": "d3_fixture_request",
        "run_id": "d3_fixture_run", "grant_id": "d3_fixture_grant_declaration",
        "request_status": "ACCEPTED", "accepted_sequence": 4}
    run = {**common, "run_id": receipt["run_id"], "grant_id": receipt["grant_id"],
        "phase_attempt_id": "d3_fixture_attempt", "backend_id": plan["backend_id"],
        "phase": "STANDARD", "attempt_no": 1, "retry_of": None, "simulation": False,
        "execution": "FINISHED", "reconciliation": "NONE", "backend_outcome": "COMPLETED",
        "solver_exit_code": 0, "input_digest": plan["input_digest"],
        "output_identity": plan["output_identity"], "revision": 3,
        "managed_scope": "COMMITTED_EMPTY_SCOPE"}
    data = synthetic_dat()
    artifact = {"filename": "axial_rod.dat", "dat_bytes": data, "size": len(data),
        "sha256": digest_bytes(data), "run_id": run["run_id"],
        "phase_attempt_id": run["phase_attempt_id"], "input_digest": plan["input_digest"],
        "output_identity": plan["output_identity"], "selector": dict(SELECTOR),
        "units": dict(UNITS), "stable_read": True}
    bundle = {"schema": "af-rod-real-evidence-v1", "source": "OFFLINE_REAL_SCHEMA_FIXTURE",
        "plan": plan, "receipt": receipt, "run": run, "artifact": artifact,
        "events": [{"type": kind, "project_sequence": index + 3, "run_sequence": index,
                    "run_id": run["run_id"], "phase_attempt_id": run["phase_attempt_id"]}
                   for index, kind in enumerate(("REQUEST_ACCEPTED", "START_INTENT", "ROD_DAT_COMMITTED"), 1)]}
    bundle["bindings_digest"] = bundle_digest(bundle)
    return bundle


@pytest.fixture
def context(tmp_path):
    preview = create_preview(tmp_path / "original-d3-fixture", "D3 original fixture", RodPreviewContract())
    preview.admit(proposal(preview), 2, "admit_a")
    return preview, RealRodEvidence(preview)


def verify(context, bundle=None, expected=None):
    preview, checker = context
    bundle = fixture_bundle(preview) if bundle is None else bundle
    return checker.verify_declaration(bundle, expected_plan=bundle["plan"] if expected is None else expected,
                                      expected_link=fixture_link(bundle),
                                      expected_revision=preview.inspect()["project_revision"])


def fixture_link(bundle):
    return {**{key: bundle["receipt"][key] for key in
                ("request_id", "idempotency_key", "run_id", "grant_id")},
            "phase_attempt_id": bundle["run"]["phase_attempt_id"]}


@pytest.mark.parametrize("source", ["OFFLINE_REAL_SCHEMA_FIXTURE", "AF_REAL_DECLARATION"])
def test_declared_source_cannot_authenticate(context, source):
    preview, checker = context
    before = preview.inspect()
    bundle = fixture_bundle(preview)
    bundle["source"] = source
    bundle["bindings_digest"] = bundle_digest(bundle)
    result = verify(context, bundle)
    assert result["schema_checks"] == result["numerical_fixture_checks"] == "PASS"
    assert result["metrics"]["displacement_mm"] == "0.01"
    assert result["metrics"]["stress_mpa"] == "1"
    assert result["metrics"]["reaction_n"] == "-1"
    assert result["V2"] == "NOT_VERIFIED" and result["V3"] == "INCONCLUSIVE"
    assert not result["execution_authorized"] and not result["persisted"]
    assert result["V4"] == "NOT_ASSESSED" and result["ODB"] == "NOT_VERIFIED"
    assert result["real_source_acquisition"] == "NOT_RUN"
    assert result["real_contract_compatible"] is False
    assert preview.inspect() == before
    assert checker.verify_declaration(bundle, expected_plan=bundle["plan"],
        expected_link=fixture_link(bundle),
        expected_revision=before["project_revision"]) == result


@pytest.mark.parametrize("section,field,value", [
    ("plan", "backend_id", "fake-v1"), ("plan", "input_size", True),
    ("plan", "input_digest", digest_bytes(b"wrong-material")),
    ("plan", "load_n", "NaN"), ("plan", "candidate_id", "other_candidate"),
    ("plan", "contract_digest", digest_bytes(b"other-contract")),
    ("plan", "research_revision", True), ("plan", "phase", "B"),
    ("plan", "verification_policy_digest", digest_bytes(b"other-policy")),
    ("receipt", "grant_id", "wrong_grant"), ("receipt", "run_id", "wrong_run"),
    ("receipt", "accepted_sequence", 5), ("receipt", "request_status", "UNKNOWN"),
    ("run", "simulation", True), ("run", "solver_exit_code", True),
    ("run", "execution", "UNKNOWN"), ("run", "execution", "PAUSED"),
    ("run", "reconciliation", "UNKNOWN"), ("run", "retry_of", "old_run"),
    ("run", "managed_scope", "UNKNOWN"),
    ("run", "revision", 2), ("run", "input_digest", digest_bytes(b"old-input")),
    ("artifact", "run_id", "old_run"), ("artifact", "phase_attempt_id", "old_attempt"),
    ("artifact", "filename", "../old.dat"), ("artifact", "stable_read", False),
    ("artifact", "size", True), ("artifact", "output_identity", digest_bytes(b"old-output")),
    ("artifact", "selector", {**SELECTOR, "step": True}),
    ("artifact", "selector", {**SELECTOR, "increment": 2}),
    ("artifact", "units", {**UNITS, "displacement": "m"}),
])
def test_real_record_negatives_even_with_recomputed_checksum(context, section, field, value):
    bundle = fixture_bundle(context[0])
    bundle[section][field] = value
    bundle["bindings_digest"] = bundle_digest(bundle)
    with pytest.raises(ContractError):
        verify(context, bundle)


@pytest.mark.parametrize("before,after", [
    (b"2 0.01 0 0", b"2 0.02 0 0"), (b"1 1 1", b"1 1 2"),
    (b"1 -1 0 0", b"1 1 0 0"), (b"2 0.01 0 0", b"2 NaN 0 0"),
    (b"STEP 1 INCREMENT 1", b"STEP 2 INCREMENT 1"),
    (b"NODE FOOT- U1 U2 U3", b"NODE FOOT- U1 U2 U3\nNODE FOOT- U1 U2 U3"),
])
def test_independent_numerical_oracle_rejects_resealed_bad_dat(context, before, after):
    bundle = fixture_bundle(context[0])
    artifact = bundle["artifact"]
    artifact["dat_bytes"] = artifact["dat_bytes"].replace(before, after)
    artifact["size"] = len(artifact["dat_bytes"])
    artifact["sha256"] = digest_bytes(artifact["dat_bytes"])
    bundle["bindings_digest"] = bundle_digest(bundle)
    with pytest.raises(ContractError):
        verify(context, bundle)


@pytest.mark.parametrize("mode", ["missing", "order", "duplicate", "wrong_attempt", "extra"])
def test_ordered_history_required(context, mode):
    bundle = fixture_bundle(context[0])
    if mode == "missing":
        bundle["events"].pop()
    elif mode == "order":
        bundle["events"].reverse()
    elif mode == "duplicate":
        bundle["events"][1] = copy.deepcopy(bundle["events"][0])
    elif mode == "wrong_attempt":
        bundle["events"][1]["phase_attempt_id"] = "old_attempt"
    else:
        bundle["events"].append(copy.deepcopy(bundle["events"][-1]))
    bundle["bindings_digest"] = bundle_digest(bundle)
    with pytest.raises(ContractError):
        verify(context, bundle)


def test_external_pin_change_and_payload_replacement(context):
    bundle = fixture_bundle(context[0])
    pin = copy.deepcopy(bundle["plan"])
    bundle["plan"]["plan_digest"] = digest_bytes(b"replaced-plan")
    with pytest.raises(ContractError, match="REAL_PLAN_PIN_MISMATCH"):
        verify(context, bundle, pin)
    bundle = fixture_bundle(context[0])
    bundle["artifact"]["dat_bytes"] += b"changed-after-read"
    with pytest.raises(ContractError, match="REAL_ARTIFACT_BYTES_MISMATCH"):
        verify(context, bundle)


def test_no_caller_authentication_or_pass_field(context):
    bundle = fixture_bundle(context[0])
    bundle["authenticated"] = True
    with pytest.raises(ContractError):
        verify(context, bundle)


def test_stale_revision_rejected(context):
    preview, checker = context
    bundle = fixture_bundle(preview)
    with pytest.raises(ContractError, match="REVISION_CONFLICT"):
        checker.verify_declaration(bundle, expected_plan=bundle["plan"],
                                   expected_link=fixture_link(bundle), expected_revision=2)


@pytest.mark.parametrize("field", ["request_id", "idempotency_key", "run_id", "grant_id", "phase_attempt_id"])
def test_independently_pinned_original_link_rejects_substitution(context, field):
    preview, checker = context
    bundle = fixture_bundle(preview)
    link = fixture_link(bundle)
    link[field] = "different_original_reference"
    with pytest.raises(ContractError, match="REAL_EXPECTED_LINK_MISMATCH"):
        checker.verify_declaration(bundle, expected_plan=bundle["plan"], expected_link=link,
            expected_revision=preview.inspect()["project_revision"])


def test_b_before_a_observation_rejected(context):
    preview, checker = context
    with pytest.raises(ContractError, match="A_NOT_OBSERVED"):
        checker.require_real_b_admission(expected_revision=preview.inspect()["project_revision"])


def test_concurrent_duplicate_verification_has_no_persistent_side_effect(context):
    preview, _checker = context
    before = preview.inspect()
    bundle = fixture_bundle(preview)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: verify(context, bundle), range(4)))
    assert results == [results[0]] * 4
    assert preview.inspect() == before
    assert before["budget"]["held_or_charged"] == 0


def test_current_g2_fake_a_cannot_unlock_real_b(tmp_path):
    from aegiscae.research.rod_bridge import RodBridge
    from test_g2_rod_core import intent, observe as observe_fake, prepare_a

    preview = create_preview(tmp_path / "fake-route", "D3 fake route", RodPreviewContract())
    bridge = RodBridge(preview)
    prepare_a(bridge)
    intent(bridge)
    observe_fake(bridge)
    before = preview.inspect()
    assert before["attempts"]["A"]["decision"]["V2"] == "NOT_VERIFIED"
    with pytest.raises(ContractError, match="AUTHENTICATED_REAL_A_AND_REAL_CONTRACT_REQUIRED"):
        RealRodEvidence(preview).require_real_b_admission(expected_revision=before["project_revision"])
    assert preview.inspect() == before


@pytest.mark.parametrize("mode", ["pending", "unknown", "observed", "spent"])
def test_pending_unknown_synthetic_a_and_two_call_budget_block_real_b(tmp_path, mode):
    preview = create_preview(tmp_path / "budget-fixture", "D3 budget fixture", RodPreviewContract())
    checker = RealRodEvidence(preview)
    advance_intent(preview)
    expected = "PENDING_OR_UNKNOWN"
    if mode == "unknown":
        preview.mark_unknown("A", preview.inspect()["project_revision"], "unknown_a")
    elif mode in ("observed", "spent"):
        observe(preview)
        expected = "AUTHENTICATED_REAL_A_AND_REAL_CONTRACT_REQUIRED"
        if mode == "spent":
            advance_intent(preview, "B", "2")
            observe(preview, "B")
            expected = "BUDGET_EXHAUSTED"
    before = preview.inspect()
    with pytest.raises(ContractError, match=expected):
        checker.require_real_b_admission(expected_revision=before["project_revision"])
    assert preview.inspect() == before
