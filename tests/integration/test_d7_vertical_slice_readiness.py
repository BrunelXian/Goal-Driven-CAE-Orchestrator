"""D7 capability characterization, not real execution or source qualification.

Uses the existing AF test framework in new pytest temporary Projects. Its native
launcher and real issuer are denied. Synthetic DAT/STA/MSG and TEST_ONLY Grants
exercise record plumbing only; they must never qualify V2/V3 or authorize B.
No new Owner, IPC server, process controller or execution path is introduced.
"""

import copy
from decimal import Decimal
from types import SimpleNamespace

import pytest

from aegiscae.contracts.research_contracts import ContractError, digest_bytes
from aegiscae.research import rod_real_project as real
from aegiscae.research.project import ProjectError
from aegiscae.research.rod_real_verify import verify_owner_artifact_set
from test_d4_cross_repo_offline import joined as _joined_fixture
from test_d6_cross_repo_offline import PublicPreflight

joined = _joined_fixture


def complete_fixture(joined, monkeypatch):
    research, af, helper, binding, port = joined
    from abqjobpilot.execution.store import open_existing_read_only

    preflight = PublicPreflight(af, monkeypatch)
    # Match production's detached read-only projection. Reusing a mutable fixture
    # ExecutionService as the read projection would replace its execution backend.
    monkeypatch.setattr(preflight.product, "_reader", lambda: SimpleNamespace(
        context=af.context, store=open_existing_read_only(af.context)))
    application = research.hold_a_for_review(preflight, binding, 3, "d7_hold")
    assert application["budget"] == {"limit": 2, "held": 1, "charged": 0, "available": 1}
    research.record_intent_a(4, "d7_intent")
    run_id = helper.complete_fixture(af, monkeypatch)
    return research, af, helper, binding, port, run_id


def full_artifacts(af, binding):
    from abqjobpilot.execution.rod_trusted import acquire

    return acquire(af.service, af.context, plan_id=binding["plan_id"],
                   expected_plan_digest=binding["plan_digest"],
                   request_key=binding["request_key"], include_completion_artifacts=True)


def test_positive_records_are_not_positive_real_acceptance_or_settlement(joined, monkeypatch):
    research, af, _helper, binding, port, run_id = complete_fixture(joined, monkeypatch)
    records = full_artifacts(af, binding)
    check = verify_owner_artifact_set(records, research.inspect()["candidates"]["A"], binding)
    assert check["numerical_bytes_check"] == "PASS"
    assert Decimal(check["metrics"]["displacement_mm"]) == Decimal("0.01")
    state = research.observe_a(port, 5, "d7_observe")
    assert state["observations"]["A"]["independent"]["run_id"] == run_id
    assert state["reservations"]["A"]["state"] == "ACCEPTANCE_UNKNOWN"
    assert state["budget"] == {"limit": 2, "held": 1, "charged": 0, "available": 1}
    assert state["real_a"] == "NOT_READY"
    assert state["verification"]["V2"] == check["V2"] == "NOT_VERIFIED"
    assert state["verification"]["V3"] == check["V3"] == "INCONCLUSIVE"
    assert not state["execution_authorized"]
    # Reopen the committed journal; neither a new session nor replay settles it.
    reopened = real.RealRodProject(research.project).inspect()
    assert reopened == research.inspect()
    replay = research.observe_a(port, 5, "d7_observe")
    assert replay["replayed"] and replay["project_revision"] == 6


@pytest.mark.parametrize("extension", ["sta", "msg"])
def test_dat_read_already_rejects_damaged_completion_files(joined, monkeypatch, extension):
    research, af, helper, binding, port, _run_id = complete_fixture(joined, monkeypatch)
    # Deliberately damage this NEW synthetic fixture, never a real/historical run.
    (af.engineering / (af.plan["job_name"] + "." + extension)).write_bytes(b"BROKEN_FIXTURE")
    before = research.inspect()
    with pytest.raises(helper.ExecutionError):
        research.observe_a(port, 5, "d7_bad_completion")
    with pytest.raises(helper.ExecutionError):
        full_artifacts(af, binding)
    assert research.inspect() == before
    assert before["budget"]["held"] == 1 and before["budget"]["charged"] == 0
    assert before["verification"]["V2"] == "NOT_VERIFIED"
    # Existing AF acquisition already checks all three; GD's saved v1 observation
    # carries DAT only. Future independent acceptance should retain the full set.


@pytest.mark.parametrize("claim", ["TRUSTED_LOCAL_WORKSTATION", "VERIFIED", "REAL_ABAQUS"])
def test_route_c_or_real_label_cannot_self_authenticate_existing_envelope(joined, monkeypatch, claim):
    research, af, _helper, binding, _port, _run_id = complete_fixture(joined, monkeypatch)
    records = full_artifacts(af, binding)
    records["source_authentication"] = claim
    before = research.inspect()
    with pytest.raises(ContractError, match="OWNER_SOURCE_UNQUALIFIED"):
        verify_owner_artifact_set(records, before["candidates"]["A"], binding)
    assert research.inspect() == before


@pytest.mark.parametrize("proposal", [
    {"load_n": "2"},
    {"load_n": "2", "source_authentication": "VERIFIED", "V2": "PASS", "V3": "PASS"},
    {"load_n": "2", "risk_model": "TRUSTED_LOCAL_WORKSTATION", "human_approval": True},
])
def test_b_remains_unimplemented_despite_consistent_a_records(joined, monkeypatch, proposal):
    research, _af, _helper, _binding, port, _run_id = complete_fixture(joined, monkeypatch)
    research.observe_a(port, 5, "d7_observe")
    before = research.inspect()
    with pytest.raises(ContractError, match="AUTHENTICATED_REAL_A_REQUIRED"):
        research.propose_b(proposal, 6, "d7_proposal")
    assert research.inspect() == before
    assert list(before["candidates"]) == ["A"]


def test_frozen_validator_identity_requires_explicit_versioning(joined, monkeypatch):
    research, _af, _helper, _binding, _port = joined
    frozen = research.inspect()["contract_digest"]
    hashes = copy.deepcopy(real.implementation_hashes())
    hashes["V3"] = digest_bytes(b"SYNTHETIC_FUTURE_VALIDATOR_VERSION")
    with monkeypatch.context() as changed:
        changed.setattr(real, "implementation_hashes", lambda: hashes)
        with pytest.raises(ProjectError, match="INTEGRITY_ERROR"):
            research.inspect()
    assert research.inspect()["contract_digest"] == frozen


def test_af_b_and_ordinary_capability_fail_before_any_real_issuer(joined):
    _research, af, helper, _binding, _port = joined
    from abqjobpilot.execution import rod_trusted
    from abqjobpilot.execution.models import now

    with pytest.raises(helper.ExecutionError) as rejected:
        rod_trusted.prepare(af.service, af.engineering, af.candidate,
                            **af.arguments, phase="B")
    assert rejected.value.code == "REAL_A_EVIDENCE_REQUIRED"
    request = {
        "action": "authorize", "owner_id": af.store._session.owner_id,
        "operation_key": "d7_no_real_grant", "operator_token": af.token,
        "arguments": {"plan_id": af.plan["plan_id"], "plan_digest": af.plan["plan_digest"],
                      "expires_at": now() + 60, "subject": "TEST_ONLY", "source": "TEST_ONLY"},
    }
    with pytest.raises(helper.ExecutionError) as denied:
        af.service.product_control.invoke(af.service, request)
    assert denied.value.code == "HIL_DEPLOYMENT_UNQUALIFIED"
    with af.store.read() as conn:
        assert all(conn.execute("SELECT COUNT(*) FROM " + table).fetchone()[0] == 0
                   for table in ("runs", "grants", "receipts", "consumption"))
